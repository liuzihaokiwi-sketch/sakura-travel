# `kansai_classic_circle` 活动簇补全（二审版）

> 已排除你给出的 existing clusters。
> 兼容映射：`Himeji -> city_code: kobe`，`Koyasan -> city_code: osaka`。
> 除特别说明外：`circle_id = "kansai_classic_circle"`，`default_selected = false`。

---

## 新增主活动簇 / Anchor

### `kyo_kurama_kibune_kawadoko`

* `city_code`: `kyoto`
* `name_zh`: `京都·鞍马贵船川床纳凉线`
* `name_en`: `Kyoto Kurama-Kibune Kawadoko Escape`
* `level`: `A`
* `default_duration`: `full_day`
* `primary_corridor`: `kyo_rakuhoku`
* `seasonality`: `["summer","autumn"]`
* `profile_fit`: `["couple","foodie","photo","nature"]`
* `trip_role`: `anchor`
* `time_window_strength`: `strong`
* `reservation_pressure`: `high`
* `secondary_attach_capacity`: `2`
* `notes`: 贵船/鞍马本身就是京都北侧独立半天到一天线路，夏季"川床/川床料理"是强时间窗卖点，也会真实影响晚餐预约和是否把北山线单独排一天。
* `experience_family`: `mountain`
* `rhythm_role`: `contrast`
* `energy_level`: `medium`

### `kyo_sagano_torokko_hozugawa`

* `city_code`: `kyoto`
* `name_zh`: `京都·嵯峨野小火车保津川下り线`
* `name_en`: `Kyoto Sagano Railway & Hozugawa Boat Combo`
* `level`: `A`
* `default_duration`: `full_day`
* `primary_corridor`: `kyo_sagano_kameoka`
* `seasonality`: `["all_year","sakura","autumn_leaves"]`
* `profile_fit`: `["couple","family","photo"]`
* `trip_role`: `anchor`
* `time_window_strength`: `strong`
* `reservation_pressure`: `high`
* `secondary_attach_capacity`: `1`
* `notes`: 嵯峨野观光小火车与 16 公里保津川下り天然构成一整天动线，且小火车为全车指定席、旺季售罄风险高，明显属于需要前置锁位的主活动簇。
* `experience_family`: `mountain`
* `rhythm_role`: `peak`
* `energy_level`: `medium`

### `kyo_ohara_sanzenin_retreat`

* `city_code`: `kyoto`
* `name_zh`: `京都·大原三千院静修线`
* `name_en`: `Kyoto Ohara Sanzen-in Retreat`
* `level`: `A`
* `default_duration`: `half_day`
* `primary_corridor`: `kyo_ohara`
* `seasonality`: `["all_year","summer","autumn_leaves"]`
* `profile_fit`: `["couple","culture","photo","slow_travel"]`
* `trip_role`: `anchor`
* `time_window_strength`: `medium`
* `reservation_pressure`: `low`
* `secondary_attach_capacity`: `2`
* `notes`: 大原是京都北侧独立山间走法，三千院是主核，周边还能自然挂接寂光院、宝泉院；它不是"顺路补点"，而是单独半天到一天都成立的静修簇。
* `experience_family`: `shrine`
* `rhythm_role`: `contrast`
* `energy_level`: `medium`

### `kyo_takao_jingoji_autumn`

* `city_code`: `kyoto`
* `name_zh`: `京都·高雄神护寺红叶线`
* `name_en`: `Kyoto Takao Jingo-ji Autumn Line`
* `level`: `A`
* `default_duration`: `half_day`
* `primary_corridor`: `kyo_takao`
* `seasonality`: `["autumn_leaves"]`
* `profile_fit`: `["photo","nature","culture"]`
* `trip_role`: `anchor`
* `time_window_strength`: `strong`
* `reservation_pressure`: `low`
* `secondary_attach_capacity`: `2`
* `notes`: 高雄被京都官方明确列为著名红叶区，且是与市中心完全不同的山地走法；到了红叶窗口，它会直接改写京都秋季排程。
* `experience_family`: `flower`
* `rhythm_role`: `peak`
* `energy_level`: `medium`

### `kyo_machiya_kaiseki_luxury`

