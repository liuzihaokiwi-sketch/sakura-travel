"""等待生成完成后打印 plan_id 和前端访问链接。"""
import httpx, time

c = httpx.Client(base_url="http://localhost:8000", timeout=15)

# 新建 trip
r = c.post("/trips", json={"cities":[{"city_code":"tokyo","nights":5}],"party_type":"couple","party_size":2})
d = r.json()
tid = d["trip_request_id"]
print(f"[1] Created trip: {tid}")

# 触发生成
rg = c.post(f"/trips/{tid}/generate")
print(f"[2] Generate: {rg.status_code}")

# 最多等 3 分钟
for i in range(36):
    time.sleep(5)
    s = c.get(f"/trips/{tid}/status").json()
    status = s.get("status", "?")
    plan_id = s.get("plan_id", "-")
    print(f"  [{(i+1)*5:3d}s] status={status}  plan_id={plan_id}")
    if status in ("done", "failed", "error"):
        if plan_id and plan_id != "-":
            print(f"\n✅ 报告已生成！")
            print(f"   plan_id : {plan_id}")
            print(f"   API     : http://localhost:8000/trips/{tid}/plan")
            print(f"   前端    : http://localhost:3000/plan/{tid}")
        else:
            print(f"\n❌ 生成失败: status={status}")
        break
else:
    print("\n⚠️ 超时（3分钟），worker 可能未在运行")
