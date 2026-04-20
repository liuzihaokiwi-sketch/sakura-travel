# xinjiang_yili_circle 活动簇清单（北疆伊犁·赛里木湖·阿勒泰扩展版）

> 版本：v1-route-circle  
> 圈层：`xinjiang_yili_circle`  
> 城市/节点：`urumqi, yili, altay, burqin, kanas, hemu, nalati, sailimu`  
> cluster_id 前缀：`xj_`  
> 核心理解：
> - 这是**自驾 / 包车导向的路线圈**，不是普通城市圈。
> - 主轴是：`乌鲁木齐集散 -> 赛里木湖 / 伊犁河谷 / 特克斯喀拉峻 / 那拉提 / 独库北段 / 伊昭公路 ->（可选北延）阿勒泰-布尔津-喀纳斯-禾木`
> - `喀纳斯 / 禾木`地理上属于阿勒泰-布尔津方向，不是伊犁核心腹地；但因为你已明确列入本圈城市池，本版作为**扩展北线主簇**一并收录。
> - 所有活动簇均按中国国内线路逻辑整理，不使用日本餐厅平台语义。
> - `upgrade_triggers.travel_months` 用于月份触发型升级；非季节簇填空数组。
> - 冬季封路、限行和分时段管制写在文末“线路运营说明”中，不强行做成活动簇。

---

## 核心主活动簇 / Anchor

### `xj_sailimu_lake_loop_core`
- `circle_id`: `xinjiang_yili_circle`
- `city_code`: `sailimu`
- `name_zh`: `北疆·赛里木湖环湖核心线`
- `name_en`: `North Xinjiang Sayram Lake Full Loop`
- `level`: `S`
- `default_duration`: `full_day`
- `primary_corridor`: `xj_sayram_lake_ringroad`
- `seasonality`: `["all_year","summer_flower","autumn"]`
- `upgrade_triggers`: `{"travel_months":["06","07","08","09"]}`
- `profile_fit`: `["self_drive","photo","couple","nature"]`
- `trip_role`: `anchor`
- `time_window_strength`: `strong`
- `reservation_pressure`: `medium`
- `secondary_attach_capacity`: `3`
- `default_selected`: `false`
- `notes`: 赛里木湖官方就以环湖风光为核心分区，真正成立的玩法不是”到湖边拍一张”，而是完整环湖、自驾停靠、观景台与湖岸步行结合；命中夏季花海和初秋蓝湖时强度最高。
- `experience_family`: `sea`
- `rhythm_role`: `peak`
- `energy_level`: `high`

### `xj_yining_city_ili_valley`
- `circle_id`: `xinjiang_yili_circle`
- `city_code`: `yili`
- `name_zh`: `伊宁·城市与伊犁河谷生活线`
- `name_en`: `Yining City & Ili Valley Life Line`
- `level`: `A`
- `default_duration`: `full_day`
- `primary_corridor`: `xj_yining_liuxingstreet_kazanqi_river`
- `seasonality`: `["all_year","summer"]`
- `upgrade_triggers`: `{"travel_months":[]}`
- `profile_fit`: `["culture","foodie","self_drive","slow_travel"]`
- `trip_role`: `anchor`
- `time_window_strength`: `medium`
- `reservation_pressure`: `low`
- `secondary_attach_capacity`: `3`
- `default_selected`: `false`
- `notes`: 伊宁不是单纯中转站；六星街、喀赞其、伊犁河夜景与民族风情共同构成伊犁谷地的人文主簇，适合在草原和公路段之间作为完整停留日。
- `experience_family`: `locallife`
- `rhythm_role`: `contrast`
- `energy_level`: `medium`

### `xj_kalajun_grassland_core`
- `circle_id`: `xinjiang_yili_circle`
- `city_code`: `yili`
- `name_zh`: `特克斯·喀拉峻草原核心线`
- `name_en`: `Tekes Kalajun Grassland Core Line`
- `level`: `S`
- `default_duration`: `full_day`
- `primary_corridor`: `xj_tekes_kalajun_koksu`
- `seasonality`: `["summer_flower","autumn"]`
- `upgrade_triggers`: `{"travel_months":["06","07","08","09"]}`
- `profile_fit`: `["self_drive","photo","nature","hiking"]`
- `trip_role`: `anchor`
- `time_window_strength`: `strong`
- `reservation_pressure`: `medium`
- `secondary_attach_capacity`: `2`
- `default_selected`: `false`
- `notes`: 喀拉峻本身就是 5A 景区和”新疆天山”世界自然遗产组成部分，不是普通草原点位；草原、峡谷、雪山和鲜花台足够支撑一整天甚至过夜型安排。
- `experience_family`: `flower`
- `rhythm_role`: `peak`
- `energy_level`: `high`

