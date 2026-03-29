"""
AI 运维 Agent — 轻量级自动运维服务

功能:
  1. 定时检查服务健康（每5分钟）
  2. 异常时自动重启
  3. 重启失败时调 AI 分析日志并邮件通知
  4. 白名单操作，AI 不直接执行任意命令

用法:
  python deploy/ai-ops/agent.py          # 前台运行
  python deploy/ai-ops/agent.py --once   # 单次检查（cron 模式）
"""

import json
import logging
import os
import smtplib
import subprocess
import sys
import time
from datetime import datetime
from email.mime.text import MIMEText
from pathlib import Path

# ── 配置 ──────────────────────────────────────────────────────

PROJECT_DIR = "/opt/travel-ai"
COMPOSE_FILE = "docker-compose.yml"
CHECK_INTERVAL = 300  # 5 分钟
MAX_RESTART_ATTEMPTS = 3
AI_PASSIVE_DAILY_LIMIT = 20       # 被动巡检：每天最多调 AI 20 次
AI_SAME_ISSUE_COOLDOWN = 7200     # 被动巡检：同一问题 2 小时冷却

# 从环境变量读取
ANTHROPIC_BASE_URL = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_AUTH_TOKEN", "")
AI_MODEL = os.getenv("AI_OPS_MODEL", "claude-sonnet-4-20250514")

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
ALERT_EMAIL = os.getenv("ALERT_EMAIL", "")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("ai-ops")

# ── 状态追踪 ──────────────────────────────────────────────────

restart_counts: dict[str, int] = {}
ai_call_count_today: int = 0
ai_call_date: str = ""
ai_issue_tracker: dict[str, float] = {}  # service_name -> last AI call timestamp


# ── 工具函数 ──────────────────────────────────────────────────

