# 09 Layer 2 City-Circle Policy Modules

## 文档定位

本文档只定义 Layer 2 的 policy bundle 主合同、来源层次、归属和禁区。

它解决的是定义问题，不是宣称六城市圈实现已经完全统一。当前代码里确实已经存在：

- `policy_resolver.py` 中的默认 bundle 与圈层 override
- `config_resolver.py` 中的运营配置合并
- `city_circle_selector.py`、`constraint_compiler.py` 对 policy 的读取

但这不等于：

- 所有 policy 都已经配置化
- 所有 override 都已经归于同一个运营面
- Layer 2 已经完全摆脱 compatibility path

## 继续废弃的旧前提

- Japan-only 仍是 Layer 2 默认范围
- 扩六城市圈等于继续拆更多 planner
- 只要 itinerary 能产出，就不需要显式 policy source
- code default、运营配置、人工 override 可以混着算“同一种规则来源”

## 新边界下 Layer 2 的主原则

### 1. 主链只有一条

Layer 2 的主链仍应理解为：

`normalize -> circle selection -> constraint compile -> hotel/base strategy -> skeleton building -> secondary fill -> scoring -> explanation`

变化应该注入到统一主链里，而不是拆成多条 planner 链。

### 2. 差异来自 policy pack，不来自 planner 分叉

六城市圈扩展的默认表达方式应当是：

- one pipeline
- many policy packs
- one evidence format

而不是：

- tokyo planner
- hokkaido planner
- xinjiang planner

### 3. policy bundle 必须可追溯来源

当前代码现实已经形成三层来源，但还没有达到“完全统一运营面”：

1. `policy_resolver.py` 的代码默认值与圈层 override
2. `config_resolver.py` 的配置包合并结果
3. 运行时按 circle / segment / plan override 叠加出的快照

因此当前正确说法是：

- Layer 2 已经有显式 `sources` 概念
- Layer 2 还不能宣称 policy ops 完全统一完成

## Policy Bundle 的正式来源层次

当前主口径固定为：

1. `default`
2. `circle_override`
3. `config_resolver` 输出的 config snapshot
4. 未来 operator / plan override

这里要特别区分两件事：

- `policy_resolver.py` 决定的是“主 bundle 结构和静态默认差异”
- `config_resolver.py` 决定的是“运营层阈值、开关、权重快照”

不要把后者写成前者的附注，也不要把前者写成“只是临时硬编码所以可忽略”。

## 当前正式模块集合

当前 Layer 2 应被理解为以下显式模块集合：

1. `city_circle_profile`
2. `mobility_policy`
3. `climate_and_season_policy`
4. `routing_style_policy`
5. `hotel_base_policy`
6. `day_frame_policy`
7. `booking_and_reservation_policy`

注意：

- `exception_policy` 还没有以同等正式度落成独立主模块
- 因此不能宣称 Layer 2 policy system 已经完整闭合

## 各模块在主链中的读取边界

### `circle_selection`

主要读取：

- `city_circle_profile`
- `mobility_policy`
- `climate_and_season_policy`

边界说明：

- 用户显式 `requested_city_circle` 应被优先尊重并校验
- 从 `destination` 推断 circle 仍然存在于 intake contract 中
- 所以现在不能把“用户显式指定圈层”写成已经完全替代推断逻辑

### `constraint_compile`

主要读取：

- `mobility_policy`
- `climate_and_season_policy`
- `routing_style_policy`
- `hotel_base_policy`
- `day_frame_policy`
- `booking_and_reservation_policy`

边界说明：

- 这些 policy 已经进入 `resolved_policy_snapshot`
- 但不同约束的下游消费程度并不一致
- 尤其 `booked_items`、`must_stay_area` 等仍不能写成“已完全主消费”

### `hotel/base strategy` 与 `skeleton`

文档上应继续按“应读取 policy bundle”来描述。

但当前状态只能写成：

- policy contract 已进入这些阶段的设计边界
- 并非所有 policy 约束都已在下游完全硬消费

## 当前最容易误判的三个边界

### 1. “有了六城市圈 override” 不等于 “policy ops 统一完成”

当前代码里圈层差异主要仍落在：

- `_POLICY_OVERRIDES`
- `ConfigResolver`

这说明：

- 来源层次已经开始显式化
- ownership 和运营入口还没有完全收成单一面

### 2. “constraint 里带了 resolved_policy_snapshot” 不等于 “所有 policy 都已被完整消费”

`constraint_compiler.py` 已把 policy 写入 evidence，但部分消费者仍是：

- 部分消费
- 软约束消费
- 或尚未完全锁死

因此不能把 evidence presence 写成 full integration。

### 3. “selector / compiler 都读 policy” 不等于 “compatibility path 已退出”

只要 `generate_trip` 仍然可能进入：

- `FULL_LEGACY`
- `MAJOR_LEGACY`
- `FILLER_LEGACY`
- `SECTION_ADAPTER`

Layer 2 就仍处在“主链建立中，兼容链保留中”的状态。

## Owner 与维护归属

当前文档口径固定如下：

- `policy_resolver.py` 是 Layer 2 主 policy 合同的代码真相源
- `config_resolver.py` 是运营配置来源层的主入口
- `09_layer2_city_circle_policy_modules.md` 是 owner-facing 的定义口径文件

不要把归属写成：

- “规则都在代码里，文档只是解释”
- “规则都在运营后台，代码默认值不重要”

当前真实状态是双层共存，且必须同时被记录。

## 对后续模型分工的约束

以下事项属于定义层主工作，优先由更强定义型模型处理：

- policy source hierarchy wording
- ownership wording
- 模块正式性判断
- “已接入”“已主消费”“已统一运营化”三者之间的区分

以下事项可以安全交给 `gpt-5.3-codex`：

- 在既有来源层次下补测试
- route / serializer / admin 页面按既定 contract 对齐
- 针对已定义模块补实现或补 traces

## 最终口径

Layer 2 现在可以正式说的是：

- 主 policy bundle 合同已经出现
- 差异表达应走 policy pack，不应再默认走 planner 分叉
- policy source 已经开始显式化

Layer 2 现在不能宣称的是：

- policy ops 架构统一完成
- 六城市圈 policy 已全部配置化
- 所有约束都已被下游完全主消费
- compatibility path 已退出