* `city_code`: `kyoto`
* `name_zh`: `京都·町家宿怀石奢华体验线`
* `name_en`: `Kyoto Machiya Stay & Kaiseki Luxury Line`
* `level`: `A`
* `default_duration`: `half_day`
* `primary_corridor`: `kyo_central_gion`
* `seasonality`: `["all_year"]`
* `profile_fit`: `["couple","luxury","foodie"]`
* `trip_role`: `anchor`
* `time_window_strength`: `strong`
* `reservation_pressure`: `high`
* `secondary_attach_capacity`: `2`
* `notes`: 对高预算画像，京都町家住宿与怀石晚餐本身就是"来京都的理由"，会直接决定住点、晚间留白和用餐时段，不应被拆成普通餐厅补点。
* `experience_family`: `food`
* `rhythm_role`: `recovery`
* `energy_level`: `low`

### `kyo_kyoto_sakura_circuit`

* `city_code`: `kyoto`
* `name_zh`: `京都·樱花季城市总线`
* `name_en`: `Kyoto Sakura Season Circuit`
* `level`: `S`
* `default_duration`: `full_day`
* `primary_corridor`: `kyo_sakura_core`
* `seasonality`: `["sakura"]`
* `profile_fit`: `["couple","photo","first_timer"]`
* `trip_role`: `anchor`
* `time_window_strength`: `strong`
* `reservation_pressure`: `medium`
* `secondary_attach_capacity`: `2`
* `notes`: 京都官方长期单独维护樱花专题和樱花日历，且夜樱/特别开放会直接影响清晨与夜间排程，是标准的全城级季节主簇。
* `experience_family`: `flower`
* `rhythm_role`: `peak`
* `energy_level`: `high`

### `kyo_kyoto_autumn_leaves_circuit`

* `city_code`: `kyoto`
* `name_zh`: `京都·红叶季城市总线`
* `name_en`: `Kyoto Autumn Leaves Circuit`
* `level`: `S`
* `default_duration`: `full_day`
* `primary_corridor`: `kyo_autumn_core`
* `seasonality`: `["autumn_leaves"]`
* `profile_fit`: `["couple","photo","first_timer"]`
* `trip_role`: `anchor`
* `time_window_strength`: `strong`
* `reservation_pressure`: `medium`
* `secondary_attach_capacity`: `2`
* `notes`: 京都官方同样长期提供红叶日历，并明确存在夜间点灯和特别开放；这类秋季窗口会直接影响住东山、岚山还是北山。
* `experience_family`: `flower`
* `rhythm_role`: `peak`
* `energy_level`: `high`

### `kyo_gion_matsuri_festival`

* `city_code`: `kyoto`
* `name_zh`: `京都·祇园祭山鉾巡行线`
* `name_en`: `Kyoto Gion Matsuri Festival Line`
* `level`: `S`
* `default_duration`: `full_day`
* `primary_corridor`: `kyo_gion_shijo_karasuma`
* `seasonality`: `["summer"]`
* `profile_fit`: `["festival","culture","first_timer","photo"]`
* `trip_role`: `anchor`
* `time_window_strength`: `strong`
* `reservation_pressure`: `high`
* `secondary_attach_capacity`: `1`
* `notes`: 祇园祭是京都最强的夏季全城节庆之一，官方明确其为 7 月整月举行、含山鉾巡行与宵山体系；这会直接影响酒店、交通和观演窗口。
* `experience_family`: `shrine`
* `rhythm_role`: `peak`
* `energy_level`: `high`

### `uji_byodoin_tea_heritage`

* `city_code`: `uji`
* `name_zh`: `宇治·平等院抹茶文化线`
* `name_en`: `Uji Byodoin & Tea Heritage Line`
* `level`: `A`
* `default_duration`: `half_day`
* `primary_corridor`: `uji_byodoin_omotesando`
* `seasonality`: `["all_year"]`
* `profile_fit`: `["foodie","culture","couple","photo"]`
* `trip_role`: `anchor`
* `time_window_strength`: `medium`
* `reservation_pressure`: `low`
* `secondary_attach_capacity`: `2`
* `notes`: Uji不应只被笼统并入"京都日归"；平等院世界遗产 + 茶房体验 + 茶点街区本身就是独立半天主簇。
* `experience_family`: `shrine`
* `rhythm_role`: `contrast`
* `energy_level`: `medium`

