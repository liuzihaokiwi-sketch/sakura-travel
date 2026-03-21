"""快速验证 .env 中所有 AI API Key 是否可用"""
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

def test_openai():
    key = os.getenv("OPENAI_API_KEY", "")
    base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    if not key or key.startswith("your_"):
        return "⏭️  未配置"
    try:
        r = httpx.get(f"{base}/models", headers={"Authorization": f"Bearer {key}"}, timeout=10)
        if r.status_code == 200:
            models = [m["id"] for m in r.json().get("data", [])[:5]]
            return f"✅ 可用 (前5个模型: {', '.join(models)})"
        return f"❌ HTTP {r.status_code}: {r.text[:100]}"
    except Exception as e:
        return f"❌ {e}"

def test_ai_base():
    key = os.getenv("OPENAI_API_KEY", "")
    base = os.getenv("AI_BASE_URL", "")
    if not base or base == os.getenv("OPENAI_BASE_URL", ""):
        return "⏭️  与 OPENAI_BASE_URL 相同，跳过"
    try:
        r = httpx.get(f"{base}/models", headers={"Authorization": f"Bearer {key}"}, timeout=10)
        if r.status_code == 200:
            return f"✅ 可用"
        return f"❌ HTTP {r.status_code}: {r.text[:100]}"
    except Exception as e:
        return f"❌ {e}"

def test_anthropic():
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if not key or key.startswith("your_"):
        return "⏭️  未配置"
    try:
        r = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={"model": "claude-sonnet-4-20250514", "max_tokens": 5, "messages": [{"role": "user", "content": "hi"}]},
            timeout=15,
        )
        if r.status_code == 200:
            return f"✅ 可用"
        elif r.status_code == 401:
            return f"❌ Key 无效 (401)"
        elif r.status_code == 429:
            return f"⚠️ Key 有效但限流 (429)"
        return f"❌ HTTP {r.status_code}: {r.text[:100]}"
    except Exception as e:
        return f"❌ {e}"

def test_deepl():
    key = os.getenv("DEEPL_API_KEY", "")
    if not key or key.startswith("your_"):
        return "⏭️  未配置"
    try:
        base = "https://api-free.deepl.com" if key.endswith(":fx") else "https://api.deepl.com"
        r = httpx.get(f"{base}/v2/usage", headers={"Authorization": f"DeepL-Auth-Key {key}"}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            used = data.get("character_count", 0)
            limit = data.get("character_limit", 0)
            return f"✅ 可用 (已用 {used:,}/{limit:,} 字符)"
        return f"❌ HTTP {r.status_code}"
    except Exception as e:
        return f"❌ {e}"

def test_serpapi():
    key = os.getenv("SERPAPI_KEY", "")
    if not key or key.startswith("your_"):
        return "⏭️  未配置"
    try:
        r = httpx.get(f"https://serpapi.com/account?api_key={key}", timeout=10)
        if r.status_code == 200:
            data = r.json()
            return f"✅ 可用 (剩余搜索: {data.get('total_searches_left', '?')})"
        return f"❌ HTTP {r.status_code}"
    except Exception as e:
        return f"❌ {e}"

def test_google_places():
    key = os.getenv("GOOGLE_PLACES_API_KEY", "")
    if not key or key.startswith("your_"):
        return "⏭️  未配置"
    try:
        r = httpx.get(
            "https://maps.googleapis.com/maps/api/place/details/json",
            params={"place_id": "ChIJD7fiBh9u5kcRYJSMaMOCCwQ", "fields": "name", "key": key},
            timeout=10,
        )
        data = r.json()
        if data.get("status") == "OK":
            return f"✅ 可用 (测试: {data['result']['name']})"
        return f"❌ {data.get('status')}: {data.get('error_message', '')[:80]}"
    except Exception as e:
        return f"❌ {e}"

print("\n🔑 AI API Key 验证\n")
print(f"  OPENAI_API_KEY:       {test_openai()}")
print(f"  AI_BASE_URL:          {test_ai_base()}")
print(f"  ANTHROPIC_API_KEY:    {test_anthropic()}")
print(f"  DEEPL_API_KEY:        {test_deepl()}")
print(f"  SERPAPI_KEY:           {test_serpapi()}")
print(f"  GOOGLE_PLACES_API_KEY: {test_google_places()}")

# 显示配置的模型
print(f"\n📦 配置的模型层级:")
print(f"  AI_MODEL_LIGHT:    {os.getenv('AI_MODEL_LIGHT', '未配置')}")
print(f"  AI_MODEL_STANDARD: {os.getenv('AI_MODEL_STANDARD', '未配置')}")
print(f"  AI_MODEL_STRONG:   {os.getenv('AI_MODEL_STRONG', '未配置')}")
print()
