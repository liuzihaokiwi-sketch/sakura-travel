## ADDED Requirements

### Requirement: 单一产品配置模型

系统 SHALL 维护一份 `product_config.json` 作为所有产品定义的唯一真相源。所有前端页面、客服话术、后台逻辑、API 校验 MUST 从此配置读取，禁止硬编码。

```json
{
  "tiers": {
    "free_preview": {
      "name_cn": "免费体验",
      "price_cny": 0,
      "preview_days": 1,
      "preview_day_selection": "best_score",
      "visible_modules": ["timeline", "poi_names", "poi_one_liner", "transport_overview", "hero_image"],
      "locked_modules": ["restaurant_names", "hotel_info", "transport_detail", "tips", "other_days_detail"],
      "teaser_modules": ["other_days_titles", "restaurant_existence", "rain_backup_teaser", "total_recommendation_count"],
      "self_serve_tuning": false,
      "formal_modifications": 0,
      "shareable": true,
      "exportable": false
    },
    "standard": {
      "name_cn": "行程优化版",
      "price_cny": 248,
      "original_price_cny": 298,
      "full_days": true,
      "visible_modules": ["all"],
      "locked_modules": [],
      "self_serve_tuning": true,
      "formal_modifications": 1,
      "includes": ["完整多日行程", "餐厅精选推荐", "酒店区域指南", "交通详细指引", "避坑指南", "雨天备案", "出行准备清单"],
      "shareable": true,
      "exportable": true
    },
    "premium": {
      "name_cn": "深度管家版",
      "price_cny": 888,
      "full_days": true,
      "visible_modules": ["all"],
      "locked_modules": [],
      "self_serve_tuning": true,
      "formal_modifications": 3,
      "includes_extra": ["专属规划顾问", "旅前 1v1 答疑", "预约代办协助", "旅中紧急支持"],
      "shareable": true,
      "exportable": true,
      "wechat_vip": true
    }
  },
  "tuning_rules": {
    "self_serve_allowed": ["replace_poi", "replace_restaurant", "adjust_pace", "remove_poi", "adjust_start_time", "switch_night_plan"],
    "formal_required": ["change_city", "change_date", "change_route_skeleton", "free_text_request"],
    "self_serve_cooldown_per_entity": 5,
    "self_serve_cooldown_window_hours": 24
  },
  "copy_rules": {
    "forbidden_words": ["AI生成", "自动生成", "算法", "引擎", "模型", "维度", "评分系统"],
    "allowed_expressions": ["专业团队", "规划师", "多源数据校验", "专业判断框架"],
    "tone": "professional_warm"
  }
}
```

#### Scenario: 前端读取配置

- **WHEN** 预览页渲染时
- **THEN** 从 `GET /config/product` API 读取 free_preview tier 的 visible_modules / locked_modules / teaser_modules，据此决定展示/锁定/半露出

#### Scenario: 后台校验修改次数

- **WHEN** 用户提交正式精调请求
- **THEN** 系统从 product_config 读取该用户 tier 的 formal_modifications 剩余次数，不足则拒绝并引导升级

#### Scenario: 配置更新影响全局

- **WHEN** 产品经理更新 standard tier 的 formal_modifications 从 1 改为 2
- **THEN** 所有读取该配置的前端页面、客服话术模板、后台校验逻辑自动生效

### Requirement: 配置版本化

product_config SHALL 有版本号（semver），每次修改 MUST 递增版本号。系统 SHALL 记录每个订单创建时使用的配置版本，保证"按下单时的规则执行"。

#### Scenario: 订单绑定配置版本

- **WHEN** 用户在 config v1.2.0 时下单标准版
- **THEN** 订单记录 config_version = "1.2.0"，该订单的权益按 v1.2.0 定义执行，即使后续配置更新

### Requirement: 自助微调与正式修改次数边界

系统 SHALL 严格区分自助微调和正式修改：

| 类型 | 是否消耗修改次数 | 是否需要人工介入 | 触发方式 |
|------|----------------|----------------|---------|
| 替换景点（从候选中选） | ❌ 不消耗 | ❌ 不需要 | 用户在交付页点击 |
| 替换餐厅（从候选中选） | ❌ 不消耗 | ❌ 不需要 | 用户在交付页点击 |
| 调整当天节奏 | ❌ 不消耗 | ❌ 不需要 | 用户滑杆调节 |
| 删除某景点 | ❌ 不消耗 | ❌ 不需要 | 用户点击"不想去" |
| 调整出发时间 | ❌ 不消耗 | ❌ 不需要 | 用户时间选择器 |
| 切换夜间方案 | ❌ 不消耗 | ❌ 不需要 | 用户切换选项 |
| 改城市/日期/路线骨架 | ✅ 消耗 | ✅ 需要 | 用户提交正式请求 |
| 自由文字需求 | ✅ 消耗 | ✅ 需要 | 用户提交正式请求 |
| 自助微调后仍不满意 | ✅ 消耗 | ✅ 需要 | 用户点击"仍不满意" |

#### Scenario: 自助微调不消耗次数

- **WHEN** 标准版用户替换了 3 个景点和 2 个餐厅
- **THEN** 正式精调次数仍为 1 次，未消耗

#### Scenario: 正式精调消耗次数

- **WHEN** 标准版用户提交"我想把京都那天改成奈良"的正式请求
- **THEN** 消耗 1 次正式精调次数，进入人工审核队列