### `osa_koyasan_shukubo_pilgrimage`

* `city_code`: `osaka`
* `name_zh`: `大阪出发·高野山宿坊朝勤线`
* `name_en`: `Osaka Gateway to Koyasan Shukubo Pilgrimage`
* `level`: `A`
* `default_duration`: `full_day`
* `primary_corridor`: `wakayama_koyasan`
* `seasonality`: `["all_year","autumn_leaves"]`
* `profile_fit`: `["culture","slow_travel","couple"]`
* `trip_role`: `anchor`
* `time_window_strength`: `strong`
* `reservation_pressure`: `high`
* `secondary_attach_capacity`: `1`
* `notes`: 高野山完整体验核心不是"打卡寺庙"，而是宿坊过夜、精进料理与晨课，官方也明确过夜才是完整体验，因此它会直接影响跨区路线和晚数。
* `experience_family`: `shrine`
* `rhythm_role`: `peak`
* `energy_level`: `medium`

### `nara_yoshino_sakura_mountain`

* `city_code`: `nara`
* `name_zh`: `奈良·吉野山樱花线`
* `name_en`: `Nara Mt. Yoshino Sakura Line`
* `level`: `S`
* `default_duration`: `full_day`
* `primary_corridor`: `nara_yoshino`
* `seasonality`: `["sakura"]`
* `profile_fit`: `["photo","couple","nature"]`
* `trip_role`: `anchor`
* `time_window_strength`: `strong`
* `reservation_pressure`: `high`
* `secondary_attach_capacity`: `1`
* `notes`: 吉野山是奈良最强季节型主簇之一，官方明确约 3 万株樱花、夜樱点灯和建议留宿，这完全满足独立成行的一整天甚至一晚线路。
* `experience_family`: `flower`
* `rhythm_role`: `peak`
* `energy_level`: `high`

### `nara_yoshino_autumn_koyo`

* `city_code`: `nara`
* `name_zh`: `奈良·吉野山红叶展望线`
* `name_en`: `Nara Mt. Yoshino Autumn Foliage Line`
* `level`: `A`
* `default_duration`: `full_day`
* `primary_corridor`: `nara_yoshino`
* `seasonality`: `["autumn_leaves"]`
* `profile_fit`: `["photo","nature","slow_travel"]`
* `trip_role`: `anchor`
* `time_window_strength`: `medium`
* `reservation_pressure`: `low`
* `secondary_attach_capacity`: `1`
* `notes`: 吉野并非只有春樱，奈良官方也把其列为红叶与展望的重要区域，适合单独南下排一整天。
* `experience_family`: `flower`
* `rhythm_role`: `contrast`
* `energy_level`: `high`

### `nara_horyuji_ikaruga_worldheritage`

* `city_code`: `nara`
* `name_zh`: `奈良·法隆寺斑鸠世界遗产线`
* `name_en`: `Nara Horyuji-Ikaruga World Heritage Line`
* `level`: `A`
* `default_duration`: `half_day`
* `primary_corridor`: `nara_ikaruga`
* `seasonality`: `["all_year"]`
* `profile_fit`: `["history","culture","first_timer"]`
* `trip_role`: `anchor`
* `time_window_strength`: `medium`
* `reservation_pressure`: `low`
* `secondary_attach_capacity`: `1`
* `notes`: 法隆寺是奈良另一组非常强的世界遗产簇，离奈良公园主区有明显空间分离，适合作为单独半天到一天的文化线。
* `experience_family`: `shrine`
* `rhythm_role`: `contrast`
* `energy_level`: `medium`

### `nara_todaiji_naramachi_core`

