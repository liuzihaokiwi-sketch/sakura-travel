# D47 现池 203 家 audit table

自动 dump·149 家有 flag·待 Step 4 逐家迭代修改


## 各 flag 计数

- **PLACEHOLDER_ID**（占位 id h***）：104
- **CLICHE**（套话简介）：29
- **EMPTY_URL**（数据来源仅 hotels.ctrip.com/ 占位）：149
- **DEPTH_FULL_INCOMPLETE**（depth=full 但 note 缺必填）：0
- **TIER_MISMATCH**（迁移前 tier 跟 D47 阈值不符）：0

## flag 明细（按 city 分组）

### 京都（55 家）

| id | 店名 | tier | depth | 平季中位 | flags |
|---|---|---|---|---|---|
| `kyo_shijo_kawaramachi_hotel_okura_kyoto` | 京都大仓酒店（Hotel Okura Kyoto） | b3(品质) | skeleton | 1100 | EMPTY_URL |
| `kyo_shijo_kawaramachi_good_nature_hotel` | Good Nature Hotel（Good Nature Hotel） | b4(高端) | skeleton | 1900 | EMPTY_URL |
| `kyo_shijo_kawaramachi_cross_hotel_kyoto` | Cross Hotel Kyoto（Cross Hotel Kyoto） | b3(品质) | skeleton | 1100 | EMPTY_URL |
| `kyo_gion_higashiyama_genji_kyoto` | Genji Kyoto（Genji Kyoto） | b4(高端) | skeleton | 1900 | EMPTY_URL |
| `kyo_gion_higashiyama_hotel` | Hotel 侑楽 京八坂（Hotel 侑楽 京八坂） | b4(高端) | skeleton | 1900 | EMPTY_URL |
| `kyo_nijo_central_h011` | 京都布莱顿酒店（京都ブライトンホテル） | b3(品质) | skeleton | 1100 | PLACEHOLDER_ID, EMPTY_URL |
| `kyo_kyoto_station_doubletree_by_hilton_kyoto_sta` | DoubleTree by Hilton 京都站（DoubleTree by H | b3(品质) | skeleton | 1100 | EMPTY_URL |
| `kyo_shijo_kawaramachi_h022` | 京都四条新町英特盖特酒店（ホテルインターゲート京都四条新町） | b3(品质) | skeleton | 1100 | PLACEHOLDER_ID, EMPTY_URL |
| `kyo_gion_higashiyama_nohga_hotel` | NOHGA HOTEL 京都清水（NOHGA HOTEL 京都清水） | b4(高端) | skeleton | 1900 | EMPTY_URL |
| `kyo_shijo_kawaramachi_h047` | 京小宿 室町 汤音（京小宿 室町 ゆとね） | b2(舒适) | skeleton | 600 | PLACEHOLDER_ID, CLICHE, EMPTY_URL |
| `kyo_gion_higashiyama_h048` | 料理旅馆 花乐（料理旅館 花楽） | b2(舒适) | skeleton | 600 | PLACEHOLDER_ID, CLICHE, EMPTY_URL |
| `kyo_kyoto_station_tune_stay_kyoto` | TUNE STAY KYOTO（TUNE STAY KYOTO） | b4(高端) | skeleton | 1900 | EMPTY_URL |
| `kyo_shijo_kawaramachi_insomnia_kyoto_oike` | insomnia KYOTO OIKE（insomnia KYOTO OIKE） | b4(高端) | skeleton | 1900 | EMPTY_URL |
| `kyo_shijo_kawaramachi_h057` | 先斗町依斯柏席昂酒店（ホテルエスパシオン先斗町） | b4(高端) | skeleton | 1900 | PLACEHOLDER_ID, EMPTY_URL |
| `kyo_shijo_kawaramachi_h059` | 京都五条假日酒店（ホリデイ・イン京都五条） | b3(品质) | skeleton | 1100 | PLACEHOLDER_ID, EMPTY_URL |
| `kyo_gion_higashiyama_sowaka` | SOWAKA（SOWAKA） | b4(高端) | skeleton | 1900 | EMPTY_URL |
| `kyo_kyoto_station_h061` | 京都梅小路花传抄（京都梅小路花伝抄） | b2(舒适) | skeleton | 600 | PLACEHOLDER_ID, CLICHE, EMPTY_URL |
| `kyo_nijo_central_h062` | 京都鹰峰收获酒店（ホテルハーヴェスト京都鷹峯） | b4(高端) | skeleton | 1200 | PLACEHOLDER_ID, EMPTY_URL |
| `kyo_gion_higashiyama_doubletree_by_hilton_kyoto_hig` | DoubleTree by Hilton 京都东山（DoubleTree by  | b3(品质) | skeleton | 1100 | EMPTY_URL |
| `kyo_kyoto_station_sakura_terrace_the_gallery` | 樱花台画廊饭店（櫻花台畫廊飯店 (Sakura Terrace The Gall | b4(高端) | skeleton | 1900 | EMPTY_URL |
| `kyo_shijo_kawaramachi_sequence` | sequence饭店-京都五条（sequence飯店-京都五条） | b4(高端) | skeleton | 1900 | EMPTY_URL |
| `kyo_shijo_kawaramachi_h078` | 京都格兰贝尔酒店（京都グランベルホテル） | b4(高端) | skeleton | 1900 | PLACEHOLDER_ID, EMPTY_URL |
| `kyo_kyoto_station_h080` | 京阪京都大饭店（ホテル京阪京都グランデ） | b3(品质) | skeleton | 1100 | PLACEHOLDER_ID, EMPTY_URL |
| `kyo_shijo_kawaramachi_h081` | 门酒店京都高濑川（ザ・ゲートホテル京都高瀬川） | b4(高端) | skeleton | 1900 | PLACEHOLDER_ID, EMPTY_URL |
| `kyo_shijo_kawaramachi_rojiyu_kyoto` | ROJIYU KYOTO（ROJIYU KYOTO） | b4(高端) | skeleton | 1900 | EMPTY_URL |
| `kyo_gion_higashiyama_h088` | 御室花传抄（御室花伝抄） | b2(舒适) | skeleton | 600 | PLACEHOLDER_ID, CLICHE, EMPTY_URL |
| `kyo_shijo_kawaramachi_h097` | 京都悠洛悦苑（京都悠洛悦苑） | b4(高端) | skeleton | 1900 | PLACEHOLDER_ID, EMPTY_URL |
| `kyo_gion_higashiyama_fufu_kyoto` | Fufu Kyoto（Fufu Kyoto） | b4(高端) | skeleton | 1900 | CLICHE, EMPTY_URL |
| `kyo_shijo_kawaramachi_h291` | 四条河原町温泉 空庭露台京都（四条河原町温泉 空庭テラス京都） | b2(舒适) | skeleton | 600 | PLACEHOLDER_ID, CLICHE, EMPTY_URL |
| `kyo_shijo_kawaramachi_h292` | 四条河原町温泉 空庭露台京都 别邸（四条河原町温泉 空庭テラス京都 別邸） | b4(高端) | skeleton | 1900 | PLACEHOLDER_ID, CLICHE, EMPTY_URL |
| `kyo_kyoto_station_h305` | 京汤元 鸠屋瑞凤阁（京湯元 ハトヤ瑞鳳閣） | b2(舒适) | skeleton | 600 | PLACEHOLDER_ID, CLICHE, EMPTY_URL |
| `kyo_arashiyama_h315` | 京都岚山温泉 花传抄（京都 嵐山温泉 花伝抄） | b3(品质) | skeleton | 1100 | PLACEHOLDER_ID, CLICHE, EMPTY_URL |
| `kyo_gion_higashiyama_the_shinmonzen` | The Shinmonzen（The Shinmonzen） | b4(高端) | skeleton | 1900 | EMPTY_URL |
| `kyo_gion_higashiyama_hotel_seiryu_kyoto_kiyomizu` | 京都清水圣龙酒店（Hotel Seiryu Kyoto Kiyomizu） | b4(高端) | skeleton | 1900 | EMPTY_URL |
| `kyo_arashiyama_muni_kyoto_by_onko_chishin` | MUNI KYOTO by Onko Chishin（MUNI KYOTO by | b4(高端) | skeleton | 1900 | EMPTY_URL |
| `kyo_nijo_central_garrya_nijo_castle_kyoto` | 京都二条城嘉瑞亚（Garrya Nijo Castle Kyoto） | b4(高端) | skeleton | 1900 | EMPTY_URL |
| `kyo_shijo_kawaramachi_candeohotels` | Candeo Hotels 京都乌丸六角（カンデオホテルズ京都烏丸六角） | b3(品质) | skeleton | 1100 | EMPTY_URL |
| `kyo_shijo_kawaramachi_h342` | 町家住宅京都（町家レジデンスイン京都） | b2(舒适) | skeleton | 750 | PLACEHOLDER_ID, EMPTY_URL |
| `kyo_shijo_kawaramachi_kuraya` | 藏屋（藏や (Kuraya)） | b2(舒适) | skeleton | 750 | EMPTY_URL |
| `kyo_gion_higashiyama_h346` | 祇园新桥 梅庵（祇園新橋 梅庵） | b2(舒适) | skeleton | 750 | PLACEHOLDER_ID, EMPTY_URL |
| `kyo_gion_higashiyama_h352` | 金光院 萤庵（金光院 ほたる庵） | b2(舒适) | skeleton | 550 | PLACEHOLDER_ID, EMPTY_URL |
| `kyo_gion_higashiyama_h354` | 仁和寺 御室会馆（仁和寺 御室会館） | b2(舒适) | skeleton | 550 | PLACEHOLDER_ID, EMPTY_URL |
| `kyo_gion_higashiyama_h355` | 知恩院 和顺会馆（知恩院 和順会館） | b2(舒适) | skeleton | 550 | PLACEHOLDER_ID, EMPTY_URL |
| `kyo_gion_higashiyama_h356` | 妙心寺 东林院（妙心寺 東林院） | b2(舒适) | skeleton | 550 | PLACEHOLDER_ID, EMPTY_URL |
| `kyo_arashiyama_h357` | 鹿王院（鹿王院） | b2(舒适) | skeleton | 550 | PLACEHOLDER_ID, EMPTY_URL |
| `kyo_shijo_kawaramachi_h358` | 药师院（薬師院） | b2(舒适) | skeleton | 550 | PLACEHOLDER_ID, EMPTY_URL |
| `kyo_shijo_kawaramachi_h369` | 松井本馆（松井本館） | b2(舒适) | skeleton | 600 | PLACEHOLDER_ID, CLICHE, EMPTY_URL |
| `kyo_shijo_kawaramachi_h370` | 天妇罗吉川（天ぷら吉川） | b2(舒适) | skeleton | 600 | PLACEHOLDER_ID, CLICHE, EMPTY_URL |
| `kyo_gion_higashiyama_h371` | 柚子屋旅馆（柚子屋旅館） | b2(舒适) | skeleton | 600 | PLACEHOLDER_ID, CLICHE, EMPTY_URL |
| `kyo_arashiyama_h372` | 红叶家本馆 高雄山庄（もみぢ家本館 高雄山荘） | b2(舒适) | skeleton | 600 | PLACEHOLDER_ID, CLICHE, EMPTY_URL |
| `kyo_gion_higashiyama_h373` | 纯和风料理旅馆 季乃会（純和風料理旅館 き乃ゑ） | b2(舒适) | skeleton | 600 | PLACEHOLDER_ID, CLICHE, EMPTY_URL |
| `kyo_arashiyama_h374` | 岚山温泉 花传抄（嵐山温泉 花伝抄） | b2(舒适) | skeleton | 600 | PLACEHOLDER_ID, CLICHE, EMPTY_URL |
| `kyo_arashiyama_h381` | 贵船 藤屋（貴船 ふじや） | b4(高端) | skeleton | 1600 | PLACEHOLDER_ID, CLICHE, EMPTY_URL |
| `kyo_arashiyama_h382` | 料理旅馆 右源太（料理旅館 右源太） | b5(奢华) | skeleton | 2500 | PLACEHOLDER_ID, CLICHE, EMPTY_URL |
| `kyo_arashiyama_h386` | 格兰西嵐山酒店（ザ グランド ウェスト 嵐山） | b4(高端) | skeleton | 1900 | PLACEHOLDER_ID, EMPTY_URL |

### 城崎（9 家）

| id | 店名 | tier | depth | 平季中位 | flags |
|---|---|---|---|---|---|
| `kns_kinosaki_onsen_h275` | 西村屋酒店招月庭（西村屋ホテル招月庭） | b5(奢华) | skeleton | 1900 | PLACEHOLDER_ID, EMPTY_URL |
| `kns_kinosaki_onsen_h278` | 城崎温泉 喜乐（城崎温泉 喜楽） | b3(品质) | skeleton | 600 | PLACEHOLDER_ID, EMPTY_URL |
| `kns_kinosaki_onsen_h280` | 大西屋水翔苑（大西屋水翔苑） | b3(品质) | skeleton | 600 | PLACEHOLDER_ID, EMPTY_URL |
| `kns_kinosaki_onsen_h302` | 蟹宿六之屋（蟹宿むつの屋） | b3(品质) | skeleton | 600 | PLACEHOLDER_ID, EMPTY_URL |
| `kns_kinosaki_onsen_h307` | 深山（深山） | b3(品质) | skeleton | 600 | PLACEHOLDER_ID, EMPTY_URL |
| `kns_kinosaki_onsen_h311` | 新泉（新泉） | b3(品质) | skeleton | 600 | PLACEHOLDER_ID, EMPTY_URL |
| `kns_kinosaki_onsen_h312` | 月色（月明かり） | b3(品质) | skeleton | 600 | PLACEHOLDER_ID, EMPTY_URL |
| `kns_kinosaki_onsen_h313` | 泉翠（泉翠） | b3(品质) | skeleton | 600 | PLACEHOLDER_ID, EMPTY_URL |
| `kns_kinosaki_onsen_h314` | 艳乡（艷郷） | b3(品质) | skeleton | 600 | PLACEHOLDER_ID, EMPTY_URL |

### 大阪（32 家）

| id | 店名 | tier | depth | 平季中位 | flags |
|---|---|---|---|---|---|
| `osk_namba_dotonbori_swissotel_nankai_osaka` | 大阪南海瑞士酒店（Swissotel Nankai Osaka） | b3(品质) | skeleton | 600 | EMPTY_URL |
| `osk_shinsaibashi_hotel_nikko_osaka` | 大阪日航酒店（Hotel Nikko Osaka） | b3(品质) | skeleton | 600 | EMPTY_URL |
| `osk_namba_dotonbori_hotel_new_otani_osaka` | 大阪新大谷酒店（Hotel New Otani Osaka） | b3(品质) | skeleton | 600 | EMPTY_URL |
| `osk_umeda_kita_h106` | 丽嘉皇家大酒店大阪（リーガロイヤルホテル大阪） | b3(品质) | skeleton | 600 | PLACEHOLDER_ID, EMPTY_URL |
| `osk_namba_dotonbori_cross_hotel_osaka` | Cross Hotel Osaka（Cross Hotel Osaka） | b3(品质) | skeleton | 600 | EMPTY_URL |
| `osk_bay_area_h110` | 大阪湾王子大酒店（グランドプリンスホテル大阪ベイ） | b5(奢华) | skeleton | 1900 | PLACEHOLDER_ID, EMPTY_URL |
| `osk_umeda_kita_zentis_osaka` | Zentis Osaka（Zentis Osaka） | b5(奢华) | skeleton | 1900 | EMPTY_URL |
| `osk_shinsaibashi_candeo_hotels_osaka_shinsaibas` | Candeo Hotels 大阪心斋桥（Candeo Hotels Osaka  | b3(品质) | skeleton | 600 | EMPTY_URL |
| `osk_namba_dotonbori_hiyori` | 大阪难波Hiyori酒店（大阪なんばHiyoriホテル） | b3(品质) | skeleton | 600 | EMPTY_URL |
| `osk_shinsaibashi_the_bridge_hotel` | The Bridge Hotel 心斋桥（The Bridge Hotel 心斎 | b3(品质) | skeleton | 600 | EMPTY_URL |
| `osk_bay_area_h127` | 环球港口酒店（ホテル ユニバーサルポート） | b5(奢华) | skeleton | 1900 | PLACEHOLDER_ID, EMPTY_URL |
| `osk_bay_area_usj` | 公园前沿酒店 USJ（ザ パーク フロント ホテル USJ） | b5(奢华) | skeleton | 1900 | EMPTY_URL |
| `osk_namba_dotonbori_h132` | 大阪蒙特利格拉斯密尔酒店（ホテルモントレ グラスミア大阪） | b3(品质) | skeleton | 600 | PLACEHOLDER_ID, EMPTY_URL |
| `osk_namba_dotonbori_here_osaka_namba` | &Here OSAKA NAMBA（&Here OSAKA NAMBA） | b5(奢华) | skeleton | 1900 | EMPTY_URL |
| `osk_tennoji_shinsekai_omo7_by` | OMO7大阪 by 星野度假村（OMO7大阪 by 星野リゾート） | b3(品质) | skeleton | 600 | EMPTY_URL |
| `osk_umeda_kita_h144` | 大阪梅田希尔顿格芮精选酒店（キャノピーbyヒルトン大阪梅田） | b3(品质) | skeleton | 600 | PLACEHOLDER_ID, EMPTY_URL |
| `osk_namba_dotonbori_h160` | 难波东方酒店（ナンバオリエンタルホテル） | b3(品质) | skeleton | 600 | PLACEHOLDER_ID, EMPTY_URL |
| `osk_tennoji_shinsekai_h164` | 京瓷酒店（ホテル京セラ） | b3(品质) | skeleton | 600 | PLACEHOLDER_ID, EMPTY_URL |
| `osk_honmachi_h168` | 大阪本町维斯塔尊贵酒店（ホテルビスタプレミオ大阪本町） | b3(品质) | skeleton | 600 | PLACEHOLDER_ID, EMPTY_URL |
| `osk_bay_area_h173` | 环球影城奇点酒店（ユニバーサルスタジオ シンギュラリホテル） | b3(品质) | skeleton | 600 | PLACEHOLDER_ID, EMPTY_URL |
| `osk_shinsaibashi_h174` | 大阪蒙特利勒弗莱尔酒店（ホテルモントレ ル・フレール大阪） | b3(品质) | skeleton | 600 | PLACEHOLDER_ID, EMPTY_URL |
| `osk_honmachi_h175` | 三井花园酒店大阪淀屋桥（三井ガーデンホテル大阪淀屋橋） | b3(品质) | skeleton | 600 | PLACEHOLDER_ID, EMPTY_URL |
| `osk_namba_dotonbori_h176` | 大阪城希尔顿逸林酒店（ダブルツリーbyヒルトン大阪城） | b3(品质) | skeleton | 600 | PLACEHOLDER_ID, EMPTY_URL |
| `osk_umeda_kita_tones_osaka` | TONES OSAKA（TONES OSAKA） | b5(奢华) | skeleton | 1900 | EMPTY_URL |
| `osk_umeda_kita_h191` | 大阪堂岛雅乐轩（アロフト大阪堂島） | b5(奢华) | skeleton | 1900 | PLACEHOLDER_ID, EMPTY_URL |
| `osk_honmachi_the_boly_osaka` | THE BOLY OSAKA（THE BOLY OSAKA） | b5(奢华) | skeleton | 1900 | EMPTY_URL |
| `osk_honmachi_h193` | 大阪本町莱弗利酒店（ザ・ライブリー大阪本町） | b5(奢华) | skeleton | 1900 | PLACEHOLDER_ID, EMPTY_URL |
| `osk_bay_area_risonare` | 星野度假村 Risonare 大阪（星野リゾート リゾナーレ大阪） | b5(奢华) | skeleton | 1900 | EMPTY_URL |
| `osk_tennoji_shinsekai_h195` | 大阪天王寺塔安达之森（アンダの森 大阪天王寺タワー） | b5(奢华) | skeleton | 1900 | PLACEHOLDER_ID, EMPTY_URL |
| `osk_honmachi_voco` | voco大阪中央（voco大阪セントラル） | b3(品质) | skeleton | 600 | EMPTY_URL |
| `osk_bay_area_liber` | 大阪LIBER酒店（大阪LIBERホテル） | b5(奢华) | skeleton | 1900 | CLICHE, EMPTY_URL |
| `osk_umeda_kita_h337` | 大阪阿尔莫尼安布拉塞酒店（アルモニーアンブラッセ大阪） | b5(奢华) | skeleton | 1900 | PLACEHOLDER_ID, EMPTY_URL |

### 奈良（10 家）

| id | 店名 | tier | depth | 平季中位 | flags |
|---|---|---|---|---|---|
| `nra_nara_park_area_h243` | 紫翠奢华精选酒店·奈良（紫翠 ラグジュアリーコレクションホテル 奈良） | b5(奢华) | skeleton | 1600 | PLACEHOLDER_ID, EMPTY_URL |
| `nra_nara_park_area_h246` | 奈良街道塞托雷（セトレならまち） | b5(奢华) | skeleton | 1900 | PLACEHOLDER_ID, EMPTY_URL |
| `nra_nara_park_area_miroku_nara_by_the_share_hotel` | MIROKU Nara by THE SHARE HOTELS（MIROKU N | b5(奢华) | skeleton | 1900 | EMPTY_URL |
| `nra_nara_park_area_fufu_nara` | Fufu Nara（Fufu Nara） | b5(奢华) | skeleton | 1900 | CLICHE, EMPTY_URL |
| `nra_nara_park_area_jw_marriott_hotel_nara` | 奈良JW万豪酒店（JW Marriott Hotel Nara） | b5(奢华) | skeleton | 1600 | EMPTY_URL |
| `nra_nara_park_area_h368` | 春日酒店（春日ホテル） | b3(品质) | skeleton | 600 | PLACEHOLDER_ID, CLICHE, EMPTY_URL |
| `nra_nara_park_area_h375` | 古都之宿 武藏野（古都の宿 むさし野） | b3(品质) | skeleton | 600 | PLACEHOLDER_ID, CLICHE, EMPTY_URL |
| `nra_nara_park_area_h378` | 游景之宿 平城（遊景の宿 平城） | b3(品质) | skeleton | 600 | PLACEHOLDER_ID, CLICHE, EMPTY_URL |
| `nra_nara_park_area_h379` | 四季亭（四季亭） | b3(品质) | skeleton | 600 | PLACEHOLDER_ID, CLICHE, EMPTY_URL |
| `nra_nara_park_area_h380` | 飞鸟庄（飛鳥荘） | b3(品质) | skeleton | 600 | PLACEHOLDER_ID, CLICHE, EMPTY_URL |

### 白浜（3 家）

| id | 店名 | tier | depth | 平季中位 | flags |
|---|---|---|---|---|---|
| `shr_shirahama_infinito_hotel_spa_nanki_shira` | INFINITO Hotel & Spa Nanki Shirahama（INF | b4(高端) | skeleton | 1200 | CLICHE, EMPTY_URL |
| `shr_shirahama_shiraraso_grand_hotel` | Shiraraso Grand Hotel（Shiraraso Grand Ho | b3(品质) | skeleton | 600 | CLICHE, EMPTY_URL |
| `shr_shirahama_shirahama_key_terrace_hotel_se` | Shirahama Key Terrace Hotel Seamore（Shir | b3(品质) | skeleton | 600 | CLICHE, EMPTY_URL |

### 神户（30 家）

| id | 店名 | tier | depth | 平季中位 | flags |
|---|---|---|---|---|---|
| `kbe_harborland_meriken_h202` | 神户拉斯维特海港酒店（ホテル ラ・スイート神戸ハーバーランド） | b4(高端) | skeleton | 1100 | PLACEHOLDER_ID, EMPTY_URL |
| `kbe_harborland_meriken_h204` | 神户大仓酒店（ホテルオークラ神戸） | b4(高端) | skeleton | 1100 | PLACEHOLDER_ID, EMPTY_URL |
| `kbe_harborland_meriken_h205` | 神户美利坚公园东方酒店（神戸メリケンパークオリエンタルホテル） | b4(高端) | skeleton | 1100 | PLACEHOLDER_ID, EMPTY_URL |
| `kbe_bay_area_h207` | 神户湾喜来登大酒店（神戸ベイシェラトン） | b4(高端) | skeleton | 1100 | PLACEHOLDER_ID, EMPTY_URL |
| `kbe_kitano_shinkobe_ana_crowne_plaza_kobe` | 神户全日空皇冠假日酒店（ANA Crowne Plaza Kobe） | b4(高端) | skeleton | 1100 | EMPTY_URL |
| `kbe_motomachi_nankinmach_oriental_hotel_kobe` | 神户东方大酒店（東方ホテル (Oriental Hotel Kobe)） | b4(高端) | skeleton | 1100 | EMPTY_URL |
| `kbe_harborland_meriken_h219` | 神户海港拉斯维特酒店（神戸ハーバーランドラ・スイート） | b4(高端) | skeleton | 1100 | PLACEHOLDER_ID, EMPTY_URL |
| `kbe_harborland_meriken_h220` | 神户大仓大酒店（神戸大倉ホテル） | b4(高端) | skeleton | 1100 | PLACEHOLDER_ID, EMPTY_URL |
| `kbe_harborland_meriken_h221` | 神户美利坚公园东方酒店（神戸メリケンパークオリエンタル） | b4(高端) | skeleton | 1100 | PLACEHOLDER_ID, EMPTY_URL |
| `kbe_kitano_shinkobe_h234` | 神户北野酒店（神戸北野ホテル） | b5(奢华) | skeleton | 1900 | PLACEHOLDER_ID, EMPTY_URL |
| `kbe_harborland_meriken_h260` | 神户港温泉 莲（神戸みなと温泉 蓮） | b3(品质) | skeleton | 600 | PLACEHOLDER_ID, CLICHE, EMPTY_URL |
| `arm_arima_onsen_h263` | 陶泉 御所坊（陶泉 御所坊） | b5(奢华) | skeleton | 1900 | PLACEHOLDER_ID, EMPTY_URL |
| `arm_arima_onsen_h264` | 竹取亭圆山（竹取亭円山） | b3(品质) | skeleton | 600 | PLACEHOLDER_ID, EMPTY_URL |
| `arm_arima_onsen_h265` | 有马格兰大酒店（有馬グランドホテル） | b3(品质) | skeleton | 600 | PLACEHOLDER_ID, EMPTY_URL |
| `arm_arima_onsen_h267` | 花小宿酒店（ホテル花小宿） | b5(奢华) | skeleton | 1900 | PLACEHOLDER_ID, EMPTY_URL |
| `arm_arima_onsen_h268` | 天地之宿 奥之细道（天地の宿 奥の細道） | b5(奢华) | skeleton | 1900 | PLACEHOLDER_ID, EMPTY_URL |
| `arm_arima_onsen_h269` | 四季之彩 旅篭（四季の彩 旅篭） | b3(品质) | skeleton | 600 | PLACEHOLDER_ID, EMPTY_URL |
| `arm_arima_onsen_h270` | 有马温泉 月光园 鸿朧馆（有馬温泉 月光園 鴻朧館） | b3(品质) | skeleton | 600 | PLACEHOLDER_ID, EMPTY_URL |
| `arm_arima_onsen_h271` | 银水庄 兆乐（銀水荘 兆楽） | b3(品质) | skeleton | 600 | PLACEHOLDER_ID, EMPTY_URL |
| `arm_arima_onsen_h272` | 有马山丛 御所别墅（有馬山叢 御所別墅） | b5(奢华) | skeleton | 1900 | PLACEHOLDER_ID, EMPTY_URL |
| `arm_arima_onsen_h273` | 根岸屋旅凤阁（根岸屋旅鳳閣） | b3(品质) | skeleton | 600 | PLACEHOLDER_ID, EMPTY_URL |
| `arm_arima_onsen_h274` | 有马御苑（有馬御苑） | b3(品质) | skeleton | 600 | PLACEHOLDER_ID, EMPTY_URL |
| `kbe_harborland_meriken_h293` | 神户港温泉 莲（神戸港温泉 蓮） | b3(品质) | skeleton | 600 | PLACEHOLDER_ID, CLICHE, EMPTY_URL |
| `arm_arima_onsen_h294` | 高山庄 华野（高山荘 華野） | b5(奢华) | skeleton | 1900 | PLACEHOLDER_ID, EMPTY_URL |
| `arm_arima_onsen_h295` | 花结（花結び） | b3(品质) | skeleton | 600 | PLACEHOLDER_ID, EMPTY_URL |
| `arm_arima_onsen_h296` | 元汤 古泉阁（元湯 古泉閣） | b3(品质) | skeleton | 600 | PLACEHOLDER_ID, EMPTY_URL |
| `arm_arima_onsen_h297` | 月光园 游月山庄（月光園 游月山荘） | b3(品质) | skeleton | 600 | PLACEHOLDER_ID, EMPTY_URL |
| `arm_arima_onsen_h300` | 陵枫阁（陵楓閣） | b3(品质) | skeleton | 600 | PLACEHOLDER_ID, EMPTY_URL |
| `arm_arima_onsen_h304` | 月之舟（月への舟） | b3(品质) | skeleton | 600 | PLACEHOLDER_ID, EMPTY_URL |
| `arm_arima_onsen_h308` | 有马光彩（有馬きらり） | b3(品质) | skeleton | 600 | PLACEHOLDER_ID, EMPTY_URL |

### 高野山（10 家）

| id | 店名 | tier | depth | 平季中位 | flags |
|---|---|---|---|---|---|
| `kya_koyasan_temple_h349` | 惠光院（恵光院） | b2(舒适) | skeleton | 550 | PLACEHOLDER_ID, EMPTY_URL |
| `kya_koyasan_temple_h350` | 一乘院（一乗院） | b2(舒适) | skeleton | 550 | PLACEHOLDER_ID, EMPTY_URL |
| `kya_koyasan_temple_h351` | 莲华定院（蓮華定院） | b2(舒适) | skeleton | 550 | PLACEHOLDER_ID, EMPTY_URL |
| `kya_koyasan_temple_h359` | 福智院（福智院） | b2(舒适) | skeleton | 550 | PLACEHOLDER_ID, EMPTY_URL |
| `kya_koyasan_temple_h361` | 西南院（西南院） | b2(舒适) | skeleton | 550 | PLACEHOLDER_ID, EMPTY_URL |
| `kya_koyasan_temple_h362` | 清净心院（清浄心院） | b2(舒适) | skeleton | 550 | PLACEHOLDER_ID, EMPTY_URL |
| `kya_koyasan_temple_h363` | 赤松院（赤松院） | b2(舒适) | skeleton | 550 | PLACEHOLDER_ID, EMPTY_URL |
| `kya_koyasan_temple_h364` | 不动院（不動院） | b2(舒适) | skeleton | 550 | PLACEHOLDER_ID, EMPTY_URL |
| `kya_koyasan_temple_h365` | 常喜院（常喜院） | b2(舒适) | skeleton | 550 | PLACEHOLDER_ID, EMPTY_URL |
| `kya_koyasan_temple_h367` | 龙泉院（龍泉院） | b2(舒适) | skeleton | 550 | PLACEHOLDER_ID, EMPTY_URL |