def run(cmd: str, timeout: int = 30) -> tuple[int, str]:
    """执行 shell 命令，返回 (exit_code, output)"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=timeout, cwd=PROJECT_DIR
        )
        output = (result.stdout + result.stderr).strip()
        return result.returncode, output
    except subprocess.TimeoutExpired:
        return -1, "TIMEOUT"
    except Exception as e:
        return -1, str(e)


def send_email(subject: str, body: str):
    """发送告警邮件"""
    if not all([SMTP_HOST, SMTP_USER, SMTP_PASSWORD, ALERT_EMAIL]):
        log.warning("SMTP 未配置，跳过邮件")
        return
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = f"[travel-ai] {subject}"
        msg["From"] = SMTP_USER
        msg["To"] = ALERT_EMAIL
        with smtplib.SMTP_SSL(SMTP_HOST, 465, timeout=10) as s:
            s.login(SMTP_USER, SMTP_PASSWORD)
            s.send_message(msg)
        log.info(f"邮件已发送: {subject}")
    except Exception as e:
        log.error(f"邮件发送失败: {e}")


# ── 健康检查 ──────────────────────────────────────────────────

SERVICES = [
    {
        "name": "api",
        "check": "docker exec japan_ai_api python3 -c \"import urllib.request; print(urllib.request.urlopen('http://localhost:8000/health').read().decode())\"",
        "restart": f"docker compose -f {COMPOSE_FILE} restart api",
        "logs": "docker logs japan_ai_api --tail 50",
    },
    {
        "name": "worker",
        "check": "docker ps --filter name=japan_ai_worker --filter status=running -q",
        "restart": f"docker compose -f {COMPOSE_FILE} restart worker",
        "logs": "docker logs japan_ai_worker --tail 50",
    },
    {
        "name": "frontend",
        "check": "docker ps --filter name=travel-web --filter status=running -q",
        "restart": f"docker compose -f {COMPOSE_FILE} restart frontend",
        "logs": "docker logs travel-web --tail 50",
    },
    {
        "name": "nginx",
        "check": "docker ps --filter name=japan_ai_nginx --filter status=running -q",
        "restart": f"docker compose -f {COMPOSE_FILE} up -d nginx",
        "logs": "docker logs japan_ai_nginx --tail 50",
    },
]


def check_service(service: dict) -> bool:
    """检查单个服务是否健康"""
    code, output = run(service["check"], timeout=15)
    if code != 0 or not output.strip():
        return False
    # api 特殊检查：确认 status 不是 error
    if service["name"] == "api":
        try:
            health = json.loads(output)
            return health.get("status") in ("ok", "degraded")
        except json.JSONDecodeError:
            return False
    return True


def restart_service(service: dict) -> bool:
    """重启服务，返回是否成功"""
    log.info(f"重启 {service['name']}...")
    code, output = run(service["restart"], timeout=60)
    if code != 0:
        log.error(f"重启 {service['name']} 失败: {output}")
        return False
    time.sleep(10)
    return check_service(service)


def get_logs(service: dict) -> str:
    """获取服务日志"""
    _, output = run(service["logs"], timeout=10)
    return output


# ── AI 分析 ──────────────────────────────────────────────────

def should_call_ai(service_name: str) -> tuple[bool, str]:
    """熔断检查：是否应该调用 AI"""
    global ai_call_count_today, ai_call_date

    today = datetime.now().strftime("%Y-%m-%d")
    if ai_call_date != today:
        ai_call_count_today = 0
        ai_call_date = today

    # 每日上限（仅被动巡检）
    if ai_call_count_today >= AI_PASSIVE_DAILY_LIMIT:
        return False, f"今日 AI 调用已达上限 ({AI_DAILY_LIMIT} 次)"

    # 同一服务冷却
    last_call = ai_issue_tracker.get(service_name, 0)
    elapsed = time.time() - last_call
    if elapsed < AI_SAME_ISSUE_COOLDOWN:
        remaining = int((AI_SAME_ISSUE_COOLDOWN - elapsed) / 60)
        return False, f"{service_name} 的 AI 分析冷却中（还剩 {remaining} 分钟）"

    return True, ""


def call_ai(service_name: str, logs: str, error_context: str) -> str:
    """调用 AI 分析故障日志"""
    global ai_call_count_today

    if not ANTHROPIC_API_KEY:
        return "AI API key 未配置"

    # 熔断检查
    ok, reason = should_call_ai(service_name)
    if not ok:
        log.info(f"AI 熔断: {reason}")
        return reason

    ai_call_count_today += 1
    ai_issue_tracker[service_name] = time.time()
    log.info(f"调用 AI 分析 {service_name} (今日第 {ai_call_count_today} 次)")

    prompt = f"""你是一个运维 AI。以下是 travel-ai 项目中 {service_name} 服务的故障信息。

错误上下文:
{error_context}

最近日志:
{logs[-3000:]}

请简洁分析:
1. 根因是什么（一句话）
2. 建议的修复操作（从以下选项中选择）:
   - restart: 重启该服务
   - rebuild: 重新构建镜像并重启
   - check_config: 配置问题，需要人工检查 .env
   - check_disk: 磁盘满，需要清理
   - human: 需要人工介入
3. 如果选择 human，简要说明人工需要做什么