* `city_code`: `nara`
* `name_zh`: `奈良·东大寺奈良町核心线`
* `name_en`: `Nara Todaiji & Naramachi Core Line`
* `level`: `A`
* `default_duration`: `full_day`
* `primary_corridor`: `nara_park_naramachi`
* `seasonality`: `["all_year"]`
* `profile_fit`: `["first_timer","culture","family","photo"]`
* `trip_role`: `anchor`
* `time_window_strength`: `medium`
* `reservation_pressure`: `low`
* `secondary_attach_capacity`: `2`
* `notes`: 东大寺与奈良公园是奈良最强核心，但奈良町提供完全不同的旧城补充，因此"东大寺/鹿/奈良町"应作为独立核心线存在，而不只算 `nara_deep_kasuga_kofuku` 的附属。
* `experience_family`: `shrine`
* `rhythm_role`: `peak`
* `energy_level`: `high`

### `kobe_himeji_castle_kokoen_daytrip`

* `city_code`: `kobe`
* `name_zh`: `兵库西·姬路城好古园世界遗产日归`
* `name_en`: `Hyogo West Himeji Castle & Kokoen Day Trip`
* `level`: `A`
* `default_duration`: `full_day`
* `primary_corridor`: `hyogo_himeji_harima`
* `seasonality`: `["all_year"]`
* `profile_fit`: `["history","photo","first_timer"]`
* `trip_role`: `anchor`
* `time_window_strength`: `medium`
* `reservation_pressure`: `low`
* `secondary_attach_capacity`: `1`
* `notes`: 姬路城是 UNESCO 世界遗产，也是日本最重要的现存城郭之一；和好古园天然组成完整日归线，足以改变关西住宿与跨区路线。
* `experience_family`: `shrine`
* `rhythm_role`: `peak`
* `energy_level`: `high`

### `kobe_rokko_arima_nightview_escape`

* `city_code`: `kobe`
* `name_zh`: `神户·六甲山有马夜景温泉线`
* `name_en`: `Kobe Rokko-Arima Night View Escape`
* `level`: `A`
* `default_duration`: `full_day`
* `primary_corridor`: `hyogo_rokko_arima`
* `seasonality`: `["all_year","summer","autumn_leaves","winter"]`
* `profile_fit`: `["couple","photo","slow_travel"]`
* `trip_role`: `anchor`
* `time_window_strength`: `strong`
* `reservation_pressure`: `medium`
* `secondary_attach_capacity`: `2`
* `notes`: 六甲山夜景、缆车/索道与有马温泉是官方成熟联动产品，且夜景价值高度依赖日落后时段，明显会影响是否在神户/有马留宿。
* `experience_family`: `onsen`
* `rhythm_role`: `recovery`
* `energy_level`: `medium`

### `kobe_nadagogo_sake_breweries`

* `city_code`: `kobe`
* `name_zh`: `神户·滩五乡酒藏巡游线`
* `name_en`: `Kobe Nada Gogo Sake Breweries Line`
* `level`: `A`
* `default_duration`: `half_day`
* `primary_corridor`: `hyogo_nada_higashinada`
* `seasonality`: `["all_year"]`
* `profile_fit`: `["foodie","culture","couple"]`
* `trip_role`: `anchor`
* `time_window_strength`: `medium`
* `reservation_pressure`: `low`
* `secondary_attach_capacity`: `2`
* `notes`: 滩五乡是日本顶级清酒产区，官方直接给出一日巡游方案；对酒造/发酵文化画像，它足以独立成半天到一天主题线。
* `experience_family`: `food`
* `rhythm_role`: `contrast`
* `energy_level`: `medium`

### `kobe_nunobiki_ropeway_herbgarden`

* `city_code`: `kobe`
* `name_zh`: `神户·布引香草园索道线`
* `name_en`: `Kobe Nunobiki Ropeway & Herb Garden`
* `level`: `A`
* `default_duration`: `half_day`
* `primary_corridor`: `kobe_shinkobe_nunobiki`
* `seasonality`: `["all_year","spring","autumn","winter"]`
* `profile_fit`: `["couple","photo","family"]`
* `trip_role`: `anchor`
* `time_window_strength`: `medium`
* `reservation_pressure`: `low`
* `secondary_attach_capacity`: `2`
* `notes`: 布引索道 + 香草园不是普通小景点，官方明确其为市区近郊度假型高地景观区，还能自然挂接布引瀑布或北野。
* `experience_family`: `mountain`
* `rhythm_role`: `contrast`
* `energy_level`: `medium`