### `xj_nalati_grassland_valley`
- `circle_id`: `xinjiang_yili_circle`
- `city_code`: `nalati`
- `name_zh`: `那拉提·草原与河谷线`
- `name_en`: `Nalati Grassland & Valley Line`
- `level`: `S`
- `default_duration`: `full_day`
- `primary_corridor`: `xj_nalati_sky_grassland_valley`
- `seasonality`: `["summer_flower","autumn"]`
- `upgrade_triggers`: `{"travel_months":["06","07","08","09"]}`
- `profile_fit`: `["self_drive","family","photo","slow_travel"]`
- `trip_role`: `anchor`
- `time_window_strength`: `strong`
- `reservation_pressure`: `medium`
- `secondary_attach_capacity`: `2`
- `default_selected`: `false`
- `notes`: 那拉提的标准玩法不是一个观景台，而是”空中草原 + 河谷草原 + 牧场风情”的组合；景区本身就按不同线路组织，天然适合作为整天草原主簇。
- `experience_family`: `flower`
- `rhythm_role`: `peak`
- `energy_level`: `high`

### `xj_duku_north_roadtrip`
- `circle_id`: `xinjiang_yili_circle`
- `city_code`: `nalati`
- `name_zh`: `北疆·独库北段公路线`
- `name_en`: `Northern Duku Highway Roadtrip Line`
- `level`: `A`
- `default_duration`: `full_day`
- `primary_corridor`: `xj_duku_north_qiaorma_nalati`
- `seasonality`: `["summer_open","autumn_open"]`
- `upgrade_triggers`: `{"travel_months":["06","07","08","09"]}`
- `profile_fit`: `["self_drive","roadtrip","photo"]`
- `trip_role`: `anchor`
- `time_window_strength`: `strong`
- `reservation_pressure`: `low`
- `secondary_attach_capacity`: `1`
- `default_selected`: `false`
- `notes`: 独库北段本身就是目的地型景观公路，不只是交通段；雪墙、达坂、乔尔玛与高山草甸会直接决定行车节奏、出发时间与车辆限制。
- `experience_family`: `mountain`
- `rhythm_role`: `peak`
- `energy_level`: `high`

### `xj_yizhao_highway_conditional`
- `circle_id`: `xinjiang_yili_circle`
- `city_code`: `yili`
- `name_zh`: `伊犁·伊昭公路线（条件性）`
- `name_en`: `Ili Yizhao Highway Conditional Line`
- `level`: `A`
- `default_duration`: `full_day`
- `primary_corridor`: `xj_yizhao_s237`
- `seasonality`: `["summer_open","autumn_open"]`
- `upgrade_triggers`: `{"travel_months":["06","07","08","09","10"]}`
- `profile_fit`: `["self_drive","roadtrip","photo","experienced_traveler"]`
- `trip_role`: `anchor`
- `time_window_strength`: `strong`
- `reservation_pressure`: `none`
- `secondary_attach_capacity`: `1`
- `default_selected`: `false`
- `notes`: 伊昭公路是明显的条件性主簇：通行窗口短、限行规则多、恶劣天气随时管制；一旦开放，它会成为伊犁最强的高颜值穿越公路之一。
- `experience_family`: `mountain`
- `rhythm_role`: `peak`
- `energy_level`: `high`

### `xj_qiongkushitai_wilderness`
- `circle_id`: `xinjiang_yili_circle`
- `city_code`: `yili`
- `name_zh`: `特克斯·琼库什台深度自然线`
- `name_en`: `Tekes Qiongkushitai Deep Wilderness Line`
- `level`: `A`
- `default_duration`: `full_day`
- `primary_corridor`: `xj_qiongkushitai_wildscape`
- `seasonality`: `["summer_flower","autumn"]`
- `upgrade_triggers`: `{"travel_months":["06","07","08","09"]}`
- `profile_fit`: `["self_drive","hiking","photo","slow_travel"]`
- `trip_role`: `anchor`
- `time_window_strength`: `medium`
- `reservation_pressure`: `medium`
- `secondary_attach_capacity`: `1`
- `default_selected`: `false`
- `notes`: 琼库什台不是”顺路看一眼”的村子，而是更偏深度自然、村落、轻徒步和山谷景观的独立主簇，尤其适合愿意牺牲效率换风景的客群。
- `experience_family`: `mountain`
- `rhythm_role`: `peak`
- `energy_level`: `high`

