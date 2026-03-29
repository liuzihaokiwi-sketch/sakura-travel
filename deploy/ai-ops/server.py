"""
AI 运维 Agent — HTTP 对话接口

提供一个简单的 Web 界面，你可以和 AI 对话来管理服务器。

启动: python deploy/ai-ops/server.py
访问: http://localhost:9090 或 https://kiwitrip.cn:9090
"""

import json
import logging
import os
import subprocess
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread

# ── 配置 ──────────────────────────────────────────────────────

PROJECT_DIR = "/opt/travel-ai"
COMPOSE_FILE = "docker-compose.yml"
PORT = 9090

ANTHROPIC_BASE_URL = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_AUTH_TOKEN", "")
AI_MODEL = os.getenv("AI_OPS_MODEL", "claude-sonnet-4-20250514")
OPS_PASSWORD = os.getenv("OPS_PASSWORD", "admin123")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("ai-ops-server")

# ── 工具函数 ──────────────────────────────────────────────────

def run(cmd: str, timeout: int = 30) -> str:
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=timeout, cwd=PROJECT_DIR
        )
        return (result.stdout + result.stderr).strip()
    except subprocess.TimeoutExpired:
        return "命令超时"
    except Exception as e:
        return f"执行错误: {e}"

# ── 白名单工具（AI 可调用）────────────────────────────────────

TOOLS = [
    {
        "name": "check_health",
        "description": "检查所有服务健康状态",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_logs",
        "description": "获取某个服务的最近日志",
        "input_schema": {
            "type": "object",
            "properties": {
                "service": {
                    "type": "string",
                    "enum": ["api", "worker", "frontend", "nginx", "postgres", "redis"],
                    "description": "服务名",
                }
            },
            "required": ["service"],
        },
    },
    {
        "name": "restart_service",
        "description": "重启某个服务",
        "input_schema": {
            "type": "object",
            "properties": {
                "service": {
                    "type": "string",
                    "enum": ["api", "worker", "frontend", "nginx"],
                    "description": "服务名",
                }
            },
            "required": ["service"],
        },
    },
    {
        "name": "docker_ps",
        "description": "查看所有容器状态",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "run_command",
        "description": "执行受限命令（只允许查看类命令：docker logs, docker ps, cat, grep, df, free）",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "要执行的命令"}
            },
            "required": ["command"],
        },
    },
    {
        "name": "rebuild_service",
        "description": "重新构建并重启某个服务（耗时较长）",
        "input_schema": {
            "type": "object",
            "properties": {
                "service": {
                    "type": "string",
                    "enum": ["api", "worker", "frontend"],
                    "description": "服务名",
                }
            },
            "required": ["service"],
        },
    },
]

CONTAINER_MAP = {
    "api": "japan_ai_api",
    "worker": "japan_ai_worker",
    "frontend": "travel-web",
    "nginx": "japan_ai_nginx",
    "postgres": "japan_ai_postgres",
    "redis": "japan_ai_redis",
}

# 只读命令白名单前缀
SAFE_PREFIXES = ["docker logs", "docker ps", "docker inspect", "cat ", "grep ", "df ", "free ", "du ", "ls "]


def execute_tool(name: str, input_data: dict) -> str:
    if name == "check_health":
        return run(
            'docker exec japan_ai_api python3 -c "'
            "import urllib.request; print(urllib.request.urlopen("
            "'http://localhost:8000/health').read().decode())\"",
            timeout=15,
        )

    if name == "get_logs":
        svc = input_data.get("service", "api")
        container = CONTAINER_MAP.get(svc, svc)
        return run(f"docker logs {container} --tail 80", timeout=15)

    if name == "restart_service":
        svc = input_data.get("service", "api")
        return run(f"docker compose -f {COMPOSE_FILE} restart {svc}", timeout=60)

    if name == "docker_ps":
        return run("docker compose ps", timeout=10)

    if name == "run_command":
        cmd = input_data.get("command", "")
        # 安全检查
        if not any(cmd.strip().startswith(prefix) for prefix in SAFE_PREFIXES):
            return f"拒绝执行: 命令 '{cmd}' 不在安全白名单中。只允许: {', '.join(SAFE_PREFIXES)}"
        return run(cmd, timeout=15)

    if name == "rebuild_service":
        svc = input_data.get("service", "api")
        return run(
            f"docker compose -f {COMPOSE_FILE} build {svc} && "
            f"docker compose -f {COMPOSE_FILE} up -d {svc}",
            timeout=300,
        )

    return f"未知工具: {name}"