### `kobe_luminarie_winter`

* `city_code`: `kobe`
* `name_zh`: `神户·Luminarie 冬季灯光线`
* `name_en`: `Kobe Luminarie Winter Illumination`
* `level`: `A`
* `default_duration`: `quarter_day`
* `primary_corridor`: `kobe_sannomiya_meriken_winter`
* `seasonality`: `["winter"]`
* `profile_fit`: `["couple","photo","festival"]`
* `trip_role`: `anchor`
* `time_window_strength`: `strong`
* `reservation_pressure`: `high`
* `secondary_attach_capacity`: `1`
* `notes`: Kobe Luminarie 是神户最强冬季限定事件之一，年年固定冬季窗口，官方也把它作为冬季主吸引物；会真实影响冬季酒店与晚间路线。
* `experience_family`: `citynight`
* `rhythm_role`: `peak`
* `energy_level`: `low`

### `arima_onsen_overnight_ryokan`

* `city_code`: `arima_onsen`
* `name_zh`: `有马温泉·一泊二食旅馆线`
* `name_en`: `Arima Onsen Overnight Ryokan Stay`
* `level`: `A`
* `default_duration`: `full_day`
* `primary_corridor`: `arima_onsen_core`
* `seasonality`: `["all_year","autumn_leaves","winter"]`
* `profile_fit`: `["couple","luxury","slow_travel"]`
* `trip_role`: `anchor`
* `time_window_strength`: `strong`
* `reservation_pressure`: `high`
* `secondary_attach_capacity`: `1`
* `notes`: 已有 `arima_onsen_day_trip`，但真正应单独建簇的是过夜型旅馆体验；官方明确有马以古老温泉、ryokan 与会席料理为核心卖点。
* `experience_family`: `onsen`
* `rhythm_role`: `recovery`
* `energy_level`: `low`

---

## 新增强次级簇 / Enrichment

### `kyo_gion_pontocho_nightwalk`

* `city_code`: `kyoto`
* `name_zh`: `京都·祇园夜走先斗町线`
* `name_en`: `Kyoto Gion & Pontocho Night Walk`
* `level`: `B`
* `default_duration`: `quarter_day`
* `primary_corridor`: `kyo_gion_pontocho`
* `seasonality`: `["all_year","summer"]`
* `profile_fit`: `["couple","photo","culture"]`
* `trip_role`: `enrichment`
* `time_window_strength`: `strong`
* `reservation_pressure`: `medium`
* `secondary_attach_capacity`: `2`
* `notes`: 祇园/先斗町的价值明显集中在傍晚到夜间，且夜间步行、餐厅与鸭川纳凉床会自然连成一组。
* `experience_family`: `citynight`
* `rhythm_role`: `contrast`
* `energy_level`: `low`

### `kyo_matcha_wagashi_crawl`

* `city_code`: `kyoto`
* `name_zh`: `京都·抹茶和果子甜品线`
* `name_en`: `Kyoto Matcha & Wagashi Crawl`
* `level`: `B`
* `default_duration`: `half_day`
* `primary_corridor`: `kyo_central_teahouse`
* `seasonality`: `["all_year"]`
* `profile_fit`: `["foodie","photo","couple"]`
* `trip_role`: `enrichment`
* `time_window_strength`: `medium`
* `reservation_pressure`: `low`
* `secondary_attach_capacity`: `2`
* `notes`: 京都和果子与抹茶是成熟主题，不只是"顺路吃甜品"；对甜品/茶文化画像，半天主题线成立。
* `experience_family`: `food`
* `rhythm_role`: `utility`
* `energy_level`: `low`

### `kyo_miyako_odori_spring`

* `city_code`: `kyoto`
* `name_zh`: `京都·都踊春季歌舞线`
* `name_en`: `Kyoto Miyako Odori Spring Performance`
* `level`: `A`
* `default_duration`: `quarter_day`
* `primary_corridor`: `kyo_gion_kaburenjo`
* `seasonality`: `["sakura"]`
* `profile_fit`: `["culture","couple","luxury"]`
* `trip_role`: `enrichment`
* `time_window_strength`: `strong`
* `reservation_pressure`: `high`
* `secondary_attach_capacity`: `2`
* `notes`: 都踊是 4 月整月、固定场次的祇园歌舞公演，时间窗和订位属性都非常强，适合作为京都春季文化型强次级簇。
* `experience_family`: `shrine`
* `rhythm_role`: `contrast`
* `energy_level`: `low`