### `xj_kanas_hemu_dualcore`
- `circle_id`: `xinjiang_yili_circle`
- `city_code`: `kanas`
- `name_zh`: `阿勒泰北线·喀纳斯湖禾木村双核线`
- `name_en`: `Altay North Loop Kanas-Hemu Dual-Core`
- `level`: `S`
- `default_duration`: `full_day`
- `primary_corridor`: `xj_burqin_kanas_hemu`
- `seasonality`: `["summer_flower","autumn","winter_snow"]`
- `upgrade_triggers`: `{"travel_months":["06","07","08","09","10","12","01","02"]}`
- `profile_fit`: `["self_drive","photo","slow_travel","family"]`
- `trip_role`: `anchor`
- `time_window_strength`: `strong`
- `reservation_pressure`: `high`
- `secondary_attach_capacity`: `2`
- `default_selected`: `false`
- `notes`: 喀纳斯湖与禾木应视为北疆扩展双核主簇，通常至少要按 2 天以上思路规划；秋色和冬雪都会显著提升其级别与停留意愿。
- `experience_family`: `sea`
- `rhythm_role`: `peak`
- `energy_level`: `high`

---

## 强次级簇 / Enrichment

### `xj_guozigou_bridge_window`
- `circle_id`: `xinjiang_yili_circle`
- `city_code`: `yili`
- `name_zh`: `伊犁·果子沟大桥沿线窗口线`
- `name_en`: `Ili Guozigou Bridge View Window`
- `level`: `B`
- `default_duration`: `quarter_day`
- `primary_corridor`: `xj_guozigou_bridge_view`
- `seasonality`: `["all_year","summer","autumn"]`
- `upgrade_triggers`: `{"travel_months":[]}`
- `profile_fit`: `["self_drive","photo","roadtrip"]`
- `trip_role`: `enrichment`
- `time_window_strength`: `strong`
- `reservation_pressure`: `none`
- `secondary_attach_capacity`: `1`
- `default_selected`: `false`
- `notes`: 果子沟大桥更像高价值”窗口线”而非单独整天簇，但它对赛里木湖进出段影响极大，必须单独保留。
- `experience_family`: `mountain`
- `rhythm_role`: `contrast`
- `energy_level`: `medium`

### `xj_lake_sunset_stargazing`
- `circle_id`: `xinjiang_yili_circle`
- `city_code`: `sailimu`
- `name_zh`: `赛湖·湖边日落星空守候线`
- `name_en`: `Sayram Lake Sunset & Stargazing Line`
- `level`: `A`
- `default_duration`: `quarter_day`
- `primary_corridor`: `xj_sayram_lake_nightshore`
- `seasonality`: `["all_year","summer","autumn"]`
- `upgrade_triggers`: `{"travel_months":["06","07","08","09"]}`
- `profile_fit`: `["couple","photo","self_drive","slow_travel"]`
- `trip_role`: `enrichment`
- `time_window_strength`: `strong`
- `reservation_pressure`: `medium`
- `secondary_attach_capacity`: `1`
- `default_selected`: `false`
- `notes`: 对赛里木湖来说，白天环湖和夜间守候是两种完全不同的体验；命中晴天和住湖边时，这条线经常直接升级为行程高光。
- `experience_family`: `sea`
- `rhythm_role`: `recovery`
- `energy_level`: `low`

### `xj_grassland_horse_riding_light`
- `circle_id`: `xinjiang_yili_circle`
- `city_code`: `nalati`
- `name_zh`: `草原·骑马轻体验线`
- `name_en`: `Grassland Light Horse-Riding Experience`
- `level`: `B`
- `default_duration`: `quarter_day`
- `primary_corridor`: `xj_grassland_horse_experience`
- `seasonality`: `["summer_flower","autumn"]`
- `upgrade_triggers`: `{"travel_months":["06","07","08","09"]}`
- `profile_fit`: `["family","photo","slow_travel"]`
- `trip_role`: `enrichment`
- `time_window_strength`: `medium`
- `reservation_pressure`: `low`
- `secondary_attach_capacity`: `1`
- `default_selected`: `false`
- `notes`: 骑马轻体验不是核心大线，但在那拉提、喀拉峻、禾木这类草原/村落场景里非常适合做半日型加挂。
- `experience_family`: `locallife`
- `rhythm_role`: `contrast`
- `energy_level`: `medium`