# ── AI 对话 ──────────────────────────────────────────────────

DEFAULT_MAX_TOOL_ROUNDS = 10  # 默认每次对话最多 10 轮工具调用

SYSTEM_PROMPT = """你是 travel-ai 项目的运维 AI 助手，运行在阿里云 ECS 上。

项目架构:
- api (FastAPI, python): 后端 API，容器 japan_ai_api
- worker (arq): 后台任务，容器 japan_ai_worker
- frontend (Next.js): 前端，容器 travel-web
- nginx: 反向代理，容器 japan_ai_nginx
- postgres: 数据库，容器 japan_ai_postgres
- redis: 缓存/队列，容器 japan_ai_redis

docker-compose.yml 在 /opt/travel-ai/，所有服务同一网络。

你的职责:
1. 检查服务状态，诊断问题
2. 查看日志分析错误原因
3. 执行安全操作（重启、重建）
4. 简洁回复，直接给出结论和操作

安全规则:
- 你只能使用提供的工具
- 不要猜测，先查日志再下结论
- 重大操作前说明原因
- 回复用中文"""

conversation_history: list[dict] = []


def parse_max_rounds(message: str) -> tuple[str, int]:
    """解析用户消息中的次数限制，如 '检查前端问题 工作20次'"""
    import re
    match = re.search(r'工作\s*(\d+)\s*次', message)
    if match:
        rounds = min(int(match.group(1)), 50)  # 上限 50
        clean_msg = re.sub(r'\s*工作\s*\d+\s*次\s*', '', message).strip()
        return clean_msg, rounds
    return message, DEFAULT_MAX_TOOL_ROUNDS


def chat_with_ai(user_message: str) -> str:
    """主动对话 — 不受被动巡检的熔断限制"""
    global conversation_history

    clean_message, max_rounds = parse_max_rounds(user_message)
    conversation_history.append({"role": "user", "content": clean_message})

    # 保留最近 20 轮对话
    if len(conversation_history) > 40:
        conversation_history = conversation_history[-40:]

    messages = conversation_history.copy()

    # 多轮 tool use 循环
    for _ in range(max_rounds):
        data = json.dumps({
            "model": AI_MODEL,
            "max_tokens": 2000,
            "system": SYSTEM_PROMPT,
            "tools": TOOLS,
            "messages": messages,
        }).encode()

        try:
            req = urllib.request.Request(
                f"{ANTHROPIC_BASE_URL}/v1/messages",
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                },
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode())
        except Exception as e:
            return f"AI 调用失败: {e}"

        # 处理响应
        stop_reason = result.get("stop_reason", "end_turn")
        content_blocks = result.get("content", [])

        if stop_reason == "tool_use":
            # AI 要调用工具
            messages.append({"role": "assistant", "content": content_blocks})

            tool_results = []
            for block in content_blocks:
                if block.get("type") == "tool_use":
                    tool_name = block["name"]
                    tool_input = block.get("input", {})
                    log.info(f"AI 调用工具: {tool_name}({json.dumps(tool_input, ensure_ascii=False)})")
                    tool_output = execute_tool(tool_name, tool_input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block["id"],
                        "content": tool_output[:5000],  # 截断过长输出
                    })

            messages.append({"role": "user", "content": tool_results})
            continue
        else:
            # 最终回复
            text_parts = [b["text"] for b in content_blocks if b.get("type") == "text"]
            reply = "\n".join(text_parts)
            conversation_history.append({"role": "assistant", "content": reply})
            return reply

    return "AI 工具调用超过上限，请重试"


# ── HTTP 服务 ────────────────────────────────────────────────

