#!/usr/bin/env python3
"""
🛠️ 一键维护脚本 (Maintenance Toolkit)
=======================================

集成所有运维操作：启动/停止/重启/更新/推送/健康检查/日志查看

用法:
  python scripts/maintain.py start          # 启动全部服务
  python scripts/maintain.py stop           # 停止全部服务
  python scripts/maintain.py restart        # 重启全部服务
  python scripts/maintain.py status         # 查看服务状态
  python scripts/maintain.py update         # 拉取代码 + 安装依赖 + 重启
  python scripts/maintain.py deploy         # 完整部署: commit + push + update + restart
  python scripts/maintain.py health         # 健康检查 (API + DB + Redis + 前端)
  python scripts/maintain.py logs [service] # 查看日志
  python scripts/maintain.py backup         # 备份数据库
  python scripts/maintain.py sync           # 同步远端数据库到本地
  python scripts/maintain.py crawl-status   # 爬虫状态
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)

# ── 配置 ─────────────────────────────────────────────────────────────────────

DOCKER = r"C:\Program Files\Docker\Docker\resources\bin\docker.exe"
PYTHON = str(ROOT / ".venv" / "Scripts" / "python.exe")
NPM = "npm"
GIT = "git"

API_URL = "http://127.0.0.1:8000"
WEB_URL = "http://127.0.0.1:3000"


# ── 工具函数 ─────────────────────────────────────────────────────────────────

def run(cmd: str, capture: bool = False, check: bool = True, timeout: int = 120) -> str:
    """执行命令"""
    print(f"  ▸ {cmd}")
    result = subprocess.run(
        cmd, shell=True, capture_output=capture,
        text=True, encoding="utf-8", errors="replace", timeout=timeout,
        cwd=str(ROOT),
    )
    if check and result.returncode != 0 and capture:
        print(f"    ⚠️ 返回码 {result.returncode}: {(result.stderr or '')[:200]}")
    return (result.stdout or "").strip() if capture else ""


def run_quiet(cmd: str, timeout: int = 30) -> tuple[int, str]:
    """静默执行，返回 (returncode, stdout)"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True,
            text=True, encoding="utf-8", errors="replace", timeout=timeout,
            cwd=str(ROOT),
        )
        return result.returncode, (result.stdout or "").strip()
    except subprocess.TimeoutExpired:
        return -1, "timeout"
    except Exception as e:
        return -1, str(e)


def header(title: str):
    print(f"\n{'─'*50}")
    print(f"  {title}")
    print(f"{'─'*50}")


def ok(msg: str):
    print(f"  ✅ {msg}")


def fail(msg: str):
    print(f"  ❌ {msg}")


def warn(msg: str):
    print(f"  ⚠️  {msg}")


def info(msg: str):
    print(f"  ℹ️  {msg}")


# ── Docker 服务管理 ──────────────────────────────────────────────────────────

def docker_compose(*args: str) -> str:
    cmd = f'"{DOCKER}" compose {" ".join(args)}'
    return run(cmd, capture=True, check=False)


def cmd_start():
    """启动全部服务"""
    header("🚀 启动服务")

    # 1. Docker 基础设施
    info("启动 PostgreSQL + Redis...")
    docker_compose("up", "-d", "postgres", "redis")
    time.sleep(3)

    # 等待健康检查
    for i in range(15):
        code, out = run_quiet(f'"{DOCKER}" compose ps --format json')
        if code == 0 and "healthy" in out.lower():
            break
        time.sleep(2)

    ok("Docker 服务已启动")

    # 2. 后端 API
    info("启动 FastAPI 后端...")
    run(f'start "API" /MIN cmd /c "{PYTHON} -m uvicorn app.main:app --reload --port 8000 > logs\\api.log 2>&1"',
        check=False)
    ok("API 启动中 (http://localhost:8000)")

    # 3. 前端 Next.js
    info("启动 Next.js 前端...")
    run(f'start "WEB" /MIN cmd /c "cd web && {NPM} run dev > ..\\logs\\web.log 2>&1"',
        check=False)
    ok("前端启动中 (http://localhost:3000)")

    # 4. Worker
    info("启动后台 Worker...")
    run(f'start "WORKER" /MIN cmd /c "{PYTHON} -m app.workers > logs\\worker.log 2>&1"',
        check=False)
    ok("Worker 启动中")

    print()
    info("等待 8 秒后执行健康检查...")
    time.sleep(8)
    cmd_health()