只输出 JSON:
{{"cause": "...", "action": "restart|rebuild|check_config|check_disk|human", "detail": "..."}}"""

    try:
        import urllib.request

        data = json.dumps({
            "model": AI_MODEL,
            "max_tokens": 500,
            "messages": [{"role": "user", "content": prompt}],
        }).encode()

        req = urllib.request.Request(
            f"{ANTHROPIC_BASE_URL}/v1/messages",
            data=data,
            headers={
                "Content-Type": "application/json",
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            return result["content"][0]["text"]
    except Exception as e:
        return f"AI 调用失败: {e}"


# ── 白名单操作执行 ────────────────────────────────────────────

ALLOWED_ACTIONS = {
    "restart": lambda svc: run(svc["restart"], timeout=60),
    "rebuild": lambda svc: run(
        f"docker compose -f {COMPOSE_FILE} build {svc['name']} && "
        f"docker compose -f {COMPOSE_FILE} up -d {svc['name']}",
        timeout=300
    ),
    "check_disk": lambda _: run("docker image prune -af --filter 'until=72h' && docker system prune -f", timeout=60),
}


def execute_ai_action(service: dict, ai_response: str):
    """解析 AI 建议并执行白名单内的操作"""
    try:
        # 尝试从 AI 回复中提取 JSON
        response_text = ai_response.strip()
        # 处理可能的 markdown 代码块
        if "```" in response_text:
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        advice = json.loads(response_text)
    except (json.JSONDecodeError, IndexError):
        log.warning(f"AI 回复解析失败，发邮件通知人工")
        send_email(
            f"{service['name']} 异常 - AI 分析结果",
            f"AI 回复:\n{ai_response}\n\n请人工检查。"
        )
        return

    action = advice.get("action", "human")
    cause = advice.get("cause", "未知")
    detail = advice.get("detail", "")

    log.info(f"AI 分析: cause={cause}, action={action}")

    if action in ALLOWED_ACTIONS:
        log.info(f"执行 AI 建议: {action}")
        code, output = ALLOWED_ACTIONS[action](service)
        success = "成功" if code == 0 else "失败"
        send_email(
            f"{service['name']} 自动修复{success}",
            f"原因: {cause}\n操作: {action}\n详情: {detail}\n\n执行结果:\n{output[-500:]}"
        )
    else:
        # human 或未知操作 → 只通知
        send_email(
            f"{service['name']} 需要人工处理",
            f"原因: {cause}\n建议: {detail}\n\nAI 无法自动修复，请人工检查。"
        )


# ── 主循环 ────────────────────────────────────────────────────

def check_all():
    """执行一次全量检查"""
    issues = []

    for service in SERVICES:
        if check_service(service):
            # 健康，重置计数
            restart_counts[service["name"]] = 0
            continue

        log.warning(f"{service['name']} 异常!")
        count = restart_counts.get(service["name"], 0) + 1
        restart_counts[service["name"]] = count

        if count <= MAX_RESTART_ATTEMPTS:
            # 尝试重启
            if restart_service(service):
                log.info(f"{service['name']} 重启成功 (第{count}次)")
                send_email(
                    f"{service['name']} 异常已自动重启",
                    f"第 {count} 次重启成功。"
                )
                restart_counts[service["name"]] = 0
            else:
                log.error(f"{service['name']} 重启失败 (第{count}次)")
                issues.append(service)
        else:
            # 超过重试次数，调 AI
            log.warning(f"{service['name']} 已重启 {MAX_RESTART_ATTEMPTS} 次仍失败，调用 AI 分析")
            logs = get_logs(service)
            error_context = f"服务 {service['name']} 连续 {count} 次重启失败"
            ai_result = call_ai(service["name"], logs, error_context)
            log.info(f"AI 分析结果: {ai_result[:200]}")
            execute_ai_action(service, ai_result)

    return len(issues) == 0


def main():
    log.info("AI 运维 Agent 启动")
    log.info(f"  项目目录: {PROJECT_DIR}")
    log.info(f"  检查间隔: {CHECK_INTERVAL}s")
    log.info(f"  AI 模型: {AI_MODEL}")
    log.info(f"  AI API: {'已配置' if ANTHROPIC_API_KEY else '未配置'}")
    log.info(f"  邮件通知: {'已配置' if SMTP_HOST else '未配置'}")

    if "--once" in sys.argv:
        check_all()
        return

    while True:
        try:
            check_all()
        except Exception as e:
            log.error(f"检查出错: {e}")
            send_email("Agent 自身异常", f"检查过程出错:\n{e}")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