HTML_PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI 运维助手</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:-apple-system,system-ui,sans-serif; background:#1a1a2e; color:#e0e0e0; height:100vh; display:flex; flex-direction:column; }
.header { padding:16px 20px; background:#16213e; border-bottom:1px solid #0f3460; }
.header h1 { font-size:16px; color:#e94560; }
.header p { font-size:12px; color:#888; margin-top:4px; }
.chat { flex:1; overflow-y:auto; padding:20px; }
.msg { margin-bottom:16px; max-width:85%; }
.msg.user { margin-left:auto; }
.msg .bubble { padding:12px 16px; border-radius:12px; font-size:14px; line-height:1.6; white-space:pre-wrap; word-break:break-word; }
.msg.user .bubble { background:#0f3460; color:#e0e0e0; border-bottom-right-radius:4px; }
.msg.ai .bubble { background:#16213e; color:#e0e0e0; border-bottom-left-radius:4px; border:1px solid #0f3460; }
.msg .time { font-size:11px; color:#666; margin-top:4px; padding:0 4px; }
.msg.user .time { text-align:right; }
.input-area { padding:16px 20px; background:#16213e; border-top:1px solid #0f3460; display:flex; gap:12px; }
.input-area textarea { flex:1; background:#1a1a2e; border:1px solid #0f3460; border-radius:8px; padding:12px; color:#e0e0e0; font-size:14px; resize:none; outline:none; font-family:inherit; }
.input-area textarea:focus { border-color:#e94560; }
.input-area button { background:#e94560; color:white; border:none; border-radius:8px; padding:12px 24px; font-size:14px; cursor:pointer; font-weight:600; }
.input-area button:hover { background:#c73e54; }
.input-area button:disabled { opacity:0.5; cursor:not-allowed; }
.loading { display:inline-block; }
.loading span { display:inline-block; width:6px; height:6px; background:#e94560; border-radius:50%; margin:0 2px; animation:bounce 1s infinite; }
.loading span:nth-child(2) { animation-delay:0.15s; }
.loading span:nth-child(3) { animation-delay:0.3s; }
@keyframes bounce { 0%,80%,100%{transform:translateY(0)} 40%{transform:translateY(-8px)} }
.quick-btns { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:16px; }
.quick-btns button { background:#0f3460; color:#e0e0e0; border:1px solid #1a3a6e; border-radius:6px; padding:6px 12px; font-size:12px; cursor:pointer; }
.quick-btns button:hover { background:#1a3a6e; }
</style>
</head>
<body>
<div class="header">
  <h1>AI 运维助手</h1>
  <p>travel-ai · kiwitrip.cn</p>
</div>
<div class="chat" id="chat">
  <div class="quick-btns">
    <button onclick="send('检查所有服务状态')">检查服务</button>
    <button onclick="send('看一下后端日志')">后端日志</button>
    <button onclick="send('前端为什么报500')">前端诊断</button>
    <button onclick="send('worker为什么一直重启')">Worker诊断</button>
    <button onclick="send('磁盘和内存使用情况')">系统资源</button>
    <button onclick="send('重启所有服务')">重启全部</button>
  </div>
</div>
<div class="input-area">
  <textarea id="input" rows="2" placeholder="输入指令... (Enter 发送)" onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();send()}"></textarea>
  <button id="btn" onclick="send()">发送</button>
</div>
<script>
const chat = document.getElementById('chat');
const input = document.getElementById('input');
const btn = document.getElementById('btn');

function addMsg(role, text) {
  const div = document.createElement('div');
  div.className = 'msg ' + role;
  const time = new Date().toLocaleTimeString('zh-CN', {hour:'2-digit',minute:'2-digit'});
  div.innerHTML = '<div class="bubble">' + escHtml(text) + '</div><div class="time">' + time + '</div>';
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
  return div;
}

function escHtml(t) { return t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

async function send(text) {
  const msg = text || input.value.trim();
  if (!msg) return;
  input.value = '';
  addMsg('user', msg);
  btn.disabled = true;

  const loading = document.createElement('div');
  loading.className = 'msg ai';
  loading.innerHTML = '<div class="bubble"><div class="loading"><span></span><span></span><span></span></div></div>';
  chat.appendChild(loading);
  chat.scrollTop = chat.scrollHeight;

  try {
    const base=location.pathname.replace(/\/+$/,'');const res = await fetch(base+'/chat', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({message: msg})
    });
    const data = await res.json();
    loading.remove();
    addMsg('ai', data.reply || data.error || '无响应');
  } catch(e) {
    loading.remove();
    addMsg('ai', '请求失败: ' + e.message);
  }
  btn.disabled = false;
  input.focus();
}
</script>
</body>
</html>"""


active_sessions: set[str] = set()

import hashlib
def make_token(password: str) -> str:
    return hashlib.sha256(f"ops-{password}-salt".encode()).hexdigest()[:32]

LOGIN_PAGE = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI 运维 - 登录</title>
<style>
body{font-family:sans-serif;background:#1a1a2e;color:#e0e0e0;display:flex;align-items:center;justify-content:center;height:100vh;margin:0}
.box{background:#16213e;padding:40px;border-radius:16px;border:1px solid #0f3460;width:300px}
h2{margin:0 0 20px;color:#e94560;font-size:18px;text-align:center}
input{width:100%;padding:12px;background:#1a1a2e;border:1px solid #0f3460;border-radius:8px;color:#e0e0e0;font-size:14px;margin-bottom:16px;box-sizing:border-box}
button{width:100%;padding:12px;background:#e94560;color:white;border:none;border-radius:8px;font-size:14px;cursor:pointer;font-weight:600}
.err{color:#e94560;font-size:12px;text-align:center;margin-bottom:12px}
</style></head><body>
<div class="box"><h2>AI 运维助手</h2>
<div id="err" class="err"></div>
<input id="pw" type="password" placeholder="输入密码" onkeydown="if(event.key==='Enter')login()">
<button onclick="login()">登录</button>
</div>
<script>
async function login(){
  const pw=document.getElementById('pw').value;
  const base=location.pathname.replace(/\/+$/,'');const res=await fetch(base+'/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({password:pw})});
  const data=await res.json();
  if(data.ok){document.cookie='ops_token='+data.token+';path=/';location.reload()}
  else{document.getElementById('err').textContent='密码错误'}
}
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _get_token(self):
        cookies = self.headers.get("Cookie", "")
        for part in cookies.split(";"):
            part = part.strip()
            if part.startswith("ops_token="):
                return part.split("=", 1)[1]
        return None

    def _is_authed(self):
        token = self._get_token()
        return token and token in active_sessions

    def do_GET(self):
        if not self._is_authed():
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(LOGIN_PAGE.encode())
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML_PAGE.encode())

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))

        if self.path == "/login":
            password = body.get("password", "")
            if password == OPS_PASSWORD:
                token = make_token(password + str(time.time()))
                active_sessions.add(token)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True, "token": token}).encode())
            else:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False}).encode())
            return

        if self.path == "/chat":
            if not self._is_authed():
                self.send_response(401)
                self.end_headers()
                return

            message = body.get("message", "")
            log.info(f"用户: {message}")
            reply = chat_with_ai(message)
            log.info(f"AI: {reply[:100]}...")

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"reply": reply}, ensure_ascii=False).encode())
            return

        self.send_response(404)
        self.end_headers()


def main():
    # 同时启动后台健康检查
    import importlib.util
    spec = importlib.util.spec_from_file_location("agent", os.path.join(os.path.dirname(__file__), "agent.py"))
    agent_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(agent_mod)
    def background_checker():
        import time
        while True:
            try:
                agent_mod.check_all()
            except Exception as e:
                log.error(f"后台检查出错: {e}")
            time.sleep(agent_mod.CHECK_INTERVAL)

    checker_thread = Thread(target=background_checker, daemon=True)
    checker_thread.start()
    log.info(f"后台健康检查已启动 (间隔 {agent_mod.CHECK_INTERVAL}s)")

    server = HTTPServer(("0.0.0.0", PORT), Handler)
    log.info(f"AI 运维助手已启动: http://0.0.0.0:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
