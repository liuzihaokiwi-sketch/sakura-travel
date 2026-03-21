## MODIFIED Requirements

### Requirement: 问卷题目集合
问卷 QUESTIONS 数组 SHALL 在 `style` 题之前包含 `japan_experience` 和 `play_mode` 两道新题，共 7 道题（destination → duration → party → japan_experience → play_mode → style → wechat）。

#### Scenario: japan_experience 题展示
- **WHEN** 用户完成前三道基础题
- **THEN** 第 4 题显示「你去过日本几次？」，选项为：第一次去（first_time）/ 去过 1–2 次（few_times）/ 去过很多次，想玩得更深（experienced）

#### Scenario: play_mode 题展示
- **WHEN** 用户完成 japan_experience 题
- **THEN** 第 5 题显示「这次更想怎么玩？」，选项为：多城顺玩（multi_city）/ 一地深玩（single_city）/ 还没想好，给我建议（undecided）

#### Scenario: 两道新题自动跳转
- **WHEN** 用户选择任意单选项
- **THEN** 300ms 后自动跳至下一题，无需点"下一步"

### Requirement: 提交 payload 包含新字段
提交 API 的 payload SHALL 包含 `japan_experience` 和 `play_mode` 两个字段，均为可选（用户未答时传 null）。

#### Scenario: 正常提交带新字段
- **WHEN** 用户完整填写两道新题后提交
- **THEN** payload 中包含 `japan_experience: "first_time" | "few_times" | "experienced"` 和 `play_mode: "multi_city" | "single_city" | "undecided"`

#### Scenario: 后端未存储新字段时不报错
- **WHEN** 后端 `/quiz` 接口尚未处理新字段
- **THEN** 提交仍成功（后端忽略未知字段），不影响现有流程
