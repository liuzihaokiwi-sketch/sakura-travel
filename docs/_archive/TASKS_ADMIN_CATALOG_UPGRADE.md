# 管理后台 Catalog 页面升级任务

> 给 Sonnet 执行。改完后本地验证 `from app.main import app` 不报错，然后 push + 部署到 ECS。
> ECS 部署命令：`ssh root@47.242.209.129 "cd /opt/travel-ai && git pull && docker compose up -d --build api frontend && sleep 10 && docker logs japan_ai_api --tail 5"`

## 涉及文件
- 后端：`app/api/ops/catalog.py`（API 序列化）
- 前端：`web/app/admin/catalog/page.tsx`（管理页面）
- 前端 API：`web/app/api/admin/catalog/entities/route.ts`（透传，不用改）

## 任务列表

### 1. 后端：_serialize_entity 增加缺失字段 [简单]
文件：`app/api/ops/catalog.py` 的 `_serialize_entity()` 函数

增加返回：
```python
base["trust_status"] = getattr(entity, "trust_status", "unverified")
base["data_source"] = "google" if entity.google_place_id else ("tabelog" if entity.tabelog_id else "ai")
base["google_rating_display"] = None  # 从子表取
```

对于 POI 和 Hotel，google_rating 已经从子表取了。对于 Restaurant，也要取：
```python
if restaurant:
    # ... existing fields ...
    base["google_rating"] = float(restaurant.tabelog_score) if restaurant.tabelog_score else None  # 用 tabelog_score 作为评分
```

### 2. 后端：list_entities 支持 trust_status 筛选 [简单]
文件：`app/api/ops/catalog.py` 的 `list_entities()` 函数

增加参数：
```python
trust_status: Optional[str] = Query(None, description="verified / unverified / ai_generated / suspicious / rejected"),
```

增加过滤：
```python
if trust_status:
    stmt = stmt.where(EntityBase.trust_status == trust_status)
```

### 3. 后端：增加批量审核 API [简单]
文件：`app/api/ops/catalog.py`

新增端点：
```python
class TrustUpdate(BaseModel):
    entity_ids: list[str]
    trust_status: str  # verified / suspicious / rejected
    trust_note: Optional[str] = None

@router.patch("/catalog/entities/batch-trust")
async def batch_update_trust(body: TrustUpdate, db: AsyncSession = Depends(get_db)) -> dict:
    """批量更新 trust_status"""
    uids = [uuid.UUID(eid) for eid in body.entity_ids]
    from sqlalchemy import update
    await db.execute(
        update(EntityBase)
        .where(EntityBase.entity_id.in_(uids))
        .values(
            trust_status=body.trust_status,
            trust_note=body.trust_note,
            verified_by="admin",
            verified_at=func.now(),
        )
    )
    await db.commit()
    return {"updated": len(uids), "trust_status": body.trust_status}
```

前端 API route 也要加（`web/app/api/admin/catalog/entities/route.ts`）：
```typescript
export async function PATCH(req: NextRequest) {
  try {
    const body = await req.json();
    const res = await fetch(`${BACKEND}/ops/catalog/entities/batch-trust`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
```

### 4. 前端：表格增加列 [中等]
文件：`web/app/admin/catalog/page.tsx`

现有列：名称/城市/区域 | 层级 | 综合评分 | Google ★

需要增加/修改：
- **数据来源**列：显示 `data_source` 字段，用不同颜色标签
  - `google` → 绿色标签 "Google"
  - `tabelog` → 蓝色标签 "Tabelog"
  - `ai` → 红色标签 "AI生成"
- **信任状态**列：显示 `trust_status`，用不同颜色
  - `verified` → 绿色 "已验证"
  - `unverified` → 灰色 "未验证"
  - `ai_generated` → 橙色 "AI生成"
  - `suspicious` → 红色 "存疑"
  - `rejected` → 黑色 "已拒绝"
- **Google 评分**列：显示真实 google_rating（从子表），格式 ★ 4.2
- 去掉现在的"综合评分"列（entity_scores 表大部分是空的，没意义）

### 5. 前端：增加 trust_status 筛选器 [简单]
文件：`web/app/admin/catalog/page.tsx`

在现有的"全部城市"、"全部层级"下拉框旁边，增加：
- **信任状态**下拉：全部 / 已验证 / 未验证 / AI生成 / 存疑 / 已拒绝

### 6. 前端：增加批量审核操作 [中等]
文件：`web/app/admin/catalog/page.tsx`

- 每行左侧增加勾选框（checkbox）
- 顶部增加批量操作按钮：
  - "✓ 批量验证" → 选中项 trust_status 改为 verified
  - "⚠ 标记存疑" → 选中项改为 suspicious
  - "✗ 批量拒绝" → 选中项改为 rejected
- 调用 PATCH `/api/admin/catalog/entities` 接口