### `kyo_gozan_okuribi_night`

* `city_code`: `kyoto`
* `name_zh`: `京都·五山送火夜观线`
* `name_en`: `Kyoto Gozan Okuribi Night`
* `level`: `A`
* `default_duration`: `quarter_day`
* `primary_corridor`: `kyo_citywide_okuribi_view`
* `seasonality`: `["summer"]`
* `profile_fit`: `["culture","photo","festival"]`
* `trip_role`: `enrichment`
* `time_window_strength`: `strong`
* `reservation_pressure`: `medium`
* `secondary_attach_capacity`: `1`
* `notes`: 五山送火是 8 月 16 日晚固定举行的京都代表性宗教仪式，窗口极窄、城市级影响很强，适合单独建成一夜型节庆簇。
* `experience_family`: `shrine`
* `rhythm_role`: `peak`
* `energy_level`: `low`

### `osa_umeda_stationcity_shopping`

* `city_code`: `osaka`
* `name_zh`: `大阪·梅田站城购物线`
* `name_en`: `Osaka Umeda Station City Shopping Line`
* `level`: `A`
* `default_duration`: `half_day`
* `primary_corridor`: `osa_kita_umeda`
* `seasonality`: `["all_year"]`
* `profile_fit`: `["shopping","family","luxury"]`
* `trip_role`: `enrichment`
* `time_window_strength`: `weak`
* `reservation_pressure`: `low`
* `secondary_attach_capacity`: `2`
* `notes`: 梅田不是单一商场，而是站城级购物簇；官方把 Osaka Station City、Grand Front、Whity、Diamor、Umeda Sky 等放在同一大型商业区内，足以吃掉半天到一天。
* `experience_family`: `locallife`
* `rhythm_role`: `utility`
* `energy_level`: `low`

### `osa_shinsaibashi_midosuji_shopping`

* `city_code`: `osaka`
* `name_zh`: `大阪·心斋桥御堂筋购物线`
* `name_en`: `Osaka Shinsaibashi & Midosuji Shopping Line`
* `level`: `B`
* `default_duration`: `half_day`
* `primary_corridor`: `osa_minami_shinsaibashi`
* `seasonality`: `["all_year"]`
* `profile_fit`: `["shopping","couple","luxury"]`
* `trip_role`: `enrichment`
* `time_window_strength`: `weak`
* `reservation_pressure`: `none`
* `secondary_attach_capacity`: `2`
* `notes`: 心斋桥筋 600 米商店街 + 御堂筋奢牌街已足够形成完整购物动线，对购物画像会影响住在 Minami 还是 Kita。
* `experience_family`: `locallife`
* `rhythm_role`: `utility`
* `energy_level`: `low`

### `osa_osaka_nightview_observatories`

* `city_code`: `osaka`
* `name_zh`: `大阪·城市夜景展望台线`
* `name_en`: `Osaka Skyline Night View Line`
* `level`: `B`
* `default_duration`: `quarter_day`
* `primary_corridor`: `osa_city_observatories`
* `seasonality`: `["all_year"]`
* `profile_fit`: `["couple","photo","first_timer"]`
* `trip_role`: `enrichment`
* `time_window_strength`: `strong`
* `reservation_pressure`: `low`
* `secondary_attach_capacity`: `1`
* `notes`: Umeda Sky、Harukas 300 等大阪高层展望设施都明显依赖日落到夜间窗口，适合当作单独晚间主活动，而不是白天顺手经过。
* `experience_family`: `citynight`
* `rhythm_role`: `contrast`
* `energy_level`: `low`

### `osa_tenjin_matsuri_river_fireworks`

