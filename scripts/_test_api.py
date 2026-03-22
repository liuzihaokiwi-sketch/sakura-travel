"""Quick API connectivity test."""
import asyncio, httpx, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
load_dotenv()

async def test():
    url = os.getenv("OPENAI_BASE_URL", "") + "/chat/completions"
    key = os.getenv("OPENAI_API_KEY", "")
    model = os.getenv("AI_MODEL_STRONG", "gpt-4o")
    print(f"Testing: {url} with model={model}")
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(url, headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }, json={
            "model": model,
            "messages": [{"role": "user", "content": "Say OK"}],
            "max_tokens": 5,
        })
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            d = r.json()
            print(f"Response: {d['choices'][0]['message']['content']}")
            print("✅ API 连通正常")
        else:
            print(f"Error: {r.text[:200]}")

asyncio.run(test())
