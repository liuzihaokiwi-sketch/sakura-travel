# 关西城市圈"玩什么"数据采集方案

> 更新日期: 2026-03-31
> 状态: Phase 1 完成，Phase 2 待执行

---

## 一、背景与目标

### 问题
之前的爬虫思路是**按数据源盲拉实体**（Google Places、Tabelog等），导致：
- 实体跟活动簇定义不对应
- 拉到一堆不需要的数据，有用的反而没覆盖
- 没有统一的分类和评级标准

### 新思路
**先定义"玩什么" → 再按分类去采集 → 多源交叉验证**

### 目标
为关西城市圈建立完整的景点/活动数据库，每个条目带：
- 统一的分类体系
- S/A/B/C星级评定 + 画像加成
- 季节限定信息
- 多数据源交叉验证

---

## 二、关西城市圈范围（10府县）

| 府县 | 子区域 | 定位 |
|------|--------|------|
| **大阪** | 大阪市区、堺、岸和田 | 核心base city |
| **京都** | 京都市区、宇治、天桥立、伊根、美山 | 核心base city |
| **兵库** | 神户、姫路、有马、城崎、淡路岛 | 温泉+世界遗产 |
| **奈良** | 奈良市区、吉野、明日香 | 古都+自然 |
| **滋贺** | 大津、彦根、近江八幡、长浜 | 琵琶湖圈 |
| **和歌山** | 和歌山市、白浜、高野山、熊野古道 | 世界遗产+海 |
| **三重** | 伊势、志摩 | 伊势神宫 |
| **福井** | 福井市、敦贺、勝山 | 恐龙博物馆+永平寺 |
| **鸟取** | 鸟取市、境港 | 砂丘 |
| **德岛** | 鸣门、祖谷 | 漩涡+溪谷 |

---

## 三、分类体系

### 主类型 + 子类

**A. 固定地点类 (fixed_spot)** — 有明确地址的景点
| 子类 | 说明 |
|------|------|
| culture_art | 文化艺术：美术馆、博物馆、文化设施 |
| history_religion | 历史宗教：神社、寺庙、古城、遗迹 |
| landmark_view | 地标观景：展望台、标志性建筑 |
| animal_science | 动物海洋科普：水族馆、动物园、科学馆 |
| nature_scenery | 自然景观：公园、山、湖、瀑布、海岸 |
| amusement | 游乐休闲：主题乐园、娱乐设施 |
| shopping_specialty | 购物/特色店铺：商场、市场、特色街 |

**B. 区域目的地类 (area_dest)** — 逛一片区域为主
| 子类 | 说明 |
|------|------|
| historic_district | 老城历史区 |
| shopping_district | 商圈购物区 |
| onsen_resort | 温泉/度假区 |

**C. 体验/活动类 (experience)** — 要"做"的事
| 子类 | 说明 |
|------|------|
| day_trip | 半日/一日游 |
| cultural_exp | 文化体验（和服、茶道、料理教室） |
| outdoor_sport | 户外运动 |
| night_show | 演出夜游 |
| seasonal_event | 节庆限定 |

### 特色标签（可叠加）
特色景点、特色商店、品牌体验馆、百年老店、城市代表伴手礼点、工厂参观、本地限定、复合型目的地

### 适合人群标签
亲子、雨天友好、拍照强、夜间强、无障碍、免费、需预约

---

## 四、评级体系（S/A/B/C + 画像加成）

### 基础等级

| 等级 | 含义 | 决策逻辑 | 关西数量 |
|------|------|----------|----------|
| **S** | 关西名片 | 去关西就该去，不去等于没来 | 13 |
| **A** | 目的地级 | 值得为它专门安排半天以上 | 56 |
| **B** | 行程增色 | 值得编入当天计划 | 78 |
| **C** | 顺路收录 | 附近才去 | 24 |

### 画像加成（+1升级 / -1降级）

| 画像维度 | 说明 |
|----------|------|
| first_kansai | 首次关西，时间3-5天 |
| revisit | 深度复访，想看不一样的 |
| family_kids | 带小孩 |
| couple | 情侣/蜜月 |
| culture_deep | 对历史宗教特别感兴趣 |
| nature_outdoor | 喜欢徒步、自然景观 |
| foodie | 以吃为核心 |
| photo | 出片优先 |
| time_tight | 3天以内快节奏 |

### 举例
```
伏见稻荷大社  S  [photo+1, first_kansai+1]
姫路城        A  [culture_deep+1→S, time_tight-1→B]
海游馆        B  [family_kids+1→A, couple+1→A]
USJ          S  [culture_deep-1→A]
高野山奥之院  A  [culture_deep+1→S]
```

---

## 五、当前数据状态

### Phase 1 完成：171景点 + 41季节活动

| 区域文件 | 景点 | 活动 | S | A | B | C |
|----------|------|------|---|---|---|---|
| kyoto_city.json | 48 | 7 | 7 | 13 | 20 | 8 |
| kyoto_extended.json | 7 | 2 | 0 | 4 | 2 | 1 |
| osaka_city.json | 24 | 5 | 3 | 6 | 10 | 5 |
| hyogo.json | 32 | 8 | 1 | 12 | 15 | 4 |
| nara.json | 22 | 9 | 2 | 8 | 11 | 1 |
| shiga.json | 10 | 3 | 0 | 3 | 7 | 0 |
| wakayama.json | 13 | 3 | 0 | 6 | 5 | 2 |
| mie_fukui_tottori_tokushima.json | 15 | 4 | 0 | 4 | 8 | 3 |
| **合计** | **171** | **41** | **13** | **56** | **78** | **24** |