### 7. 前端：展开行显示详情 [简单改进]
现有的展开行（点击 ▶）应该也显示：
- trust_status + verified_by + verified_at
- google_place_id（如果有，说明是真实数据）
- 坐标：lat/lng，如果有值显示为可点击链接（打开 Google Maps）

## 优先级
1 → 2 → 4 → 5 → 3 → 6 → 7

---

## 二、新增页面

### 8. 活动簇管理页 [中等]
**新建文件**：`web/app/admin/clusters/page.tsx`
**后端已有**：需要新建 `app/api/ops/clusters.py`

**后端 API**：
```python
# app/api/ops/clusters.py
router = APIRouter()

@router.get("/clusters")
# 列出所有活动簇，支持 city_code 筛选
# 返回：cluster_id, name_zh, city_code, level, default_duration, anchor_entities, is_active
# 从 activity_clusters 表查询

@router.get("/clusters/{cluster_id}")
# 单个簇详情 + 关联的 circle_entity_roles

@router.patch("/clusters/{cluster_id}")
# 更新簇的基础字段（name_zh, level, is_active, notes 等）
```

记得在 `app/main.py` 注册路由：`app.include_router(clusters_router, prefix="/ops", tags=["ops"])`

前端 API route：`web/app/api/admin/clusters/route.ts`（透传到后端）

**页面功能**：
- 表格列：簇 ID | 中文名 | 城市 | 等级 | 默认时长 | anchor 实体数 | 是否启用
- 按城市筛选
- 点击展开：显示 anchor_entities JSON 内容 + 关联的 circle_entity_roles 列表
- 可编辑 is_active 开关

### 9. 数据仪表板 [中等]
**新建文件**：`web/app/admin/dashboard/page.tsx`
**后端**：新建 `app/api/ops/dashboard.py`

**后端 API**：
```python
@router.get("/dashboard/stats")
# 返回：
# - entity_counts: {city_code: {poi: N, hotel: N, restaurant: N}}
# - trust_distribution: {verified: N, unverified: N, ai_generated: N, suspicious: N, rejected: N}
# - source_distribution: {google: N, tabelog: N, osm: N, ai: N, ctrip: N, dianping: N}
# - cluster_stats: {total: N, with_anchors: N, without_anchors: N}
# - recent_entities: 最近 10 条新增实体
```

**页面功能**：
- 顶部：4 个数字卡片（总实体数、已验证数、活动簇数、待审核数）
- 中间左：按城市的实体数量柱状图（用简单 div 柱状图，不引入图表库）
- 中间右：trust_status 分布饼图（用 CSS 圆环）
- 底部：最近新增的 10 条实体列表

### 10. 爬虫任务触发 [简单]
**新建文件**：`web/app/admin/crawl/page.tsx`
**后端**：新建 `app/api/ops/crawl.py`

**后端 API**：
```python
@router.post("/crawl/city")
# 参数：city_code, entity_types (list: poi/hotel/restaurant/specialty_shop)
# 触发 run_city_pipeline() 作为后台任务
# 返回 job_id

@router.get("/crawl/status/{job_id}")
# 查询抓取任务状态
```

**页面功能**：
- 城市下拉选择
- 勾选要抓取的类型（景点/酒店/餐厅/特色店铺）
- "开始抓取"按钮
- 下方显示最近的抓取任务列表和状态

### 11. 管理后台导航侧边栏 [简单]
**修改文件**：`web/app/admin/layout.tsx`

当前 admin 没有导航菜单，各页面之间靠 URL 跳转。增加左侧导航栏：

```
📊 数据概览    /admin/dashboard
📋 订单看板    /admin
🏨 内容库      /admin/catalog
🗺️ 活动簇      /admin/clusters
🔄 数据抓取    /admin/crawl
⚙️ 配置管理    /admin/config
📈 转化分析    /admin/conversion
🔍 链路追踪    /admin/trace
```

- 左侧固定 sidebar（宽 200px），当前页面高亮
- 移动端折叠为汉堡菜单
- catalog 页面的"← 返回后台"链接可以去掉（有侧边栏就不需要了）

---

## 三、整体优先级

**第一批（最重要）**：
1. 任务 11 — 导航侧边栏（所有页面都需要）
2. 任务 9 — 数据仪表板（进入后台第一眼看到的）
3. 任务 1-5 — catalog 页面 trust_status + 筛选

**第二批**：
4. 任务 6-7 — catalog 批量审核 + 详情增强
5. 任务 8 — 活动簇管理

**第三批**：
6. 任务 10 — 爬虫任务触发

## 验证标准
- 本地 `from app.main import app` 不报错
- 管理后台能看到 trust_status 列和数据来源列
- 能按 trust_status 筛选
- 能批量选择并更新 trust_status
- 展开详情能看到坐标和 google_place_id
- 侧边栏导航能在所有 admin 页面正常显示和跳转
- 数据仪表板能显示统计数字
- 活动簇管理页能列出所有簇
- 部署到 ECS 后远程也能正常访问