### `xj_herdsman_home_visit_meal`
- `circle_id`: `xinjiang_yili_circle`
- `city_code`: `yili`
- `name_zh`: `草原·牧民家访与风味餐线`
- `name_en`: `Grassland Herdsman Visit & Camp Meal`
- `level`: `B`
- `default_duration`: `quarter_day`
- `primary_corridor`: `xj_nomad_visit_experience`
- `seasonality`: `["summer_flower","autumn"]`
- `upgrade_triggers`: `{"travel_months":["06","07","08","09"]}`
- `profile_fit`: `["culture","family","slow_travel","foodie"]`
- `trip_role`: `enrichment`
- `time_window_strength`: `medium`
- `reservation_pressure`: `medium`
- `secondary_attach_capacity`: `1`
- `default_selected`: `false`
- `notes`: 牧民家访、奶茶、手抓肉、毡房风味餐非常适合放在草原主簇之下做体验型加挂，但单独不必抬得过高。
- `experience_family`: `food`
- `rhythm_role`: `contrast`
- `energy_level`: `medium`

### `xj_hemu_morningmist_night`
- `circle_id`: `xinjiang_yili_circle`
- `city_code`: `hemu`
- `name_zh`: `禾木·晨雾炊烟与夜色线`
- `name_en`: `Hemu Morning Mist & Night Scene Line`
- `level`: `A`
- `default_duration`: `quarter_day`
- `primary_corridor`: `xj_hemu_viewplatform_village`
- `seasonality`: `["summer_flower","autumn","winter_snow"]`
- `upgrade_triggers`: `{"travel_months":["06","07","08","09","10","12","01","02"]}`
- `profile_fit`: `["photo","couple","slow_travel"]`
- `trip_role`: `enrichment`
- `time_window_strength`: `strong`
- `reservation_pressure`: `high`
- `secondary_attach_capacity`: `1`
- `default_selected`: `false`
- `notes`: 禾木的真正记忆点通常落在早晨观景台、晨雾炊烟和夜晚木屋灯光，因此值得从喀纳斯大簇中拆出独立强次级簇。
- `experience_family`: `locallife`
- `rhythm_role`: `recovery`
- `energy_level`: `low`

### `xj_burqin_route_rest_supply`
- `circle_id`: `xinjiang_yili_circle`
- `city_code`: `burqin`
- `name_zh`: `布尔津·北线补给与过夜缓冲线`
- `name_en`: `Burqin North Loop Supply & Overnight Buffer`
- `level`: `B`
- `default_duration`: `half_day`
- `primary_corridor`: `xj_burqin_gateway`
- `seasonality`: `["all_year","summer","autumn","winter"]`
- `upgrade_triggers`: `{"travel_months":[]}`
- `profile_fit`: `["self_drive","family","buffer_stop"]`
- `trip_role`: `buffer`
- `time_window_strength`: `weak`
- `reservation_pressure`: `medium`
- `secondary_attach_capacity`: `1`
- `default_selected`: `false`
- `notes`: 布尔津本身未必是来北疆的理由，但在喀纳斯 / 禾木前后是极其重要的补给、过夜和体力恢复节点，路线价值很高。
- `experience_family`: `locallife`
- `rhythm_role`: `utility`
- `energy_level`: `low`

### `xj_urumqi_arrival_departure_assembly`
- `circle_id`: `xinjiang_yili_circle`
- `city_code`: `urumqi`
- `name_zh`: `乌鲁木齐·进出疆集散缓冲线`
- `name_en`: `Urumqi Arrival-Departure Assembly Buffer`
- `level`: `B`
- `default_duration`: `half_day`
- `primary_corridor`: `xj_urumqi_gateway`
- `seasonality`: `["all_year"]`
- `upgrade_triggers`: `{"travel_months":[]}`
- `profile_fit`: `["self_drive","family","buffer_stop"]`
- `trip_role`: `buffer`
- `time_window_strength`: `weak`
- `reservation_pressure`: `medium`
- `secondary_attach_capacity`: `1`
- `default_selected`: `false`
- `notes`: 对这类长线自驾圈，乌鲁木齐的核心价值在于提车、补给、休整和进出疆缓冲，而不是强行做城市观光主簇。
- `experience_family`: `locallife`
- `rhythm_role`: `utility`
- `energy_level`: `low`

---

## 季节簇 / Seasonal Upgrades