### S级13个关西名片
1. 伏见稻荷大社（京都）
2. 清水寺（京都）
3. 金阁寺（京都）
4. 岚山竹林（京都）
5. 岚山地区（京都）
6. 祇园（京都）
7. 东山散步道（京都）
8. 日本环球影城（大阪）
9. 道顿堀（大阪）
10. 大阪城（大阪）
11. 奈良公园·鹿（奈良）
12. 东大寺（奈良）
13. 姫路城（兵库）

### 数据文件位置
```
data/kansai_spots/
├── taxonomy.json              # 分类体系定义
├── data_sources_registry.json # 22+数据源注册表
├── kyoto_city.json            # 京都市区
├── kyoto_extended.json        # 宇治/天桥立/伊根/美山
├── osaka_city.json            # 大阪市区
├── hyogo.json                 # 神户/姫路/有马/城崎/淡路
├── nara.json                  # 奈良市区/吉野/明日香
├── shiga.json                 # 滋贺
├── wakayama.json              # 和歌山
└── mie_fukui_tottori_tokushima.json  # 三重/福井/鸟取/德岛
```

### 每条数据的JSON结构
```json
{
  "id": "kyo_fushimi_inari",
  "name_zh": "伏见稻荷大社",
  "name_ja": "伏見稲荷大社",
  "name_en": "Fushimi Inari Taisha",
  "main_type": "fixed_spot",
  "sub_type": "history_religion",
  "grade": "S",
  "grade_reason": "关西最具辨识度的景点之一...",
  "profile_boosts": { "photo": "+1", "first_kansai": "+1" },
  "tags": ["拍照强", "夜间强", "免费", "本地限定"],
  "best_time": "清晨6-7点或傍晚",
  "visit_minutes": 90,
  "best_season": "all",
  "seasonal_highlights": ["..."],
  "coord": [34.9671, 135.7727],
  "tips": "山顶往返约2小时..."
}
```

---

## 六、数据源与交叉验证

### 已注册的22+数据源

| 数据源 | 类型 | 语言 | 验证状态 |
|--------|------|------|----------|
| japan-guide.com | 编辑 | EN | ✅ 已完成 |
| 乐吃购！日本 (letsgojp) | 编辑 | ZH-TW | ✅ 已完成 |
| kyoto.travel 官方 | 官方 | ZH-CN | ✅ 已完成 |
| 波比看世界 | 博主 | ZH-TW | ✅ 已完成 |
| MATCHA | 编辑 | ZH-TW | ✅ 已完成 |
| Klook 客路 | 平台 | ZH-TW | ✅ 已完成 |
| Go飞行 | 博主 | ZH-TW | ✅ 已完成 |
| JNTO 中文站 | 官方 | ZH-CN | ⏳ 待验证 |
| 马蜂窝 | UGC | ZH-CN | ⏳ 待验证 |
| 携程 | UGC | ZH-CN | ⏳ 待验证 |
| 小红书 | UGC | ZH-CN | ⏳ 需Chrome登录 |
| B站 | UGC | ZH-CN | ⏳ 需Chrome登录 |
| Google Places API | API | Multi | 可用(省着用) |
| Tabelog | 平台 | JA | 可用(餐厅专用) |

### 交叉验证逻辑
- 3个以上独立数据源推荐 → S/A级置信度高
- 2个数据源推荐 → B级合理
- 仅1个数据源 → 需人工审核
- UGC高频但官方未列 → 检查是否"特色景点"类（如八坂庚申堂）

---

## 七、工具链

### OpenCLI（已安装）
- 位置: `D:\projects\projects\travel-ai\opencli-main`
- 用途: 小红书/B站数据采集（需Chrome扩展+登录）
- 关键命令:
  - `opencli xiaohongshu search -q "京都必去" -f json`
  - `opencli bilibili subtitle --bvid {id}`

### 现有爬虫
- Google Places API → 坐标/评分/营业时间补充
- Tabelog → 餐厅评分
- OSM/Overpass → 地理数据

---

## 八、下一步计划

### Phase 2: UGC交叉验证（待执行）
1. 用户在Chrome登录小红书
2. 用OpenCLI批量搜索关键词
3. 提取高频景点 → 验证星级
4. 提取特色标签（拍照、亲子、雨天等）

### Phase 3: 导入DB
1. 写Python脚本将JSON导入entity_base表
2. 映射到现有entity_tags体系（新增namespace: grade/profile_boost）
3. 关联到activity_clusters

### Phase 4: 扩展到其他城市圈
- 北海道城市圈
- 东京城市圈
- 九州城市圈
- 按同样模式: taxonomy → 骨架数据 → 交叉验证 → 导入DB

---

## 九、质量标准

- **目标**: "十个日本旅游专家"级别
- **tips字段**: 必须是可操作的实用信息，不是空泛描述
- **grade_reason**: 必须说清"为什么是这个级别"
- **profile_boosts**: 必须有逻辑依据
- **coord**: 精确到小数点后4位
- **数据源优先级**: 真实数据 > AI判断，AI只做辅助分类和评级