* `city_code`: `osaka`
* `name_zh`: `大阪·天神祭船渡御烟花线`
* `name_en`: `Osaka Tenjin Matsuri River Procession`
* `level`: `S`
* `default_duration`: `full_day`
* `primary_corridor`: `osa_tenmangu_okawa`
* `seasonality`: `["summer"]`
* `profile_fit`: `["festival","photo","first_timer"]`
* `trip_role`: `anchor`
* `time_window_strength`: `strong`
* `reservation_pressure`: `high`
* `secondary_attach_capacity`: `1`
* `notes`: 天神祭固定于每年 7 月 24–25 日，白天陆渡御、夜间船渡御与烟花形成完整一日节庆线，是大阪最强季节主簇之一。
* `experience_family`: `shrine`
* `rhythm_role`: `peak`
* `energy_level`: `high`

### `osa_midosuji_illumination_winter`

* `city_code`: `osaka`
* `name_zh`: `大阪·御堂筋灯饰冬季线`
* `name_en`: `Osaka Midosuji Illumination Winter Line`
* `level`: `B`
* `default_duration`: `quarter_day`
* `primary_corridor`: `osa_midosuji_winter`
* `seasonality`: `["winter"]`
* `profile_fit`: `["couple","photo","festival"]`
* `trip_role`: `enrichment`
* `time_window_strength`: `strong`
* `reservation_pressure`: `none`
* `secondary_attach_capacity`: `2`
* `notes`: 大阪官方将 Midosuji Illuminations 作为冬季灯光节主项目之一，且通常横跨 Umeda 到 Namba 的长轴线，适合建成冬季夜游簇。
* `experience_family`: `citynight`
* `rhythm_role`: `contrast`
* `energy_level`: `low`

### `kobe_bayarea_harbor_nightview`

* `city_code`: `kobe`
* `name_zh`: `神户·海港湾区夜景线`
* `name_en`: `Kobe Bay Area Harbor Night View`
* `level`: `B`
* `default_duration`: `quarter_day`
* `primary_corridor`: `kobe_harbor_meriken`
* `seasonality`: `["all_year"]`
* `profile_fit`: `["couple","photo","first_timer"]`
* `trip_role`: `enrichment`
* `time_window_strength`: `strong`
* `reservation_pressure`: `none`
* `secondary_attach_capacity`: `2`
* `notes`: Harborland、Meriken Park、Port Tower 等官方同属湾区夜景带，典型傍晚后价值更高，适合与神户牛晚餐或湾区住宿连排。
* `experience_family`: `sea`
* `rhythm_role`: `contrast`
* `energy_level`: `low`

---

## 本轮二审结论

### 应新增入库的强主簇

* `kyo_kurama_kibune_kawadoko`
* `kyo_sagano_torokko_hozugawa`
* `kyo_ohara_sanzenin_retreat`
* `kyo_takao_jingoji_autumn`
* `kyo_machiya_kaiseki_luxury`
* `kyo_kyoto_sakura_circuit`
* `kyo_kyoto_autumn_leaves_circuit`
* `kyo_gion_matsuri_festival`
* `uji_byodoin_tea_heritage`
* `osa_koyasan_shukubo_pilgrimage`
* `nara_yoshino_sakura_mountain`
* `nara_yoshino_autumn_koyo`
* `nara_horyuji_ikaruga_worldheritage`
* `nara_todaiji_naramachi_core`
* `kobe_himeji_castle_kokoen_daytrip`
* `kobe_rokko_arima_nightview_escape`
* `kobe_nadagogo_sake_breweries`
* `kobe_nunobiki_ropeway_herbgarden`
* `kobe_luminarie_winter`
* `arima_onsen_overnight_ryokan`

### 应补入的强次级簇

* `kyo_gion_pontocho_nightwalk`
* `kyo_matcha_wagashi_crawl`
* `kyo_miyako_odori_spring`
* `kyo_gozan_okuribi_night`
* `osa_umeda_stationcity_shopping`
* `osa_shinsaibashi_midosuji_shopping`
* `osa_osaka_nightview_observatories`
* `osa_midosuji_illumination_winter`
* `kobe_bayarea_harbor_nightview`

### 不再重复补入

* 你列出的 existing clusters 本轮全部视为已存在，不重复建簇。