def cmd_stop():
    """停止全部服务"""
    header("🛑 停止服务")

    # 停止 Python/Node 进程
    info("停止 API / Worker / 前端进程...")
    run('taskkill /FI "WINDOWTITLE eq API" /F >nul 2>&1', check=False)
    run('taskkill /FI "WINDOWTITLE eq WEB" /F >nul 2>&1', check=False)
    run('taskkill /FI "WINDOWTITLE eq WORKER" /F >nul 2>&1', check=False)
    # 也按进程名杀
    run('taskkill /IM "uvicorn.exe" /F >nul 2>&1', check=False)
    run('taskkill /IM "node.exe" /F >nul 2>&1', check=False)

    # 停止 Docker
    info("停止 Docker 容器...")
    docker_compose("stop")

    ok("所有服务已停止")


def cmd_restart():
    """重启全部服务"""
    header("🔄 重启服务")
    cmd_stop()
    time.sleep(2)
    cmd_start()


# ── 状态查看 ─────────────────────────────────────────────────────────────────

def cmd_status():
    """查看服务状态"""
    header("📊 服务状态")

    # Docker 容器
    info("Docker 容器:")
    out = docker_compose("ps", "--format", "table {{.Name}}\t{{.Status}}\t{{.Ports}}")
    if out:
        for line in out.split("\n"):
            print(f"    {line}")
    else:
        warn("Docker 未运行或无容器")

    # Python 进程
    print()
    info("Python 进程:")
    code, out = run_quiet('tasklist /FI "IMAGENAME eq python.exe" /FO CSV /NH')
    if code == 0 and out and "python" in out.lower():
        count = out.count("python")
        print(f"    {count} 个 Python 进程运行中")
    else:
        print(f"    无 Python 进程")

    # Node 进程
    info("Node 进程:")
    code, out = run_quiet('tasklist /FI "IMAGENAME eq node.exe" /FO CSV /NH')
    if code == 0 and out and "node" in out.lower():
        count = out.count("node")
        print(f"    {count} 个 Node 进程运行中")
    else:
        print(f"    无 Node 进程")

    # 爬虫状态
    crawl_status_file = ROOT / "data" / "crawl_status.json"
    if crawl_status_file.exists():
        print()
        info("爬虫状态:")
        try:
            data = json.loads(crawl_status_file.read_text(encoding="utf-8"))
            s = data.get("summary", {})
            print(f"    ✅{s.get('done',0)} ❌{s.get('failed',0)} 🔄{s.get('running',0)} ⏳{s.get('pending',0)} | 📦{s.get('total_items',0):,}条")
        except Exception:
            pass


# ── 健康检查 ─────────────────────────────────────────────────────────────────

def cmd_health():
    """全面健康检查"""
    header("🏥 健康检查")
    all_ok = True

    # 1. PostgreSQL
    code, out = run_quiet(f'"{DOCKER}" exec japan_ai_postgres pg_isready -U postgres')
    if code == 0:
        ok("PostgreSQL: 正常")
    else:
        fail("PostgreSQL: 不可用")
        all_ok = False

    # 2. Redis
    code, out = run_quiet(f'"{DOCKER}" exec japan_ai_redis redis-cli ping')
    if code == 0 and "PONG" in out:
        ok("Redis: 正常")
    else:
        fail("Redis: 不可用")
        all_ok = False

    # 3. API
    code, out = run_quiet(f'curl -s -o nul -w "%{{http_code}}" {API_URL}/health')
    if code == 0 and "200" in out:
        ok("API: 正常 (http://localhost:8000)")
        # 获取详细 health
        _, detail = run_quiet(f'curl -s {API_URL}/health')
        if detail:
            print(f"    {detail}")
    else:
        fail(f"API: 不可用 (HTTP {out})")
        all_ok = False

    # 4. 前端
    code, out = run_quiet(f'curl -s -o nul -w "%{{http_code}}" {WEB_URL}')
    if code == 0 and out.startswith("2"):
        ok("前端: 正常 (http://localhost:3000)")
    else:
        warn(f"前端: 不可用 (HTTP {out})")

    # 5. 磁盘
    code, out = run_quiet('wmic logicaldisk get freespace,caption /format:csv')
    if code == 0:
        for line in out.split("\n"):
            if "C:" in line:
                parts = [p for p in line.strip().split(",") if p]
                if len(parts) >= 2:
                    try:
                        free_gb = int(parts[-1]) / (1024**3)
                        if free_gb < 5:
                            warn(f"磁盘: C盘仅剩 {free_gb:.1f} GB")
                        else:
                            ok(f"磁盘: C盘剩余 {free_gb:.0f} GB")
                    except ValueError:
                        pass

    print()
    if all_ok:
        ok("🎉 所有核心服务正常！")
    else:
        fail("部分服务异常，请检查上方输出")


