# 活动簇系统：待办任务

> 最后更新: 2026-03-29

---

## 已完成（归档）

以下工作已在 2026-03-28/29 完成，不再跟踪：

- activity_clusters 核心字段全量回填（city_code / experience_family / rhythm_role / energy_level）
- anchor_entities JSONB 字段添加 + 全圈补齐（weak_anchor = 0）
- circle_entity_roles 自动绑定（新增 424 条）
- meal_break_minutes 重复字段删除
- 废弃 seed 脚本清理（seed_complete_clusters / seed_phase2_real_circles）
- scripts/README.md 执行顺序文档

---

## 待办任务

### P1：到达日/雨天标记

在 activity_clusters 的 `profile_fit` JSONB 字段中增加标签：

```python
profile_fit: ["arrival_friendly", "indoor_friendly", ...]
```

**arrival_friendly**：到达日适合（半天、不累、离车站近）
**indoor_friendly**：雨天可用（全室内或主要室内）

标记范围：所有 329 个活动簇，由 AI 批量判断。

### P1：体验类型重标记

部分 shrine/citynight 标记不准确，影响节奏编排：

| 当前标记 | 活动 | 建议改为 |
|---------|------|---------|
| shrine | 京都·二条城+西阵织会馆 | locallife |
| shrine | 高山·春秋祭季节线 | flower |
| citynight | 福冈·博多屋台夜食文化线 | food |
| shrine | 大阪·天神祭船渡御烟花线 | festival（或 flower） |

---

## 新城市圈自动化流程

### 设计原则

人工只做决策（选圈、审核、提供图片），执行全自动。

### 一条命令搞定

```bash
python scripts/bootstrap_circle.py --circle okinawa_island \
    --name-zh "冲绳海岛圈" \
    --base-cities naha \
    --extension-cities ishigaki,miyako,kerama \
    --region japan
```

### 自动化步骤

1. **定义城市圈** — 检查 circle_id 唯一、city_code 存在、写入 city_circles
2. **生成活动簇 + anchor_entities** — AI 生成，自动校验（B级占比>=20%、experience_family 分布<=35%、anchor_entities 非空）
3. **实体采集 + 绑定** — 从 anchor_entities 反推需要的实体 → 对比 DB 找缺口 → 定向生成 → 自动建 circle_entity_roles
4. **知识包 + 内容包** — AI 生成 8 section 知识包 + persona，自动注册
5. **验证** — clusters>=15、S级>=3、B级>=20%、实体覆盖>=90%、知识包非空
6. **图片素材** — 唯一人工环节

### 校验规则

```python
def validate_clusters(clusters: list[dict]) -> list[str]:
    # 1. city_code 在 CITY_MAP
    # 2. 必须有 experience_family / rhythm_role / energy_level
    # 3. B 级占比 >= 20%
    # 4. experience_family 任一类型不超 35%
    # 5. 至少 1 个 arrival_friendly
    # 6. notes >= 20 字
    # 7. anchor_entities 非空，S 级 >= 3 个
    # 8. 无重复 cluster_id
```

### 验收标准

```python
def validate_circle_complete(circle_id: str) -> dict:
    return {
        "clusters_count": ...,          # >= 15
        "s_level_count": ...,           # >= 3
        "b_level_ratio": ...,           # >= 0.20
        "entity_coverage": ...,         # S级实体覆盖 >= 90%
        "entity_roles_bound": ...,      # 每簇至少 1 anchor_poi
        "knowledge_pack": ...,          # 非 None
        "content_pack": ...,            # 有 PERSONA_NAME
        "page_pipeline_ok": ...,        # demo 输出有真实景点名
    }
```