### `xj_ili_summer_flower_belt`
- `circle_id`: `xinjiang_yili_circle`
- `city_code`: `yili`
- `name_zh`: `伊犁·6-8月花期总线`
- `name_en`: `Ili Summer Flower Belt`
- `level`: `S`
- `default_duration`: `full_day`
- `primary_corridor`: `xj_ili_flower_belt`
- `seasonality`: `["summer_flower"]`
- `upgrade_triggers`: `{"travel_months":["06","07","08"]}`
- `profile_fit`: `["photo","self_drive","couple","nature"]`
- `trip_role`: `anchor`
- `time_window_strength`: `strong`
- `reservation_pressure`: `medium`
- `secondary_attach_capacity`: `2`
- `default_selected`: `false`
- `notes`: 伊犁的花期不是单点事件，而是 6 月薰衣草、6 月底至 7 月油菜花、7 月向日葵等多点接力；命中月份时应视为整条路线的升级总线。
- `experience_family`: `flower`
- `rhythm_role`: `peak`
- `energy_level`: `medium`

### `xj_northern_xinjiang_autumn_color`
- `circle_id`: `xinjiang_yili_circle`
- `city_code`: `altay`
- `name_zh`: `北疆·9月秋色升级线`
- `name_en`: `Northern Xinjiang Autumn Color Upgrade`
- `level`: `S`
- `default_duration`: `full_day`
- `primary_corridor`: `xj_autumn_color_upgrade`
- `seasonality`: `["autumn"]`
- `upgrade_triggers`: `{"travel_months":["09","10"]}`
- `profile_fit`: `["photo","self_drive","slow_travel"]`
- `trip_role`: `anchor`
- `time_window_strength`: `strong`
- `reservation_pressure`: `high`
- `secondary_attach_capacity`: `2`
- `default_selected`: `false`
- `notes`: 9 月的喀纳斯、禾木、伊犁河谷和部分草原会整体进入秋色模式，若以摄影或深度自然为导向，秋色应视为整圈升级逻辑而不是附属标签。
- `experience_family`: `mountain`
- `rhythm_role`: `peak`
- `energy_level`: `medium`

### `xj_hemu_kanas_winter_snowmode`
- `circle_id`: `xinjiang_yili_circle`
- `city_code`: `hemu`
- `name_zh`: `阿勒泰北线·冬季雪国模式`
- `name_en`: `Altay North Loop Winter Snow Mode`
- `level`: `A`
- `default_duration`: `full_day`
- `primary_corridor`: `xj_hemu_kanas_winter`
- `seasonality`: `["winter_snow"]`
- `upgrade_triggers`: `{"travel_months":["12","01","02"]}`
- `profile_fit`: `["photo","winter_travel","slow_travel"]`
- `trip_role`: `anchor`
- `time_window_strength`: `strong`
- `reservation_pressure`: `high`
- `secondary_attach_capacity`: `1`
- `default_selected`: `false`
- `notes`: 冬季的禾木 / 喀纳斯不是夏秋的简单替代，而是完全不同的雪国线路；若命中冰雪偏好，可直接转为独立冬季玩法。
- `experience_family`: `mountain`
- `rhythm_role`: `peak`
- `energy_level`: `medium`

---

### `xj_tuergen_apricot_blossom_valley`
- `circle_id`: `xinjiang_yili_circle`
- `city_code`: `yili`
- `name_zh`: `伊犁·吐尔根杏花沟花期线`
- `name_en`: `Ili Turgen Apricot Blossom Valley Route`
- `level`: `A`
- `default_duration`: `full_day`
- `primary_corridor`: `xj_tuergen_xinyuan_apricot_valley`
- `seasonality`: `["spring"]`
- `upgrade_triggers`: `{"travel_months":["04"]}`
- `profile_fit`: `["photo","self_drive","couple","nature"]`
- `trip_role`: `anchor`
- `time_window_strength`: `strong`
- `reservation_pressure`: `medium`
- `secondary_attach_capacity`: `1`
- `default_selected`: `false`
- `notes`: 吐尔根杏花沟的价值不在”顺路看花”，而在 4 月前后极短花期内专门追花；命中花况时会直接影响伊宁 / 新源驻点与出发顺序。
- `experience_family`: `flower`
- `rhythm_role`: `peak`
- `energy_level`: `medium`