# ── 更新 ─────────────────────────────────────────────────────────────────────

def cmd_update():
    """拉取最新代码 + 安装依赖"""
    header("📥 更新系统")

    # 1. Git pull
    info("拉取最新代码...")
    run(f"{GIT} pull --rebase", check=False)

    # 2. Python 依赖
    info("更新 Python 依赖...")
    run(f'"{PYTHON}" -m pip install -e ".[dev]" -q', check=False)

    # 3. Node 依赖
    info("更新前端依赖...")
    run(f"cd web && {NPM} install --silent", check=False)

    # 4. 数据库迁移（如果有 alembic）
    alembic_ini = ROOT / "alembic.ini"
    if alembic_ini.exists():
        info("执行数据库迁移...")
        run(f'"{PYTHON}" -m alembic upgrade head', check=False)

    ok("更新完成")


def cmd_build():
    """构建前端生产版本"""
    header("🔨 构建前端")
    info("npm run build...")
    run(f"cd web && {NPM} run build")
    ok("前端构建完成")


# ── 部署 (一键全流程) ────────────────────────────────────────────────────────

def cmd_deploy():
    """一键部署: commit → push → update → build → restart"""
    header("🚀 一键部署")
    start_time = time.time()

    # 1. 智能提交
    info("Step 1/6: 提交代码变更...")
    code, out = run_quiet(f"{GIT} status --porcelain")
    if out.strip():
        run(f'"{PYTHON}" scripts/smart_commit.py --auto', check=False)
        ok(f"代码已提交")
    else:
        ok("无待提交的变更")

    # 2. 推送
    info("Step 2/6: 推送到远端...")
    run(f"{GIT} push", check=False)
    ok("代码已推送")

    # 3. 更新依赖
    info("Step 3/6: 更新依赖...")
    cmd_update()

    # 4. 构建前端
    info("Step 4/6: 构建前端...")
    cmd_build()

    # 5. 重启服务
    info("Step 5/6: 重启服务...")
    cmd_restart()

    # 6. 健康检查
    info("Step 6/6: 健康检查...")
    time.sleep(5)
    cmd_health()

    elapsed = time.time() - start_time
    print(f"\n{'='*50}")
    ok(f"🎉 部署完成！耗时 {elapsed:.0f}s")
    print(f"{'='*50}")


# ── 数据库备份 ────────────────────────────────────────────────────────────────

def cmd_backup():
    """备份 PostgreSQL 数据库"""
    header("💾 数据库备份")

    backup_dir = ROOT / "backups"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"japan_ai_{timestamp}.sql"

    info(f"导出到: {backup_file}")
    run(
        f'"{DOCKER}" exec japan_ai_postgres pg_dump -U postgres --no-owner --no-acl postgres > "{backup_file}"',
        check=False,
    )

    if backup_file.exists() and backup_file.stat().st_size > 100:
        size_mb = backup_file.stat().st_size / (1024 * 1024)
        ok(f"备份成功: {backup_file.name} ({size_mb:.1f} MB)")

        # 清理旧备份（保留最近 10 个）
        backups = sorted(backup_dir.glob("japan_ai_*.sql"), reverse=True)
        if len(backups) > 10:
            for old in backups[10:]:
                old.unlink()
                info(f"清理旧备份: {old.name}")
    else:
        fail("备份失败")


# ── 数据同步 ─────────────────────────────────────────────────────────────────

