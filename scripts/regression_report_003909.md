# Travel AI Regression Report

- Generated at: 2026-03-27 00:39
- Case count: 1

## Assertions

- PASS: 24
- FAIL: 2

## 标准型 · 情侣首次关西

- case_id: `standard`
- description: 最常见用户画像，验证主链路是否稳定输出
- day_count: 6
- cities: kyoto, osaka
- hotel_cities: kyoto, osaka

### Assertion Results

- [PASS] 天数>=6: 实际6天
- [PASS] 天数<=6: 实际6天
- [PASS] 包含走廊 fushimi: 实际: {'namba', 'higashiyama', 'arashiyama', 'fushimi'}
- [PASS] 包含走廊 arashiyama: 实际: {'namba', 'higashiyama', 'arashiyama', 'fushimi'}
- [PASS] 包含走廊 higashiyama: 实际: {'namba', 'higashiyama', 'arashiyama', 'fushimi'}
- [PASS] Day1 是 arrival 类型: 实际: arrival
- [PASS] 最后一天是 departure 类型: 实际: departure
- [PASS] 返程日节奏在 ['light', 'balanced'] 内: 实际: light
- [PASS] 含主题公园日(day_type=theme_park): day_types: ['arrival', 'normal', 'normal', 'theme_park', 'normal', 'departure']
- [PASS] 无{'tokyo'}餐厅混入: 通过
- [PASS] 餐厅走廊一致性(lunch+dinner): 通过
- [PASS] 无 raw key 泄露: 通过
- [PASS] 返程日标题不含不当主题: 标题: '返程日 · 难波·道顿堀·心斋桥 · 轻松收尾'
- [PASS] 关键决策同源验证: 通过
- [PASS] 住宿覆盖城市 ['kyoto', 'osaka']: 实际住宿城市: ['kyoto', 'osaka']
- [PASS] 返程日无主景点(POI): 通过
- [PASS] 返程日无午/晚餐: 通过
- [FAIL] 主题公园日有专属标题: 标题: ['难波·道顿堀·心斋桥 · 住大阪·难波']
- [PASS] 同源:evidence_bundle存在: run_id=5402899d…
- [PASS] 同源:无pending约束: 通过
- [PASS] 同源:hard约束无unconsumed: 通过
- [PASS] 同源:run_id一致: 通过
- [PASS] 质量:day_mode全覆盖: modes=['arrival_light', 'classic_first_trip', 'classic_first_trip', 'theme_park_full', 'food_local', 'departure_light']
- [FAIL] 质量:day_mode与标题一致: 问题: ["Day4: mode=theme_park_full but title='难波·道顿堀·心斋桥 · 住大阪·难波'"]
- [PASS] 质量:micro-route覆盖: 5/6 天有 micro-route
- [PASS] 质量:fusion后硬约束0违规: applied=True, patches=0

### Itinerary Summary

- Day 1 | 京都 | 到达日 · 京都·伏见稻荷 · 住京都·河原町 | 到达日
- Day 2 | 京都 | 京都·岚山嵯峨野线 · 住京都·河原町 | 全日深游
- Day 3 | 京都 | 京都·东山祇园经典线 · 住京都·河原町 | 全日深游
- Day 4 | 大阪 | 难波·道顿堀·心斋桥 · 住大阪·难波 | 主题公园日
- Day 5 | 大阪 | 大阪·道顿堀南区美食夜游 · 住大阪·难波 | 全日深游
- Day 6 | 大阪 | 返程日 · 难波·道顿堀·心斋桥 · 轻松收尾 | 返程日