### `xj_xiata_glacier_trail`
- `circle_id`: `xinjiang_yili_circle`
- `city_code`: `yili`
- `name_zh`: `昭苏·夏塔古道雪山徒步线`
- `name_en`: `Zhaosu Xiata Ancient Trail & Glacier Route`
- `level`: `A`
- `default_duration`: `full_day`
- `primary_corridor`: `xj_zhaosu_xiata_glacier_valley`
- `seasonality`: `["summer","autumn"]`
- `upgrade_triggers`: `{"travel_months":["06","07","08","09"]}`
- `profile_fit`: `["hiking","photo","self_drive","nature"]`
- `trip_role`: `anchor`
- `time_window_strength`: `strong`
- `reservation_pressure`: `medium`
- `secondary_attach_capacity`: `1`
- `default_selected`: `false`
- `notes`: 夏塔的成立方式是”昭苏进山 + 雪山峡谷轻徒步 / 观景车”的完整一天，强依赖早入园与天气窗口，常会把住宿拉到昭苏一侧。
- `experience_family`: `mountain`
- `rhythm_role`: `peak`
- `energy_level`: `high`

---

## 建议优先级

### P0｜最应先入库
- `xj_sailimu_lake_loop_core`
- `xj_yining_city_ili_valley`
- `xj_kalajun_grassland_core`
- `xj_nalati_grassland_valley`
- `xj_duku_north_roadtrip`
- `xj_qiongkushitai_wilderness`
- `xj_kanas_hemu_dualcore`

### P1｜强次级与条件性高价值簇
- `xj_yizhao_highway_conditional`
- `xj_lake_sunset_stargazing`
- `xj_guozigou_bridge_window`
- `xj_herdsman_home_visit_meal`
- `xj_hemu_morningmist_night`
- `xj_ili_summer_flower_belt`
- `xj_northern_xinjiang_autumn_color`
- `xj_tuergen_apricot_blossom_valley`
- `xj_xiata_glacier_trail`

### P2｜缓冲与运营必要簇
- `xj_grassland_horse_riding_light`
- `xj_burqin_route_rest_supply`
- `xj_urumqi_arrival_departure_assembly`
- `xj_hemu_kanas_winter_snowmode`

---

## 不单独建簇但应在主簇 notes / attach 中体现的内容
- 路边简餐、抓饭、拌面、补油、补水、轮胎检查
- 高海拔 / 雪墙 / 风口路段的停车与拍照安全提示
- 湖边临时天气变化、临时交通管制
- 赛里木湖 / 伊昭公路 / 独库北段的实时开放信息检查
- 草原轻徒步与骑马的现场匹配，不必全做成独立簇

---

## 线路运营说明（非常重要）

### 1. 这是“路线圈”，不是“高密度城市圈”
这条圈层的核心价值来自：
- 景观公路
- 高山湖泊
- 草原河谷
- 日落星空
- 村落过夜
- 季节窗口

因此排程时要优先考虑：
- 单日驾驶时长
- 出发时间
- 车辆类型与限行
- 天气 / 封路
- 住宿是否必须前置锁定

### 2. 独库北段是典型季节性公路
独库公路通常只在每年夏秋短窗口开放，且可能出现阶段性限行、夜间封闭或因天气临时交通管制。它应被当作“条件成立才上主线”的公路型主簇，而不是全年默认可走。

### 3. 伊昭公路更强依赖条件
伊昭公路除了季节性开放，还常伴随：
- 夜间禁行
- 车型限制
- 雨雪雾天气临时封控
- 山区施工或绕行

因此它应被视为“条件性 upgrade cluster”，而不是默认主链。

### 4. 喀纳斯 / 禾木属于扩展北线
若加入喀纳斯和禾木，整个圈层就不再是“纯伊犁赛湖线”，而是升级为更长的北疆大环线。它会显著增加：
- 行驶距离
- 最少晚数
- 住宿压力
- 秋季资源抢占强度

### 5. 冬季不应默认按夏秋玩法理解
冬季北疆有两种情况：
- 伊犁与高山公路：很多路段会因积雪、结冰、封控而不可照常通行
- 阿勒泰 / 禾木：反而可切换成独立冰雪线路

所以冬季并不是“整圈关闭”，而是“线路逻辑彻底改变”。

---

## 来源口径（文件级）
- 新疆文旅厅：赛里木湖、那拉提、喀拉峻、喀纳斯等 5A 景区资料
- 伊犁州政府 / 伊犁文旅：六星街、喀赞其、花期手册、伊昭公路通行信息
- 新疆交通运输厅 / 新疆文旅交通栏目：独库公路、伊昭公路的通车与封控信息
- UNESCO：Xinjiang Tianshan（喀拉峻-库尔德宁作为组成部分）
- 喀纳斯景区管理委员会：喀纳斯 / 禾木景区与冬季活动资料