def cmd_sync():
    """同步远端数据库到本地"""
    header("🔄 数据同步 (Supabase → 本地)")
    run(f'"{PYTHON}" scripts/sync_remote_to_local.py')


# ── 爬虫状态 ─────────────────────────────────────────────────────────────────

def cmd_crawl_status():
    """查看爬虫状态"""
    run(f'"{PYTHON}" scripts/crawl_orchestrator.py --status')


# ── 日志查看 ─────────────────────────────────────────────────────────────────

def cmd_logs(service: str = "api"):
    """查看日志"""
    header(f"📜 日志: {service}")
    log_map = {
        "api": ROOT / "logs" / "api.log",
        "web": ROOT / "logs" / "web.log",
        "worker": ROOT / "logs" / "worker.log",
        "crawler": ROOT / "logs" / "crawler_orchestrator.log",
        "crawl": ROOT / "logs" / "crawl_p0_output.txt",
    }

    log_file = log_map.get(service)
    if log_file and log_file.exists():
        # 显示最后 50 行
        lines = log_file.read_text(encoding="utf-8", errors="replace").split("\n")
        for line in lines[-50:]:
            print(f"  {line}")
    elif service in ("postgres", "redis"):
        docker_compose("logs", "--tail=50", service)
    else:
        warn(f"未找到日志: {service}")
        info(f"可用的日志: {', '.join(log_map.keys())}, postgres, redis")


# ── 快速操作 ─────────────────────────────────────────────────────────────────

def cmd_quick_restart_api():
    """只重启 API（不动数据库和前端）"""
    header("🔄 快速重启 API")
    run('taskkill /FI "WINDOWTITLE eq API" /F >nul 2>&1', check=False)
    time.sleep(1)
    run(f'start "API" /MIN cmd /c "{PYTHON} -m uvicorn app.main:app --reload --port 8000 > logs\\api.log 2>&1"',
        check=False)
    ok("API 已重启")


def cmd_quick_restart_web():
    """只重启前端"""
    header("🔄 快速重启前端")
    run('taskkill /FI "WINDOWTITLE eq WEB" /F >nul 2>&1', check=False)
    time.sleep(1)
    run(f'start "WEB" /MIN cmd /c "cd web && {NPM} run dev > ..\\logs\\web.log 2>&1"',
        check=False)
    ok("前端已重启")


# ── 入口 ─────────────────────────────────────────────────────────────────────

COMMANDS = {
    "start":       ("🚀 启动全部服务",              cmd_start),
    "stop":        ("🛑 停止全部服务",              cmd_stop),
    "restart":     ("🔄 重启全部服务",              cmd_restart),
    "status":      ("📊 查看服务状态",              cmd_status),
    "health":      ("🏥 健康检查",                  cmd_health),
    "update":      ("📥 拉取代码+更新依赖",          cmd_update),
    "build":       ("🔨 构建前端生产版本",           cmd_build),
    "deploy":      ("🚀 一键部署(commit+push+build+restart)", cmd_deploy),
    "backup":      ("💾 备份数据库",                cmd_backup),
    "sync":        ("🔄 同步远端数据库到本地",       cmd_sync),
    "crawl-status": ("🕷️  爬虫状态",               cmd_crawl_status),
    "logs":        ("📜 查看日志 [api|web|worker|crawler|postgres|redis]", None),
    "restart-api": ("🔄 只重启API",                cmd_quick_restart_api),
    "restart-web": ("🔄 只重启前端",               cmd_quick_restart_web),
}


def main():
    parser = argparse.ArgumentParser(
        description="🛠️  Travel AI 维护脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("command", nargs="?", default="help", help="命令")
    parser.add_argument("extra", nargs="*", help="额外参数")
    args = parser.parse_args()

    cmd = args.command.lower()

    if cmd == "help" or cmd not in COMMANDS:
        print("\n🛠️  Travel AI 维护脚本")
        print(f"{'='*55}")
        for name, (desc, _) in COMMANDS.items():
            print(f"  {name:16s}  {desc}")
        print(f"\n  用法: python scripts/maintain.py <command>")
        print(f"{'='*55}\n")
        return

    if cmd == "logs":
        service = args.extra[0] if args.extra else "api"
        cmd_logs(service)
        return

    _, func = COMMANDS[cmd]
    if func:
        func()


if __name__ == "__main__":
    main()
