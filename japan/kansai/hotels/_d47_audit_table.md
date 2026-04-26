# D47 现池 203 家 audit table

自动 dump·124 家有 flag·待 Step 4 逐家迭代修改


## 各 flag 计数

- **PLACEHOLDER_ID**（占位 id h***）：0
- **CLICHE**（套话简介）：0
- **EMPTY_URL**（数据来源仅 hotels.ctrip.com/ 占位）：120
- **DEPTH_FULL_INCOMPLETE**（depth=full 但 note 缺必填）：0
- **TIER_MISMATCH**（迁移前 tier 跟 D47 阈值不符）：4

## flag 明细（按 city 分组）

### 京都（42 家）

| id | 店名 | tier | depth | 平季中位 | flags |
|---|---|---|---|---|---|
| `kyo_shijo_kawaramachi_hotel_okura_kyoto` | 京都大仓酒店（Hotel Okura Kyoto） | b3(品质) | skeleton | 1100 | EMPTY_URL |
| `kyo_shijo_kawaramachi_good_nature_hotel` | Good Nature Hotel（Good Nature Hotel） | b4(高端) | skeleton | 1900 | EMPTY_URL |
| `kyo_shijo_kawaramachi_cross_hotel_kyoto` | Cross Hotel Kyoto（Cross Hotel Kyoto） | b3(品质) | skeleton | 1100 | EMPTY_URL |
| `kyo_gion_higashiyama_genji_kyoto` | Genji Kyoto（Genji Kyoto） | b4(高端) | skeleton | 1900 | EMPTY_URL |
| `kyo_gion_higashiyama_hotel` | Hotel 侑楽 京八坂（Hotel 侑楽 京八坂） | b4(高端) | skeleton | 1900 | EMPTY_URL |
| `kyo_nijo_central_bu_lai_dun_hotel` | 京都布莱顿酒店（京都ブライトンホテル） | b3(品质) | skeleton | 1100 | EMPTY_URL |
| `kyo_kyoto_station_doubletree_by_hilton_kyoto_sta` | DoubleTree by Hilton 京都站（DoubleTree by H | b3(品质) | skeleton | 1100 | EMPTY_URL |
| `kyo_shijo_kawaramachi_shijo_xin_ting_ying_te_gai_te_hotel` | 京都四条新町英特盖特酒店（ホテルインターゲート京都四条新町） | b3(品质) | skeleton | 1100 | EMPTY_URL |
| `kyo_gion_higashiyama_nohga_hotel` | NOHGA HOTEL 京都清水（NOHGA HOTEL 京都清水） | b4(高端) | skeleton | 1900 | EMPTY_URL |
| `kyo_kyoto_station_tune_stay_kyoto` | TUNE STAY KYOTO（TUNE STAY KYOTO） | b4(高端) | skeleton | 1900 | EMPTY_URL |
| `kyo_shijo_kawaramachi_insomnia_kyoto_oike` | insomnia KYOTO OIKE（insomnia KYOTO OIKE） | b4(高端) | skeleton | 1900 | EMPTY_URL |
| `kyo_shijo_kawaramachi_xian_dou_ting_espacion_hotel` | 先斗町依斯柏席昂酒店（ホテルエスパシオン先斗町） | b4(高端) | skeleton | 1900 | EMPTY_URL |
| `kyo_shijo_kawaramachi_gojo_holiday_inn_hotel` | 京都五条假日酒店（ホリデイ・イン京都五条） | b3(品质) | skeleton | 1100 | EMPTY_URL |
| `kyo_gion_higashiyama_sowaka` | SOWAKA（SOWAKA） | b4(高端) | skeleton | 1900 | EMPTY_URL |
| `kyo_kita_takagamine_shou_huo_hotel` | 京都鹰峰收获酒店（ホテルハーヴェスト京都鷹峯） | b4(高端) | skeleton | 1200 | EMPTY_URL |
| `kyo_gion_higashiyama_doubletree_by_hilton_kyoto_hig` | DoubleTree by Hilton 京都东山（DoubleTree by  | b3(品质) | skeleton | 1100 | EMPTY_URL |
| `kyo_kyoto_station_sakura_terrace_the_gallery` | 樱花台画廊饭店（櫻花台畫廊飯店 (Sakura Terrace The Gall | b4(高端) | skeleton | 1900 | EMPTY_URL |
| `kyo_shijo_kawaramachi_sequence` | sequence饭店-京都五条（sequence飯店-京都五条） | b4(高端) | skeleton | 1900 | EMPTY_URL |
| `kyo_gion_higashiyama_granbell_hotel` | 京都格兰贝尔酒店（京都グランベルホテル） | b4(高端) | skeleton | 1900 | EMPTY_URL |
| `kyo_kyoto_station_keihan_jing_dou_hotel` | 京阪京都大饭店（ホテル京阪京都グランデ） | b3(品质) | skeleton | 1100 | EMPTY_URL |
| `kyo_shijo_kawaramachi_gate_hotel_jing_dou_gao_lai_chuan` | 门酒店京都高濑川（ザ・ゲートホテル京都高瀬川） | b4(高端) | skeleton | 1900 | EMPTY_URL |
| `kyo_shijo_kawaramachi_rojiyu_kyoto` | ROJIYU KYOTO（ROJIYU KYOTO） | b4(高端) | skeleton | 1900 | EMPTY_URL |
| `kyo_shijo_kawaramachi_yuraku_etsuen` | 京都悠洛悦苑（京都悠洛悦苑） | b4(高端) | skeleton | 1900 | EMPTY_URL |
| `kyo_shijo_kawaramachi_shijo_kawaramachi_wen_quan_kong_ting_lu_tai_jing_dou` | 四条河原町温泉 空庭テラス京都（Sora Niwa Terrace Kyoto） | b4(高端) | full | 1100 | TIER_MISMATCH(exp=b3) |
| `kyo_shijo_kawaramachi_shijo_kawaramachi_wen_quan_kong_ting_lu_tai_jing_dou_bettei` | 四条河原町温泉 空庭テラス京都 別邸（Soraniwa Terrace Kyot | b5(奢华) | full | 1900 | TIER_MISMATCH(exp=b4) |
| `kyo_gion_higashiyama_the_shinmonzen` | The Shinmonzen（The Shinmonzen） | b4(高端) | skeleton | 1900 | EMPTY_URL |
| `kyo_gion_higashiyama_hotel_seiryu_kyoto_kiyomizu` | 京都清水圣龙酒店（Hotel Seiryu Kyoto Kiyomizu） | b4(高端) | skeleton | 1900 | EMPTY_URL |
| `kyo_arashiyama_muni_kyoto_by_onko_chishin` | MUNI KYOTO by Onko Chishin（MUNI KYOTO by | b4(高端) | skeleton | 1900 | EMPTY_URL |
| `kyo_nijo_central_garrya_nijo_castle_kyoto` | 京都二条城嘉瑞亚（Garrya Nijo Castle Kyoto） | b4(高端) | skeleton | 1900 | EMPTY_URL |
| `kyo_shijo_kawaramachi_candeohotels` | Candeo Hotels 京都乌丸六角（カンデオホテルズ京都烏丸六角） | b3(品质) | skeleton | 1100 | EMPTY_URL |
| `kyo_shijo_kawaramachi_ting_jia_zhu_zhai_jing_dou` | 町家住宅京都（町家レジデンスイン京都） | b2(舒适) | skeleton | 750 | EMPTY_URL |
| `kyo_shijo_kawaramachi_kuraya` | 藏屋（藏や (Kuraya)） | b2(舒适) | skeleton | 750 | EMPTY_URL |
| `kyo_gion_higashiyama_gion_xin_qiao_mei_an` | 祇园新桥 梅庵（祇園新橋 梅庵） | b2(舒适) | skeleton | 750 | EMPTY_URL |
| `kyo_gion_higashiyama_jin_guang_yuan_ying_an` | 金光院 萤庵（金光院 ほたる庵） | b2(舒适) | skeleton | 550 | EMPTY_URL |
| `kyo_gion_higashiyama_ninnaji_omuro_hui_guan` | 仁和寺 御室会馆（仁和寺 御室会館） | b2(舒适) | skeleton | 550 | EMPTY_URL |
| `kyo_gion_higashiyama_chion_in_wajun_hui_guan` | 知恩院 和顺会馆（知恩院 和順会館） | b2(舒适) | skeleton | 550 | EMPTY_URL |
| `kyo_gion_higashiyama_myoshinji_dong_lin_yuan` | 妙心寺 东林院（妙心寺 東林院） | b2(舒适) | skeleton | 550 | EMPTY_URL |
| `kyo_arashiyama_rokuoin` | 鹿王院（鹿王院） | b2(舒适) | skeleton | 550 | EMPTY_URL |
| `kyo_shijo_kawaramachi_yao_shi_yuan` | 药师院（薬師院） | b2(舒适) | skeleton | 550 | EMPTY_URL |
| `kyo_takao_hong_ye_jia_honkan_takao_sanso` | もみぢ家本館 高雄山荘（Momijiya Honkan Takao Sanso） | b5(奢华) | full | 1500 | TIER_MISMATCH(exp=b4) |
| `kyo_arashiyama_liao_li_ryokan_you_yuan_tai` | 料理旅館 右源太（Kifune Ugenta） | b5(奢华) | full | 1500 | TIER_MISMATCH(exp=b4) |
| `kyo_arashiyama_grand_xi_lan_shan_hotel` | 格兰西嵐山酒店（ザ グランド ウェスト 嵐山） | b4(高端) | skeleton | 1900 | EMPTY_URL |

### 城崎（9 家）

| id | 店名 | tier | depth | 平季中位 | flags |
|---|---|---|---|---|---|
| `kns_kinosaki_onsen_xi_cun_wu_hotel_zhao_yue_ting` | 西村屋酒店招月庭（西村屋ホテル招月庭） | b5(奢华) | skeleton | 1900 | EMPTY_URL |
| `kns_kinosaki_onsen_wen_quan_xi_le` | 城崎温泉 喜乐（城崎温泉 喜楽） | b3(品质) | skeleton | 600 | EMPTY_URL |
| `kns_kinosaki_onsen_da_xi_wu_shui_xiang_yuan` | 大西屋水翔苑（大西屋水翔苑） | b3(品质) | skeleton | 600 | EMPTY_URL |
| `kns_kinosaki_onsen_xie_su_liu_zhi_wu` | 蟹宿六之屋（蟹宿むつの屋） | b3(品质) | skeleton | 600 | EMPTY_URL |
| `kns_kinosaki_onsen_shen_shan` | 深山（深山） | b3(品质) | skeleton | 600 | EMPTY_URL |
| `kns_kinosaki_onsen_xin_quan` | 新泉（新泉） | b3(品质) | skeleton | 600 | EMPTY_URL |
| `kns_kinosaki_onsen_yue_se` | 月色（月明かり） | b3(品质) | skeleton | 600 | EMPTY_URL |
| `kns_kinosaki_onsen_quan_cui` | 泉翠（泉翠） | b3(品质) | skeleton | 600 | EMPTY_URL |
| `kns_kinosaki_onsen_yan_xiang` | 艳乡（艷郷） | b3(品质) | skeleton | 600 | EMPTY_URL |

### 大阪（31 家）

| id | 店名 | tier | depth | 平季中位 | flags |
|---|---|---|---|---|---|
| `osk_namba_dotonbori_swissotel_nankai_osaka` | 大阪南海瑞士酒店（Swissotel Nankai Osaka） | b3(品质) | skeleton | 600 | EMPTY_URL |
| `osk_shinsaibashi_hotel_nikko_osaka` | 大阪日航酒店（Hotel Nikko Osaka） | b3(品质) | skeleton | 600 | EMPTY_URL |
| `osk_namba_dotonbori_hotel_new_otani_osaka` | 大阪新大谷酒店（Hotel New Otani Osaka） | b3(品质) | skeleton | 600 | EMPTY_URL |
| `osk_umeda_kita_rihga_royal_hotel_da_ban` | 丽嘉皇家大酒店大阪（リーガロイヤルホテル大阪） | b3(品质) | skeleton | 600 | EMPTY_URL |
| `osk_namba_dotonbori_cross_hotel_osaka` | Cross Hotel Osaka（Cross Hotel Osaka） | b3(品质) | skeleton | 600 | EMPTY_URL |
| `osk_bay_area_wan_wang_zi_hotel` | 大阪湾王子大酒店（グランドプリンスホテル大阪ベイ） | b5(奢华) | skeleton | 1900 | EMPTY_URL |
| `osk_umeda_kita_zentis_osaka` | Zentis Osaka（Zentis Osaka） | b5(奢华) | skeleton | 1900 | EMPTY_URL |
| `osk_shinsaibashi_candeo_hotels_osaka_shinsaibas` | Candeo Hotels 大阪心斋桥（Candeo Hotels Osaka  | b3(品质) | skeleton | 600 | EMPTY_URL |
| `osk_namba_dotonbori_hiyori` | 大阪难波Hiyori酒店（大阪なんばHiyoriホテル） | b3(品质) | skeleton | 600 | EMPTY_URL |
| `osk_shinsaibashi_the_bridge_hotel` | The Bridge Hotel 心斋桥（The Bridge Hotel 心斎 | b3(品质) | skeleton | 600 | EMPTY_URL |
| `osk_bay_area_universal_port_hotel` | 环球港口酒店（ホテル ユニバーサルポート） | b5(奢华) | skeleton | 1900 | EMPTY_URL |
| `osk_bay_area_usj` | 公园前沿酒店 USJ（ザ パーク フロント ホテル USJ） | b5(奢华) | skeleton | 1900 | EMPTY_URL |
| `osk_namba_dotonbori_monterey_ge_la_si_mi_er_hotel` | 大阪蒙特利格拉斯密尔酒店（ホテルモントレ グラスミア大阪） | b3(品质) | skeleton | 600 | EMPTY_URL |
| `osk_namba_dotonbori_here_osaka_namba` | &Here OSAKA NAMBA（&Here OSAKA NAMBA） | b5(奢华) | skeleton | 1900 | EMPTY_URL |
| `osk_tennoji_shinsekai_omo7_by` | OMO7大阪 by 星野度假村（OMO7大阪 by 星野リゾート） | b3(品质) | skeleton | 600 | EMPTY_URL |
| `osk_umeda_kita_umeda_hilton_canopy_hotel` | 大阪梅田希尔顿格芮精选酒店（キャノピーbyヒルトン大阪梅田） | b3(品质) | skeleton | 600 | EMPTY_URL |
| `osk_namba_dotonbori_namba_dong_fang_hotel` | 难波东方酒店（ナンバオリエンタルホテル） | b3(品质) | skeleton | 600 | EMPTY_URL |
| `osk_tennoji_shinsekai_kyocera_hotel` | 京瓷酒店（ホテル京セラ） | b3(品质) | skeleton | 600 | EMPTY_URL |
| `osk_honmachi_honmachi_vista_premio_hotel` | 大阪本町维斯塔尊贵酒店（ホテルビスタプレミオ大阪本町） | b3(品质) | skeleton | 600 | EMPTY_URL |
| `osk_bay_area_universal_qi_dian_hotel` | 环球影城奇点酒店（ユニバーサルスタジオ シンギュラリホテル） | b3(品质) | skeleton | 600 | EMPTY_URL |
| `osk_shinsaibashi_monterey_lei_fu_lai_er_hotel` | 大阪蒙特利勒弗莱尔酒店（ホテルモントレ ル・フレール大阪） | b3(品质) | skeleton | 600 | EMPTY_URL |
| `osk_honmachi_mitsui_garden_hotel_da_ban_dian_wu_qiao` | 三井花园酒店大阪淀屋桥（三井ガーデンホテル大阪淀屋橋） | b3(品质) | skeleton | 600 | EMPTY_URL |
| `osk_namba_dotonbori_cheng_hilton_doubletree_hotel` | 大阪城希尔顿逸林酒店（ダブルツリーbyヒルトン大阪城） | b3(品质) | skeleton | 600 | EMPTY_URL |
| `osk_umeda_kita_tones_osaka` | TONES OSAKA（TONES OSAKA） | b5(奢华) | skeleton | 1900 | EMPTY_URL |
| `osk_umeda_kita_dojima_aloft` | 大阪堂岛雅乐轩（アロフト大阪堂島） | b5(奢华) | skeleton | 1900 | EMPTY_URL |
| `osk_honmachi_the_boly_osaka` | THE BOLY OSAKA（THE BOLY OSAKA） | b5(奢华) | skeleton | 1900 | EMPTY_URL |
| `osk_honmachi_honmachi_lively_hotel` | 大阪本町莱弗利酒店（ザ・ライブリー大阪本町） | b5(奢华) | skeleton | 1900 | EMPTY_URL |
| `osk_bay_area_risonare` | 星野度假村 Risonare 大阪（星野リゾート リゾナーレ大阪） | b5(奢华) | skeleton | 1900 | EMPTY_URL |
| `osk_tennoji_shinsekai_tennoji_ta_an_da_zhi_sen` | 大阪天王寺塔安达之森（アンダの森 大阪天王寺タワー） | b5(奢华) | skeleton | 1900 | EMPTY_URL |
| `osk_honmachi_voco` | voco大阪中央（voco大阪セントラル） | b3(品质) | skeleton | 600 | EMPTY_URL |
| `osk_umeda_kita_a_er_mo_ni_an_bu_la_sai_hotel` | 大阪阿尔莫尼安布拉塞酒店（アルモニーアンブラッセ大阪） | b5(奢华) | skeleton | 1900 | EMPTY_URL |

### 奈良（4 家）

| id | 店名 | tier | depth | 平季中位 | flags |
|---|---|---|---|---|---|
| `nra_nara_park_area_zi_cui_she_hua_jing_xuan_hotel_nai_liang` | 紫翠奢华精选酒店·奈良（紫翠 ラグジュアリーコレクションホテル 奈良） | b5(奢华) | skeleton | 1600 | EMPTY_URL |
| `nra_nara_park_area_jie_dao_sai_tuo_lei` | 奈良街道塞托雷（セトレならまち） | b5(奢华) | skeleton | 1900 | EMPTY_URL |
| `nra_nara_park_area_miroku_nara_by_the_share_hotel` | MIROKU Nara by THE SHARE HOTELS（MIROKU N | b5(奢华) | skeleton | 1900 | EMPTY_URL |
| `nra_nara_park_area_jw_marriott_hotel_nara` | 奈良JW万豪酒店（JW Marriott Hotel Nara） | b5(奢华) | skeleton | 1600 | EMPTY_URL |

### 神户（28 家）

| id | 店名 | tier | depth | 平季中位 | flags |
|---|---|---|---|---|---|
| `kbe_harborland_meriken_la_suite_hai_gang_hotel` | 神户拉斯维特海港酒店（ホテル ラ・スイート神戸ハーバーランド） | b4(高端) | skeleton | 1100 | EMPTY_URL |
| `kbe_harborland_meriken_da_cang_hotel` | 神户大仓酒店（ホテルオークラ神戸） | b4(高端) | skeleton | 1100 | EMPTY_URL |
| `kbe_harborland_meriken_mei_li_jian_gong_yuan_dong_fang_hotel` | 神户美利坚公园东方酒店（神戸メリケンパークオリエンタルホテル） | b4(高端) | skeleton | 1100 | EMPTY_URL |
| `kbe_bay_area_wan_sheraton_hotel` | 神户湾喜来登大酒店（神戸ベイシェラトン） | b4(高端) | skeleton | 1100 | EMPTY_URL |
| `kbe_kitano_shinkobe_ana_crowne_plaza_kobe` | 神户全日空皇冠假日酒店（ANA Crowne Plaza Kobe） | b4(高端) | skeleton | 1100 | EMPTY_URL |
| `kbe_motomachi_nankinmach_oriental_hotel_kobe` | 神户东方大酒店（東方ホテル (Oriental Hotel Kobe)） | b4(高端) | skeleton | 1100 | EMPTY_URL |
| `kbe_harborland_meriken_hai_gang_la_suite_hotel` | 神户海港拉斯维特酒店（神戸ハーバーランドラ・スイート） | b4(高端) | skeleton | 1100 | EMPTY_URL |
| `kbe_harborland_meriken_da_cang_hotel_2` | 神户大仓大酒店（神戸大倉ホテル） | b4(高端) | skeleton | 1100 | EMPTY_URL |
| `kbe_harborland_meriken_mei_li_jian_gong_yuan_dong_fang_hotel_2` | 神户美利坚公园东方酒店（神戸メリケンパークオリエンタル） | b4(高端) | skeleton | 1100 | EMPTY_URL |
| `kbe_kitano_shinkobe_kitano_hotel` | 神户北野酒店（神戸北野ホテル） | b5(奢华) | skeleton | 1900 | EMPTY_URL |
| `arm_arima_onsen_tao_quan_gosho_fang` | 陶泉 御所坊（陶泉 御所坊） | b5(奢华) | skeleton | 1900 | EMPTY_URL |
| `arm_arima_onsen_zhu_qu_ting_yuan_shan` | 竹取亭圆山（竹取亭円山） | b3(品质) | skeleton | 600 | EMPTY_URL |
| `arm_arima_onsen_grand_hotel` | 有马格兰大酒店（有馬グランドホテル） | b3(品质) | skeleton | 600 | EMPTY_URL |
| `arm_arima_onsen_hua_xiao_su_hotel` | 花小宿酒店（ホテル花小宿） | b5(奢华) | skeleton | 1900 | EMPTY_URL |
| `arm_arima_onsen_tian_di_zhi_su_ao_zhi_xi_dao` | 天地之宿 奥之细道（天地の宿 奥の細道） | b5(奢华) | skeleton | 1900 | EMPTY_URL |
| `arm_arima_onsen_si_ji_zhi_cai_lv_long` | 四季之彩 旅篭（四季の彩 旅篭） | b3(品质) | skeleton | 600 | EMPTY_URL |
| `arm_arima_onsen_wen_quan_yue_guang_yuan_hong_long_guan` | 有马温泉 月光园 鸿朧馆（有馬温泉 月光園 鴻朧館） | b3(品质) | skeleton | 600 | EMPTY_URL |
| `arm_arima_onsen_yin_shui_zhuang_zhao_le` | 银水庄 兆乐（銀水荘 兆楽） | b3(品质) | skeleton | 600 | EMPTY_URL |
| `arm_arima_onsen_shan_cong_gosho_bie_shu` | 有马山丛 御所别墅（有馬山叢 御所別墅） | b5(奢华) | skeleton | 1900 | EMPTY_URL |
| `arm_arima_onsen_gen_an_wu_lv_feng_ge` | 根岸屋旅凤阁（根岸屋旅鳳閣） | b3(品质) | skeleton | 600 | EMPTY_URL |
| `arm_arima_onsen_you_ma_yu_yuan` | 有马御苑（有馬御苑） | b3(品质) | skeleton | 600 | EMPTY_URL |
| `arm_arima_onsen_gao_sanso_hua_ye` | 高山庄 华野（高山荘 華野） | b5(奢华) | skeleton | 1900 | EMPTY_URL |
| `arm_arima_onsen_hua_jie` | 花结（花結び） | b3(品质) | skeleton | 600 | EMPTY_URL |
| `arm_arima_onsen_yuan_tang_gu_quan_ge` | 元汤 古泉阁（元湯 古泉閣） | b3(品质) | skeleton | 600 | EMPTY_URL |
| `arm_arima_onsen_yue_guang_yuan_you_yue_sanso` | 月光园 游月山庄（月光園 游月山荘） | b3(品质) | skeleton | 600 | EMPTY_URL |
| `arm_arima_onsen_ling_feng_ge` | 陵枫阁（陵楓閣） | b3(品质) | skeleton | 600 | EMPTY_URL |
| `arm_arima_onsen_yue_zhi_zhou` | 月之舟（月への舟） | b3(品质) | skeleton | 600 | EMPTY_URL |
| `arm_arima_onsen_you_ma_guang_cai` | 有马光彩（有馬きらり） | b3(品质) | skeleton | 600 | EMPTY_URL |

### 高野山（10 家）

| id | 店名 | tier | depth | 平季中位 | flags |
|---|---|---|---|---|---|
| `kya_koyasan_temple_hui_guang_yuan` | 惠光院（恵光院） | b2(舒适) | skeleton | 550 | EMPTY_URL |
| `kya_koyasan_temple_yi_cheng_yuan` | 一乘院（一乗院） | b2(舒适) | skeleton | 550 | EMPTY_URL |
| `kya_koyasan_temple_lian_hua_ding_yuan` | 莲华定院（蓮華定院） | b2(舒适) | skeleton | 550 | EMPTY_URL |
| `kya_koyasan_temple_fu_zhi_yuan` | 福智院（福智院） | b2(舒适) | skeleton | 550 | EMPTY_URL |
| `kya_koyasan_temple_xi_nan_yuan` | 西南院（西南院） | b2(舒适) | skeleton | 550 | EMPTY_URL |
| `kya_koyasan_temple_qing_jing_xin_yuan` | 清净心院（清浄心院） | b2(舒适) | skeleton | 550 | EMPTY_URL |
| `kya_koyasan_temple_chi_song_yuan` | 赤松院（赤松院） | b2(舒适) | skeleton | 550 | EMPTY_URL |
| `kya_koyasan_temple_bu_dong_yuan` | 不动院（不動院） | b2(舒适) | skeleton | 550 | EMPTY_URL |
| `kya_koyasan_temple_chang_xi_yuan` | 常喜院（常喜院） | b2(舒适) | skeleton | 550 | EMPTY_URL |
| `kya_koyasan_temple_long_quan_yuan` | 龙泉院（龍泉院） | b2(舒适) | skeleton | 550 | EMPTY_URL |
