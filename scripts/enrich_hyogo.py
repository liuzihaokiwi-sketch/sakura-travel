"""
Enrich hyogo.json spots and seasonal_events with additional fields.
Adds: city_code, prefecture, address_ja, nearest_station, when, cost,
      review_signals (with dimension_scores), queue_wait_minutes,
      corridor_tags, risk_flags, descriptions
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC = ROOT / "data" / "kansai_spots" / "hyogo.json"

with open(SRC, "r", encoding="utf-8") as f:
    data = json.load(f)

# ─── Spot enrichment data ────────────────────────────────────────────────────
spot_enrichment = {
    "hyo_kitano_ijinkan": {
        "city_code": "kobe",
        "prefecture": "兵庫県",
        "address_ja": "兵庫県神戸市中央区北野町2〜3丁目",
        "nearest_station": "JR三ノ宮駅から徒歩約20分 / 新神戸駅から徒歩約10分",
        "when": {
            "open_days": "各館により異なる（通常毎日）",
            "open_hours": "9:00-18:00（館により異なる）",
            "last_entry": "17:30",
            "closed_notes": "一部館は不定休あり"
        },
        "cost": {"admission_jpy": 500, "typical_spend_jpy": 1500, "budget_tier": "mid"},
        "review_signals": {
            "overall_score": 4.3,
            "review_count_approx": 8000,
            "dimension_scores": {
                "scenery": 8, "cultural_depth": 8, "accessibility": 6,
                "crowd_comfort": 5, "uniqueness": 9, "value_for_money": 6
            }
        },
        "queue_wait_minutes": 10,
        "corridor_tags": ["kitano"],
        "risk_flags": ["weekends crowded", "steep uphill walking"],
        "descriptions": {
            "why_selected": "明治時代の西洋建築が現存する日本屈指の歴史街区。神戸の国際性を体感できる唯一の場所",
            "what_to_expect": "英国館・風見鶏館など洋館が点在する坂道を散策。入館するなら組合券が割安。街歩き自体は無料",
            "skip_if": "坂道が苦手な方、各館の入館料を払いたくない方は外観だけ見て通過も可"
        }
    },
    "hyo_nankinmachi": {
        "city_code": "kobe",
        "prefecture": "兵庫県",
        "address_ja": "兵庫県神戸市中央区元町通1〜2丁目（南京町広場周辺）",
        "nearest_station": "阪神元町駅から徒歩約2分 / JR元町駅から徒歩約3分",
        "when": {
            "open_days": "毎日（各店舗による）",
            "open_hours": "10:00-21:00（店舗により異なる）",
            "last_entry": None,
            "closed_notes": "旧正月期間は混雑のため早期閉店あり"
        },
        "cost": {"admission_jpy": 0, "typical_spend_jpy": 1000, "budget_tier": "budget"},
        "review_signals": {
            "overall_score": 4.0,
            "review_count_approx": 6000,
            "dimension_scores": {
                "scenery": 7, "cultural_depth": 6, "accessibility": 9,
                "crowd_comfort": 4, "uniqueness": 7, "value_for_money": 8
            }
        },
        "queue_wait_minutes": 15,
        "corridor_tags": ["sannomiya"],
        "risk_flags": ["lunch hours very crowded", "narrow alleys"],
        "descriptions": {
            "why_selected": "日本三大中華街の一つ。神戸豚まんなど街歩きグルメの密度が高く、短時間で満足度が高い",
            "what_to_expect": "約100mの通りに屋台・中華料理店・みやげ物屋が密集。老祥記の豚まんは行列必至（15〜20分待ち）",
            "skip_if": "中華料理に興味がない方、混雑が苦手な方"
        }
    },
    "hyo_meriken_park": {
        "city_code": "kobe",
        "prefecture": "兵庫県",
        "address_ja": "兵庫県神戸市中央区波止場町2番地",
        "nearest_station": "地下鉄みなと元町駅から徒歩約7分 / JR神戸駅から徒歩約15分",
        "when": {
            "open_days": "毎日",
            "open_hours": "24時間開放（公園エリア）",
            "last_entry": None,
            "closed_notes": None
        },
        "cost": {"admission_jpy": 0, "typical_spend_jpy": 500, "budget_tier": "budget"},
        "review_signals": {
            "overall_score": 4.4,
            "review_count_approx": 12000,
            "dimension_scores": {
                "scenery": 9, "cultural_depth": 6, "accessibility": 7,
                "crowd_comfort": 7, "uniqueness": 8, "value_for_money": 10
            }
        },
        "queue_wait_minutes": 0,
        "corridor_tags": ["harborland"],
        "risk_flags": ["windy in winter", "weekends crowded near BE KOBE sign"],
        "descriptions": {
            "why_selected": "神戸を代表する港のシンボルゾーン。BE KOBEモニュメント・神戸港震災メモリアルパーク・ポートタワーを一気に巡れる",
            "what_to_expect": "海沿いの広場で潮風を感じながら散策。夕暮れ〜夜間はBE KOBEのライトアップが美しい。入場無料",
            "skip_if": "港・海景に興味がない方"
        }
    },
    "hyo_kobe_tower": {
        "city_code": "kobe",
        "prefecture": "兵庫県",
        "address_ja": "兵庫県神戸市中央区波止場町5番5号",
        "nearest_station": "地下鉄みなと元町駅から徒歩約7分 / JR神戸駅から徒歩約15分",
        "when": {
            "open_days": "毎日",
            "open_hours": "10:00-22:00",
            "last_entry": "21:30",
            "closed_notes": "強風・悪天候時は展望台クローズの場合あり"
        },
        "cost": {"admission_jpy": 1000, "typical_spend_jpy": 1500, "budget_tier": "mid"},
        "review_signals": {
            "overall_score": 4.1,
            "review_count_approx": 5000,
            "dimension_scores": {
                "scenery": 8, "cultural_depth": 5, "accessibility": 7,
                "crowd_comfort": 6, "uniqueness": 7, "value_for_money": 6
            }
        },
        "queue_wait_minutes": 15,
        "corridor_tags": ["harborland"],
        "risk_flags": ["closed in bad weather", "crowded at sunset"],
        "descriptions": {
            "why_selected": "神戸港のランドマーク。2023年リニューアル後は回転カフェが加わり、飲食しながら港景色を楽しめる",
            "what_to_expect": "双曲面デザインの赤いタワーに登り、神戸港・大阪湾・明石海峡を360度展望。夜景も美しい",
            "skip_if": "展望台系施設に興味がない方、メリケンパークから外観だけ楽しめれば十分という方"
        }
    },
    "hyo_rokko_maya_nightview": {
        "city_code": "kobe",
        "prefecture": "兵庫県",
        "address_ja": "兵庫県神戸市灘区摩耶山掬星台（摩耶山頂）",
        "nearest_station": "阪急王子公園駅からバス+ケーブル+ロープウェイで約40分",
        "when": {
            "open_days": "毎日（ケーブル・ロープウェイの運行日に準ずる）",
            "open_hours": "16:00-21:00（夜景推奨時間帯）",
            "last_entry": "20:50",
            "closed_notes": "ケーブル・ロープウェイは季節により運休あり、事前確認必須"
        },
        "cost": {"admission_jpy": 0, "typical_spend_jpy": 3000, "budget_tier": "mid"},
        "review_signals": {
            "overall_score": 4.7,
            "review_count_approx": 9000,
            "dimension_scores": {
                "scenery": 10, "cultural_depth": 4, "accessibility": 5,
                "crowd_comfort": 6, "uniqueness": 9, "value_for_money": 7
            }
        },
        "queue_wait_minutes": 20,
        "corridor_tags": ["rokko"],
        "risk_flags": ["last ropeway time strict", "cold on summit", "seasonal closures"],
        "descriptions": {
            "why_selected": "函館山・稲佐山と並ぶ日本三大夜景の一つ。標高700mから神戸・大阪・明石まで広がる「千万ドルの夜景」",
            "what_to_expect": "日没30分前に掬星台に到着し、マジックアワーから夜景への移行を体感。防寒着必携",
            "skip_if": "交通アクセスの複雑さを避けたい方、夜間の外出が難しい方"
        }
    },
    "hyo_ikuta_shrine": {
        "city_code": "kobe",
        "prefecture": "兵庫県",
        "address_ja": "兵庫県神戸市中央区下山手通1丁目2番1号",
        "nearest_station": "JR・阪急・阪神三ノ宮駅から徒歩約5分",
        "when": {
            "open_days": "毎日",
            "open_hours": "7:00-17:00（境内は常時参拝可）",
            "last_entry": None,
            "closed_notes": None
        },
        "cost": {"admission_jpy": 0, "typical_spend_jpy": 500, "budget_tier": "budget"},
        "review_signals": {
            "overall_score": 4.1,
            "review_count_approx": 7000,
            "dimension_scores": {
                "scenery": 7, "cultural_depth": 7, "accessibility": 10,
                "crowd_comfort": 6, "uniqueness": 6, "value_for_money": 10
            }
        },
        "queue_wait_minutes": 5,
        "corridor_tags": ["sannomiya"],
        "risk_flags": ["hatsumode season extremely crowded"],
        "descriptions": {
            "why_selected": "神戸最古の神社。三宮繁華街に隣接し、縁結びの神として参拝者が絶えない。境内の苔庭「生田の森」は都市のオアシス",
            "what_to_expect": "朱塗りの本殿と静寂な境内を30分で巡れる。おみくじ・お守りの種類が豊富",
            "skip_if": "神社仏閣に特に関心がない方"
        }
    },
    "hyo_kyu_kyoryuchi": {
        "city_code": "kobe",
        "prefecture": "兵庫県",
        "address_ja": "兵庫県神戸市中央区明石町・海岸通周辺",
        "nearest_station": "地下鉄旧居留地・大丸前駅から徒歩約1分",
        "when": {
            "open_days": "毎日（屋外エリアは24時間）",
            "open_hours": "終日（店舗は10:00-20:00）",
            "last_entry": None,
            "closed_notes": None
        },
        "cost": {"admission_jpy": 0, "typical_spend_jpy": 2000, "budget_tier": "mid"},
        "review_signals": {
            "overall_score": 4.2,
            "review_count_approx": 5000,
            "dimension_scores": {
                "scenery": 8, "cultural_depth": 7, "accessibility": 9,
                "crowd_comfort": 7, "uniqueness": 7, "value_for_money": 8
            }
        },
        "queue_wait_minutes": 0,
        "corridor_tags": ["sannomiya"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "明治時代の外国人居留地跡地に高級ブランド街が形成されたエリア。38番館など歴史的建造物と洗練された都市景観が共存",
            "what_to_expect": "欧風建築群を眺めながら高級ショッピング。南京町・メリケンパークと組み合わせた港神戸半日コースに最適",
            "skip_if": "ショッピングに興味がない方、歴史的建造物に特に関心がない方"
        }
    },
    "hyo_nunobiki_falls": {
        "city_code": "kobe",
        "prefecture": "兵庫県",
        "address_ja": "兵庫県神戸市中央区葺合町布引（布引の滝）",
        "nearest_station": "新神戸駅から徒歩約15分（雄滝まで）",
        "when": {
            "open_days": "毎日",
            "open_hours": "終日（ハーブ園は10:00-17:00）",
            "last_entry": None,
            "closed_notes": "ゴンドラ（ハーブ園行き）は月曜休業の場合あり"
        },
        "cost": {"admission_jpy": 0, "typical_spend_jpy": 1000, "budget_tier": "budget"},
        "review_signals": {
            "overall_score": 4.2,
            "review_count_approx": 4000,
            "dimension_scores": {
                "scenery": 8, "cultural_depth": 4, "accessibility": 7,
                "crowd_comfort": 8, "uniqueness": 7, "value_for_money": 9
            }
        },
        "queue_wait_minutes": 5,
        "corridor_tags": ["rokko"],
        "risk_flags": ["slippery paths after rain"],
        "descriptions": {
            "why_selected": "都心の新幹線駅から徒歩15分で日本三大神滝の一つに到達できる稀有な立地",
            "what_to_expect": "雄滝（43m）・雌滝・夫婦滝・鼓が滝の4つを巡るハイキングルート。整備された遊歩道で歩きやすい",
            "skip_if": "歩くのが苦手な方（往復約30分の山道）、雨天で足場が心配な方"
        }
    },
    "hyo_kobe_beef_experience": {
        "city_code": "kobe",
        "prefecture": "兵庫県",
        "address_ja": "兵庫県神戸市中央区北野坂・旧居留地周辺（各レストランによる）",
        "nearest_station": "JR三ノ宮駅から徒歩約10分",
        "when": {
            "open_days": "毎日（各店舗による）",
            "open_hours": "11:30-14:00 / 17:30-21:30（店舗により異なる）",
            "last_entry": "21:00",
            "closed_notes": "不定休あり、要事前確認"
        },
        "cost": {"admission_jpy": 0, "typical_spend_jpy": 20000, "budget_tier": "luxury"},
        "review_signals": {
            "overall_score": 4.7,
            "review_count_approx": 10000,
            "dimension_scores": {
                "scenery": 7, "cultural_depth": 8, "accessibility": 8,
                "crowd_comfort": 7, "uniqueness": 10, "value_for_money": 7
            }
        },
        "queue_wait_minutes": 0,
        "corridor_tags": ["kitano", "sannomiya"],
        "risk_flags": ["reservation essential", "expensive", "lunch much better value than dinner"],
        "descriptions": {
            "why_selected": "世界最高峰ブランド和牛・神戸牛を産地で食べる唯一の機会。ランチコースなら1.5〜2万円でA5神戸牛鉄板焼きを体験できる",
            "what_to_expect": "鉄板焼きの実演を目の前で楽しむライブ感。モーリヤ・ステーキランドなど老舗が揃う。要予約",
            "skip_if": "予算が限られている方（ランチでも1.5万円以上）、和牛に興味がない方"
        }
    },
    "hyo_kobe_harbor_land": {
        "city_code": "kobe",
        "prefecture": "兵庫県",
        "address_ja": "兵庫県神戸市中央区東川崎町1丁目（umie・MOSAIC）",
        "nearest_station": "JR神戸駅から徒歩約5分 / 地下鉄ハーバーランド駅から徒歩約3分",
        "when": {
            "open_days": "毎日",
            "open_hours": "10:00-21:00（飲食店は〜22:00）",
            "last_entry": None,
            "closed_notes": None
        },
        "cost": {"admission_jpy": 0, "typical_spend_jpy": 3000, "budget_tier": "mid"},
        "review_signals": {
            "overall_score": 4.1,
            "review_count_approx": 8000,
            "dimension_scores": {
                "scenery": 8, "cultural_depth": 4, "accessibility": 9,
                "crowd_comfort": 5, "uniqueness": 6, "value_for_money": 7
            }
        },
        "queue_wait_minutes": 0,
        "corridor_tags": ["harborland"],
        "risk_flags": ["crowded on weekends and holidays"],
        "descriptions": {
            "why_selected": "神戸港に面した複合商業施設。MOSAICテラスからポートタワーと海景を同時に楽しめる定番スポット",
            "what_to_expect": "umie内での買い物・食事とMOSAIC前の海辺散策を組み合わせる。夕暮れ時の港の景色が特に美しい",
            "skip_if": "ショッピングモールに特に用がない方"
        }
    },
    "hyo_sum_museum": {
        "city_code": "kobe",
        "prefecture": "兵庫県",
        "address_ja": "兵庫県神戸市中央区京町24番地",
        "nearest_station": "地下鉄旧居留地・大丸前駅から徒歩約3分",
        "when": {
            "open_days": "火〜日曜日",
            "open_hours": "9:30-17:30",
            "last_entry": "17:00",
            "closed_notes": "月曜休館（祝日の場合は翌平日）、年末年始休館"
        },
        "cost": {"admission_jpy": 700, "typical_spend_jpy": 700, "budget_tier": "budget"},
        "review_signals": {
            "overall_score": 3.9,
            "review_count_approx": 2000,
            "dimension_scores": {
                "scenery": 7, "cultural_depth": 9, "accessibility": 9,
                "crowd_comfort": 9, "uniqueness": 7, "value_for_money": 7
            }
        },
        "queue_wait_minutes": 0,
        "corridor_tags": ["sannomiya"],
        "risk_flags": ["closed Mondays"],
        "descriptions": {
            "why_selected": "旧横浜正金銀行神戸支店の格調ある建物で、南蛮美術コレクションなど神戸の国際交流史を体感できる",
            "what_to_expect": "常設展示は神戸開港史と南蛮美術。外観建築が特に美しく旧居留地散策のアクセントに最適",
            "skip_if": "歴史・美術展示に興味がない方"
        }
    },
    "hyo_himeji_castle": {
        "city_code": "himeji",
        "prefecture": "兵庫県",
        "address_ja": "兵庫県姫路市本町68番地",
        "nearest_station": "JR姫路駅から徒歩約20分 / バス「大手門前」下車すぐ",
        "when": {
            "open_days": "毎日",
            "open_hours": "9:00-17:00（夏季は〜18:00）",
            "last_entry": "16:00（夏季17:00）",
            "closed_notes": "12月29日・30日は休城"
        },
        "cost": {"admission_jpy": 1000, "typical_spend_jpy": 1500, "budget_tier": "mid"},
        "review_signals": {
            "overall_score": 4.8,
            "review_count_approx": 50000,
            "dimension_scores": {
                "scenery": 10, "cultural_depth": 10, "accessibility": 8,
                "crowd_comfort": 4, "uniqueness": 10, "value_for_money": 9
            }
        },
        "queue_wait_minutes": 45,
        "corridor_tags": ["himeji_castle"],
        "risk_flags": ["peak spring 60min+ queue", "steep internal staircases", "shoes must be removable"],
        "descriptions": {
            "why_selected": "現存する日本最高峰の城郭建築。江戸時代の木造天守がほぼ原形のまま残る奇跡的な世界遺産・国宝",
            "what_to_expect": "天守内部6層を木造階段で登る。最上階から姫路市街を一望。春の桜シーズンは三之丸広場の1000本の桜が絶景",
            "skip_if": "狭い階段・高所が苦手な方（天守内は急勾配）"
        }
    },
    "hyo_kokoen": {
        "city_code": "himeji",
        "prefecture": "兵庫県",
        "address_ja": "兵庫県姫路市本町68番地（姫路城西御屋敷跡）",
        "nearest_station": "JR姫路駅から徒歩約25分（姫路城と同じアクセス）",
        "when": {
            "open_days": "毎日",
            "open_hours": "9:00-17:00（夏季〜18:00）",
            "last_entry": "16:30",
            "closed_notes": "12月29日・30日は休園"
        },
        "cost": {"admission_jpy": 310, "typical_spend_jpy": 800, "budget_tier": "budget"},
        "review_signals": {
            "overall_score": 4.3,
            "review_count_approx": 5000,
            "dimension_scores": {
                "scenery": 9, "cultural_depth": 8, "accessibility": 8,
                "crowd_comfort": 7, "uniqueness": 8, "value_for_money": 9
            }
        },
        "queue_wait_minutes": 5,
        "corridor_tags": ["himeji_castle"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "姫路城の堀跡に再現された江戸式回遊庭園9園。秋の紅葉と茶室での抹茶体験が姫路観光の奥行きを深める",
            "what_to_expect": "池泉・枯山水・茶庭など異なる様式の庭園を巡る。茶室で抹茶と和菓子（約500円）。姫路城との共通券がお得",
            "skip_if": "日本庭園に特に関心がない方、時間が限られている方"
        }
    },
    "hyo_shoshazan_engyo": {
        "city_code": "himeji",
        "prefecture": "兵庫県",
        "address_ja": "兵庫県姫路市書写2968番地",
        "nearest_station": "JR姫路駅からバス約30分「書写山ロープウェイ前」下車→ロープウェイ約4分",
        "when": {
            "open_days": "毎日",
            "open_hours": "8:30-18:00（ロープウェイ始発に準ずる）",
            "last_entry": "17:30",
            "closed_notes": "強風時はロープウェイ運休の場合あり"
        },
        "cost": {"admission_jpy": 1000, "typical_spend_jpy": 1500, "budget_tier": "mid"},
        "review_signals": {
            "overall_score": 4.5,
            "review_count_approx": 6000,
            "dimension_scores": {
                "scenery": 9, "cultural_depth": 10, "accessibility": 5,
                "crowd_comfort": 8, "uniqueness": 10, "value_for_money": 8
            }
        },
        "queue_wait_minutes": 10,
        "corridor_tags": ["shosha"],
        "risk_flags": ["ropeway may close in strong wind", "requires half-day time commitment"],
        "descriptions": {
            "why_selected": "海抜371mの深山に天台宗の大伽藍が広がる。『ラストサムライ』撮影地として世界的に知られ、姫路城と組み合わせた文化深度ルートの完成形",
            "what_to_expect": "ロープウェイで山上へ。摩尼殿・大講堂・常行堂など室町〜江戸時代の建物が山中に点在。静寂の森の中を1時間歩く",
            "skip_if": "時間が足りない方（姫路城と合わせると丸一日）、山道が苦手な方"
        }
    },
    "hyo_arima_kinsen": {
        "city_code": "arima",
        "prefecture": "兵庫県",
        "address_ja": "兵庫県神戸市北区有馬町833番地",
        "nearest_station": "神戸電鉄有馬温泉駅から徒歩約5分",
        "when": {
            "open_days": "毎日（第1・第3火曜休館）",
            "open_hours": "8:00-22:00",
            "last_entry": "21:30",
            "closed_notes": "第1・第3火曜日は休館（祝日の場合は翌日）"
        },
        "cost": {"admission_jpy": 800, "typical_spend_jpy": 1200, "budget_tier": "budget"},
        "review_signals": {
            "overall_score": 4.4,
            "review_count_approx": 8000,
            "dimension_scores": {
                "scenery": 7, "cultural_depth": 8, "accessibility": 8,
                "crowd_comfort": 5, "uniqueness": 10, "value_for_money": 9
            }
        },
        "queue_wait_minutes": 20,
        "corridor_tags": ["arima_town"],
        "risk_flags": ["small bathing area", "crowded on weekends", "closed 1st/3rd Tuesday"],
        "descriptions": {
            "why_selected": "日本最古の温泉地の一つ。鉄塩泉による茶褐色の湯は全国でも有馬でしか体験できない極めて希少な泉質",
            "what_to_expect": "茶褐色の金湯に浸かる約60分の体験。本物の天然温泉の迫力が味わえる",
            "skip_if": "入浴自体が目的でない方、人混みが苦手な週末訪問者"
        }
    },
    "hyo_arima_ginsen": {
        "city_code": "arima",
        "prefecture": "兵庫県",
        "address_ja": "兵庫県神戸市北区有馬町1039番地1",
        "nearest_station": "神戸電鉄有馬温泉駅から徒歩約7分",
        "when": {
            "open_days": "毎日（第2・第4火曜休館）",
            "open_hours": "9:00-21:00",
            "last_entry": "20:30",
            "closed_notes": "第2・第4火曜日は休館"
        },
        "cost": {"admission_jpy": 650, "typical_spend_jpy": 1000, "budget_tier": "budget"},
        "review_signals": {
            "overall_score": 4.1,
            "review_count_approx": 4000,
            "dimension_scores": {
                "scenery": 6, "cultural_depth": 7, "accessibility": 8,
                "crowd_comfort": 7, "uniqueness": 8, "value_for_money": 9
            }
        },
        "queue_wait_minutes": 10,
        "corridor_tags": ["arima_town"],
        "risk_flags": ["closed 2nd/4th Tuesday"],
        "descriptions": {
            "why_selected": "金湯とは対照的な無色透明の炭酸・放射能泉。2種類の異なる泉質をハシゴできるのが有馬温泉の唯一性",
            "what_to_expect": "金湯より広々とした浴室でゆったり入浴。セット券で金湯と合わせて入浴が割安",
            "skip_if": "時間がなく金湯だけに集中したい方"
        }
    },
    "hyo_arima_onsen_street": {
        "city_code": "arima",
        "prefecture": "兵庫県",
        "address_ja": "兵庫県神戸市北区有馬町（有馬温泉街全域）",
        "nearest_station": "神戸電鉄有馬温泉駅から徒歩すぐ",
        "when": {
            "open_days": "毎日",
            "open_hours": "終日散策可（各施設は異なる）",
            "last_entry": None,
            "closed_notes": None
        },
        "cost": {"admission_jpy": 0, "typical_spend_jpy": 2000, "budget_tier": "mid"},
        "review_signals": {
            "overall_score": 4.5,
            "review_count_approx": 12000,
            "dimension_scores": {
                "scenery": 8, "cultural_depth": 8, "accessibility": 8,
                "crowd_comfort": 5, "uniqueness": 9, "value_for_money": 8
            }
        },
        "queue_wait_minutes": 0,
        "corridor_tags": ["arima_town"],
        "risk_flags": ["weekend daytime very crowded", "parking limited"],
        "descriptions": {
            "why_selected": "神戸市街から30分で到達できる日本最古級の温泉街。入浴・土産物・炭酸せんべい・歴史散策をすべて半日で完結できる稀な目的地",
            "what_to_expect": "石畳の路地に旅館・土産店・外湯が並ぶ。有馬名物の炭酸せんべいや金泥絵馬は必ず立ち寄りたい",
            "skip_if": "温泉に入らず散策だけなら30分で完結。時間が余れば金湯入浴をプラス"
        }
    },
    "hyo_arima_onsenji": {
        "city_code": "arima",
        "prefecture": "兵庫県",
        "address_ja": "兵庫県神戸市北区有馬町1302番地",
        "nearest_station": "神戸電鉄有馬温泉駅から徒歩約8分",
        "when": {
            "open_days": "毎日",
            "open_hours": "8:00-17:00",
            "last_entry": None,
            "closed_notes": None
        },
        "cost": {"admission_jpy": 0, "typical_spend_jpy": 0, "budget_tier": "budget"},
        "review_signals": {
            "overall_score": 3.9,
            "review_count_approx": 1500,
            "dimension_scores": {
                "scenery": 7, "cultural_depth": 7, "accessibility": 7,
                "crowd_comfort": 9, "uniqueness": 6, "value_for_money": 10
            }
        },
        "queue_wait_minutes": 0,
        "corridor_tags": ["arima_town"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "行基創建の古刹で温泉街散策ルート上に自然に組み込まれる。太閤橋（豊臣秀吉ゆかり）とセットで有馬の歴史に深みを加える",
            "what_to_expect": "境内は小さく参拝は10〜20分。前の太閤橋での記念撮影がおすすめ",
            "skip_if": "有馬訪問時間が限られている方（金湯・銀湯・土産を優先）"
        }
    },
    "hyo_arima_nenrinya": {
        "city_code": "arima",
        "prefecture": "兵庫県",
        "address_ja": "兵庫県神戸市北区有馬町（湯山御殿跡・太閤の湯殿館周辺）",
        "nearest_station": "神戸電鉄有馬温泉駅から徒歩約6分",
        "when": {
            "open_days": "毎日（湯山御殿館は火曜休館）",
            "open_hours": "9:00-17:00",
            "last_entry": "16:30",
            "closed_notes": "火曜休館（祝日の場合翌日）"
        },
        "cost": {"admission_jpy": 0, "typical_spend_jpy": 0, "budget_tier": "budget"},
        "review_signals": {
            "overall_score": 3.7,
            "review_count_approx": 800,
            "dimension_scores": {
                "scenery": 6, "cultural_depth": 8, "accessibility": 7,
                "crowd_comfort": 10, "uniqueness": 8, "value_for_money": 10
            }
        },
        "queue_wait_minutes": 0,
        "corridor_tags": ["arima_town"],
        "risk_flags": ["closed Tuesdays"],
        "descriptions": {
            "why_selected": "豊臣秀吉の湯山御殿跡の発掘展示は無料。秀吉が有馬を愛した歴史的背景を実物遺構で体感できる",
            "what_to_expect": "太閤の湯殿館内で発掘された浴池遺構を見学。温泉街散策の途中に立ち寄る程度（15分）",
            "skip_if": "歴史に特に興味がない方"
        }
    },
    "hyo_kinosaki_nanatouyu": {
        "city_code": "kinosaki",
        "prefecture": "兵庫県",
        "address_ja": "兵庫県豊岡市城崎町湯島（城崎温泉各外湯）",
        "nearest_station": "JR城崎温泉駅から徒歩すぐ〜10分",
        "when": {
            "open_days": "毎日（各外湯により異なる）",
            "open_hours": "7:00-23:00（外湯ごとに異なる）",
            "last_entry": "22:30",
            "closed_notes": "各外湯は週1日程度休館（外湯ごとに異なる曜日）"
        },
        "cost": {"admission_jpy": 1500, "typical_spend_jpy": 2000, "budget_tier": "mid"},
        "review_signals": {
            "overall_score": 4.7,
            "review_count_approx": 15000,
            "dimension_scores": {
                "scenery": 9, "cultural_depth": 10, "accessibility": 8,
                "crowd_comfort": 6, "uniqueness": 10, "value_for_money": 9
            }
        },
        "queue_wait_minutes": 15,
        "corridor_tags": ["kinosaki_town"],
        "risk_flags": ["each bath has weekly closure day", "wooden sandals on cobblestones"],
        "descriptions": {
            "why_selected": "浴衣姿で柳並木の温泉街を歩きながら7つの外湯をめぐる体験は、日本の温泉文化の最も完全な形",
            "what_to_expect": "一日券で7浴場すべてに入浴可能。御所の湯（最豪華）・一の湯（洞窟風呂）・まんだら湯（最古）などそれぞれ個性的",
            "skip_if": "温泉が苦手な方、一か所でゆっくりしたい方（巡湯は体力を使う）"
        }
    },
    "hyo_kinosaki_onsen_street": {
        "city_code": "kinosaki",
        "prefecture": "兵庫県",
        "address_ja": "兵庫県豊岡市城崎町湯島（大谿川沿い温泉街）",
        "nearest_station": "JR城崎温泉駅から徒歩約3分",
        "when": {
            "open_days": "毎日",
            "open_hours": "終日（夜間も外湯営業中）",
            "last_entry": None,
            "closed_notes": None
        },
        "cost": {"admission_jpy": 0, "typical_spend_jpy": 2000, "budget_tier": "mid"},
        "review_signals": {
            "overall_score": 4.6,
            "review_count_approx": 10000,
            "dimension_scores": {
                "scenery": 10, "cultural_depth": 8, "accessibility": 9,
                "crowd_comfort": 6, "uniqueness": 10, "value_for_money": 9
            }
        },
        "queue_wait_minutes": 0,
        "corridor_tags": ["kinosaki_town"],
        "risk_flags": ["long travel time from Osaka/Kyoto (2.5hr+)"],
        "descriptions": {
            "why_selected": "大谿川沿いの柳並木・石橋・旅館・外湯が一体となった日本最美の温泉街。浴衣姿で歩く夜の景色は絵画のよう",
            "what_to_expect": "夕暮れ以降が最も美しい。街灯と浴衣客が溶け合う情景は一生の記憶になる。宿泊必須推奨",
            "skip_if": "交通時間（大阪から2.5〜3時間）の長さを許容できない方"
        }
    },
    "hyo_kinosaki_onsenji": {
        "city_code": "kinosaki",
        "prefecture": "兵庫県",
        "address_ja": "兵庫県豊岡市城崎町湯島985番地",
        "nearest_station": "JR城崎温泉駅から徒歩約10分（ロープウェイ山麓駅まで）",
        "when": {
            "open_days": "毎日",
            "open_hours": "9:00-17:00（ロープウェイ運行に準ずる）",
            "last_entry": "16:30",
            "closed_notes": "荒天時ロープウェイ運休あり"
        },
        "cost": {"admission_jpy": 300, "typical_spend_jpy": 2000, "budget_tier": "mid"},
        "review_signals": {
            "overall_score": 4.2,
            "review_count_approx": 3000,
            "dimension_scores": {
                "scenery": 9, "cultural_depth": 8, "accessibility": 6,
                "crowd_comfort": 8, "uniqueness": 8, "value_for_money": 7
            }
        },
        "queue_wait_minutes": 10,
        "corridor_tags": ["kinosaki_town"],
        "risk_flags": ["ropeway weather dependent"],
        "descriptions": {
            "why_selected": "城崎温泉の開創者・道智上人が開いた古刹。ロープウェイで山上へ登ると温泉街全景と日本海が広がる絶景ビューポイント",
            "what_to_expect": "ロープウェイ往復＋境内参拝＋展望台からの眺望で約1時間。秋の紅葉シーズンは特に美しい",
            "skip_if": "ロープウェイが苦手な方、時間が限られている方"
        }
    },
    "hyo_kinosaki_ropeway": {
        "city_code": "kinosaki",
        "prefecture": "兵庫県",
        "address_ja": "兵庫県豊岡市城崎町湯島（城崎ロープウェイ山麓駅）",
        "nearest_station": "JR城崎温泉駅から徒歩約10分",
        "when": {
            "open_days": "毎日（悪天候時運休）",
            "open_hours": "8:00-17:00（季節により変動）",
            "last_entry": "16:30",
            "closed_notes": "強風・大雪時は運休。定期点検日あり"
        },
        "cost": {"admission_jpy": 1400, "typical_spend_jpy": 1400, "budget_tier": "mid"},
        "review_signals": {
            "overall_score": 4.2,
            "review_count_approx": 3500,
            "dimension_scores": {
                "scenery": 9, "cultural_depth": 5, "accessibility": 6,
                "crowd_comfort": 8, "uniqueness": 7, "value_for_money": 7
            }
        },
        "queue_wait_minutes": 10,
        "corridor_tags": ["kinosaki_town"],
        "risk_flags": ["weather dependent", "check last car time carefully"],
        "descriptions": {
            "why_selected": "山頂から城崎温泉街全体と日本海を一望できる制高点。温泉寺参拝と組み合わせて城崎の立体的な景観を理解できる",
            "what_to_expect": "約6分の空中散歩。山頂にミニ動物園もあり子連れ旅行にも適している",
            "skip_if": "ロープウェイに追加費用を払いたくない方、晴天でない日（視界不良）"
        }
    },
    "hyo_kinosaki_kani": {
        "city_code": "kinosaki",
        "prefecture": "兵庫県",
        "address_ja": "兵庫県豊岡市城崎町（城崎温泉各旅館・料理店）",
        "nearest_station": "JR城崎温泉駅すぐ",
        "when": {
            "open_days": "11月6日〜3月20日（松葉ガニ漁期）",
            "open_hours": "旅館夕食は18:00〜",
            "last_entry": None,
            "closed_notes": "シーズン外（4月〜11月5日）は松葉ガニ提供なし"
        },
        "cost": {"admission_jpy": 0, "typical_spend_jpy": 40000, "budget_tier": "luxury"},
        "review_signals": {
            "overall_score": 4.8,
            "review_count_approx": 5000,
            "dimension_scores": {
                "scenery": 7, "cultural_depth": 8, "accessibility": 6,
                "crowd_comfort": 7, "uniqueness": 10, "value_for_money": 7
            }
        },
        "queue_wait_minutes": 0,
        "corridor_tags": ["kinosaki_town"],
        "risk_flags": ["seasonal only (Nov-Mar)", "must book 3-6 months ahead", "very expensive"],
        "descriptions": {
            "why_selected": "タグ付き但馬産松葉ガニは日本で最も希少なカニの一つ。刺身・焼き・カニ鍋の一杯フルコースは城崎でしか体験できない究極の冬グルメ",
            "what_to_expect": "旅館の夕食コース（3〜5万円/人）でフルコース。解禁日（11/6）前後の週末は最低半年前予約が必須",
            "skip_if": "シーズン外の訪問者、予算が限られている方"
        }
    },
    "hyo_naruto_awaji": {
        "city_code": "awaji",
        "prefecture": "兵庫県",
        "address_ja": "兵庫県南あわじ市福良丙（大鳴門橋・渦の道）",
        "nearest_station": "高速バス「道の駅うずしお」下車すぐ / 神戸三宮から高速バスで約1時間30分",
        "when": {
            "open_days": "毎日",
            "open_hours": "9:00-18:00（季節により変動）",
            "last_entry": "17:30",
            "closed_notes": "強風時は渦の道クローズあり"
        },
        "cost": {"admission_jpy": 510, "typical_spend_jpy": 2000, "budget_tier": "mid"},
        "review_signals": {
            "overall_score": 4.5,
            "review_count_approx": 12000,
            "dimension_scores": {
                "scenery": 10, "cultural_depth": 5, "accessibility": 6,
                "crowd_comfort": 6, "uniqueness": 10, "value_for_money": 8
            }
        },
        "queue_wait_minutes": 10,
        "corridor_tags": ["awaji_south"],
        "risk_flags": ["must check tidal schedule", "no vortex at wrong tide time"],
        "descriptions": {
            "why_selected": "世界三大潮流の一つ。最大直径30mにもなる鳴門の渦潮は自然が生み出す圧倒的スペクタクル",
            "what_to_expect": "渦の道（大鳴門橋上の遊歩道、ガラス床）から渦潮を直下に見下ろす。大潮期の満潮・干潮時刻前後2時間が最大の見頃",
            "skip_if": "潮時表を事前確認せずに行くと渦がほとんど見えないことも"
        }
    },
    "hyo_awaji_yumebutai": {
        "city_code": "awaji",
        "prefecture": "兵庫県",
        "address_ja": "兵庫県淡路市夢舞台2番地",
        "nearest_station": "高速バス「夢舞台」下車すぐ / 洲本バスセンターからバス約30分",
        "when": {
            "open_days": "毎日",
            "open_hours": "9:00-18:00（敷地内は自由散策）",
            "last_entry": None,
            "closed_notes": "ホテル・レストランは別途"
        },
        "cost": {"admission_jpy": 0, "typical_spend_jpy": 1500, "budget_tier": "mid"},
        "review_signals": {
            "overall_score": 4.4,
            "review_count_approx": 7000,
            "dimension_scores": {
                "scenery": 9, "cultural_depth": 8, "accessibility": 6,
                "crowd_comfort": 8, "uniqueness": 10, "value_for_money": 8
            }
        },
        "queue_wait_minutes": 0,
        "corridor_tags": ["awaji_north"],
        "risk_flags": ["car recommended for full access"],
        "descriptions": {
            "why_selected": "安藤忠雄の代表作。コンクリートの幾何学的空間と自然が融合した百段苑・貝の浜・円形広場は建築ファン必訪",
            "what_to_expect": "無料エリアを中心に約90分で巡れる。春は百段苑の花々、冬は雪景色と混雑が少ない季節が特に美しい",
            "skip_if": "建築・現代アートに興味がない方"
        }
    },
    "hyo_awaji_akashi_bridge": {
        "city_code": "awaji",
        "prefecture": "兵庫県",
        "address_ja": "兵庫県淡路市岩屋（淡路側）/ 兵庫県神戸市垂水区舞子台4丁目（舞子公園側）",
        "nearest_station": "JR舞子駅から徒歩約5分（舞子公園側）/ 高速バス「淡路IC」下車",
        "when": {
            "open_days": "毎日",
            "open_hours": "橋科学館9:00-18:00（季節変動）",
            "last_entry": "17:30",
            "closed_notes": "月曜休館（橋科学館）"
        },
        "cost": {"admission_jpy": 310, "typical_spend_jpy": 500, "budget_tier": "budget"},
        "review_signals": {
            "overall_score": 4.1,
            "review_count_approx": 5000,
            "dimension_scores": {
                "scenery": 9, "cultural_depth": 5, "accessibility": 8,
                "crowd_comfort": 7, "uniqueness": 8, "value_for_money": 8
            }
        },
        "queue_wait_minutes": 5,
        "corridor_tags": ["awaji_north"],
        "risk_flags": ["bridge tower tour requires separate booking"],
        "descriptions": {
            "why_selected": "全長3911mの世界最長吊り橋。海面89mの主塔展望台から明石海峡・淡路島・神戸を一望できる",
            "what_to_expect": "舞子公園内の橋科学館と展望台を合わせて約1時間。橋の巨大さに圧倒される",
            "skip_if": "橋・土木工学に特に興味がない方（外観を車窓から眺めるだけでも十分な場合も）"
        }
    },
    "hyo_awaji_onion": {
        "city_code": "awaji",
        "prefecture": "兵庫県",
        "address_ja": "兵庫県淡路市（道の駅あわじ・各飲食店）",
        "nearest_station": "高速バス「淡路IC」下車後タクシー / 道の駅あわじは淡路ICすぐ",
        "when": {
            "open_days": "毎日",
            "open_hours": "9:00-18:00（道の駅）",
            "last_entry": None,
            "closed_notes": None
        },
        "cost": {"admission_jpy": 0, "typical_spend_jpy": 1500, "budget_tier": "budget"},
        "review_signals": {
            "overall_score": 4.0,
            "review_count_approx": 3000,
            "dimension_scores": {
                "scenery": 5, "cultural_depth": 5, "accessibility": 7,
                "crowd_comfort": 7, "uniqueness": 7, "value_for_money": 9
            }
        },
        "queue_wait_minutes": 10,
        "corridor_tags": ["awaji_north"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "淡路島産玉ねぎは日本最高品質の産地ブランド。道の駅での購入・その場で食べる玉ねぎバーガーは淡路観光のグルメ定番",
            "what_to_expect": "道の駅あわじや淡路SAで玉ねぎ丸ごとスープ・玉ねぎバーガーなどを試食・購入。淡路島ドライブ旅に自然に組み込める",
            "skip_if": "食への興味が薄い方、玉ねぎ料理だけのために移動するには弱い"
        }
    },
    "hyo_sumoto_onsen": {
        "city_code": "awaji",
        "prefecture": "兵庫県",
        "address_ja": "兵庫県洲本市小路谷（洲本温泉エリア）",
        "nearest_station": "高速バス「洲本バスセンター」から徒歩〜タクシー約10分",
        "when": {
            "open_days": "毎日（旅館宿泊または日帰り入浴）",
            "open_hours": "チェックイン15:00〜チェックアウト11:00（宿泊の場合）",
            "last_entry": None,
            "closed_notes": "日帰り温泉は要事前確認"
        },
        "cost": {"admission_jpy": 0, "typical_spend_jpy": 20000, "budget_tier": "luxury"},
        "review_signals": {
            "overall_score": 4.3,
            "review_count_approx": 2500,
            "dimension_scores": {
                "scenery": 9, "cultural_depth": 5, "accessibility": 5,
                "crowd_comfort": 8, "uniqueness": 7, "value_for_money": 7
            }
        },
        "queue_wait_minutes": 0,
        "corridor_tags": ["awaji_south"],
        "risk_flags": ["car almost essential", "reservation required"],
        "descriptions": {
            "why_selected": "大阪湾に向かって開けた海景温泉。夕暮れ時の海を眺めながら温泉に浸かる体験は淡路島宿泊の最大の魅力",
            "what_to_expect": "旅館に1泊し、夕食・朝食・露天風呂をセットで楽しむ。洲本城跡との組み合わせが定番",
            "skip_if": "淡路島で宿泊せずに日帰りの方、自動車なしで来島が難しい方"
        }
    },
    "hyo_awaji_engpark": {
        "city_code": "awaji",
        "prefecture": "兵庫県",
        "address_ja": "兵庫県淡路市夢舞台8番地（国営明石海峡公園淡路地区）",
        "nearest_station": "高速バス「夢舞台」下車徒歩約5分",
        "when": {
            "open_days": "毎日（火曜定休あり）",
            "open_hours": "9:30-17:00（季節により延長）",
            "last_entry": "16:30",
            "closed_notes": "火曜休園（繁忙期を除く）、年末年始休園"
        },
        "cost": {"admission_jpy": 450, "typical_spend_jpy": 800, "budget_tier": "budget"},
        "review_signals": {
            "overall_score": 4.2,
            "review_count_approx": 4000,
            "dimension_scores": {
                "scenery": 9, "cultural_depth": 4, "accessibility": 7,
                "crowd_comfort": 7, "uniqueness": 7, "value_for_money": 8
            }
        },
        "queue_wait_minutes": 0,
        "corridor_tags": ["awaji_north"],
        "risk_flags": ["closed Tuesdays", "large area - bike rental recommended"],
        "descriptions": {
            "why_selected": "2000年淡路花博の跡地を活用した国営公園。春のチューリップと秋のコスモスが特に有名な大規模花卉公園",
            "what_to_expect": "広大な敷地を自転車でめぐりながら花畑を鑑賞。夢舞台と組み合わせた半日コースが定番",
            "skip_if": "花・ガーデニングに特に興味がない方"
        }
    },
    "hyg_nada_sake": {
        "city_code": "kobe",
        "prefecture": "兵庫県",
        "address_ja": "兵庫県神戸市灘区御影本町〜西郷（灘五郷酒蔵エリア）",
        "nearest_station": "阪神御影駅・魚崎駅周辺 / JR住吉駅から徒歩圏内",
        "when": {
            "open_days": "毎日（各蔵により異なる）",
            "open_hours": "10:00-16:30（各蔵により異なる）",
            "last_entry": "16:00",
            "closed_notes": "年末年始休館あり、蔵ごとに休館日異なる"
        },
        "cost": {"admission_jpy": 0, "typical_spend_jpy": 1000, "budget_tier": "budget"},
        "review_signals": {
            "overall_score": 4.1,
            "review_count_approx": 5000,
            "dimension_scores": {
                "scenery": 6, "cultural_depth": 9, "accessibility": 7,
                "crowd_comfort": 8, "uniqueness": 8, "value_for_money": 10
            }
        },
        "queue_wait_minutes": 0,
        "corridor_tags": ["nada"],
        "risk_flags": ["do not drive after tasting"],
        "descriptions": {
            "why_selected": "日本最大の清酒産地・灘五郷の百年酒蔵を無料見学・試飲。白鶴・菊正宗・沢の鶴など国産日本酒ファン必訪",
            "what_to_expect": "酒蔵の製造工程展示→試飲（複数銘柄）→土産購入。白鶴酒造資料館・菊正宗酒造記念館が特に設備充実",
            "skip_if": "お酒が飲めない方、または神戸市内中心部から移動時間が惜しい方"
        }
    },
    "hyg_earthquake_museum": {
        "city_code": "kobe",
        "prefecture": "兵庫県",
        "address_ja": "兵庫県神戸市中央区脇浜海岸通1丁目5番2号",
        "nearest_station": "阪神岩屋駅から徒歩約5分 / JR灘駅から徒歩約10分",
        "when": {
            "open_days": "火〜日曜",
            "open_hours": "9:30-17:30（金・土は〜19:00）",
            "last_entry": "17:00",
            "closed_notes": "月曜休館（祝日の場合翌平日）、1月17日は特別開館"
        },
        "cost": {"admission_jpy": 600, "typical_spend_jpy": 600, "budget_tier": "budget"},
        "review_signals": {
            "overall_score": 4.3,
            "review_count_approx": 6000,
            "dimension_scores": {
                "scenery": 4, "cultural_depth": 10, "accessibility": 7,
                "crowd_comfort": 8, "uniqueness": 9, "value_for_money": 9
            }
        },
        "queue_wait_minutes": 0,
        "corridor_tags": ["nada"],
        "risk_flags": ["emotionally heavy content", "closed Mondays"],
        "descriptions": {
            "why_selected": "1995年阪神淡路大震災を後世に伝える沈浸型施設。「1.17体験シアター」の疑似地震体験と被災映像は訪問者の心に深く刻まれる",
            "what_to_expect": "1階の震災体験シアター（迫力の映像・音響・振動）から2〜3階の展示へ。日本の防災文化を深く理解できる約1時間",
            "skip_if": "地震・災害関連のコンテンツが精神的につらい方"
        }
    }
}

# ─── Seasonal event enrichment ────────────────────────────────────────────────
event_enrichment = {
    "hyo_kobe_luminarie": {
        "city_code": "kobe",
        "prefecture": "兵庫県",
        "corridor_tags": ["sannomiya"],
        "cost": {"admission_jpy": 0, "typical_spend_jpy": 500, "budget_tier": "budget"},
        "descriptions": {
            "why_selected": "1995年阪神大震災の犠牲者を追悼する光の祭典。毎年約300万人が訪れる日本屈指の冬季イルミネーションイベント",
            "what_to_expect": "イタリア製の金属彩灯が旧居留地に幻想的な光の回廊を作る。開催約10日間。最終週末は特に混雑",
            "skip_if": "12月以外の訪問者。混雑が苦手な方（最終週末は数十万人規模）"
        }
    },
    "hyo_himeji_sakura": {
        "city_code": "himeji",
        "prefecture": "兵庫県",
        "corridor_tags": ["himeji_castle"],
        "cost": {"admission_jpy": 1000, "typical_spend_jpy": 2000, "budget_tier": "mid"},
        "descriptions": {
            "why_selected": "白鷺城と1000本の染井吉野の組み合わせは日本の城郭桜景の最高峰。世界中の旅行者が訪れる春の絶景",
            "what_to_expect": "三之丸広場で桜の下でのピクニック、夜桜ライトアップ（日没〜21時頃）。開花期間中は混雑必至で早朝訪問推奨",
            "skip_if": "花粉症がひどい方、混雑が絶対に苦手な方"
        }
    },
    "hyo_arima_autumn_festival": {
        "city_code": "arima",
        "prefecture": "兵庫県",
        "corridor_tags": ["arima_town"],
        "cost": {"admission_jpy": 0, "typical_spend_jpy": 3000, "budget_tier": "mid"},
        "descriptions": {
            "why_selected": "紅葉シーズンの有馬温泉街が地元の秋祭りで彩られる。湯泉神社の神楽奉納と提灯行列が日本の温泉情緒を高める",
            "what_to_expect": "紅葉＋祭り＋温泉の三位一体体験。具体日程は毎年公式サイトで確認が必要",
            "skip_if": "秋以外の訪問者"
        }
    },
    "hyo_kinosaki_kani_season": {
        "city_code": "kinosaki",
        "prefecture": "兵庫県",
        "corridor_tags": ["kinosaki_town"],
        "cost": {"admission_jpy": 0, "typical_spend_jpy": 40000, "budget_tier": "luxury"},
        "descriptions": {
            "why_selected": "日本海産松葉ガニの解禁は城崎温泉旅館業界最大のイベント。タグ付き但馬港捕獲蟹は日本で最も価値の高い食材の一つ",
            "what_to_expect": "解禁日（11/6）は全国から食通が押し寄せる。旅館の蟹フルコースディナーは刺身・焼き・鍋・雑炊まで一匹丸ごと堪能",
            "skip_if": "11月6日〜3月20日以外の訪問者、予算が限られている方"
        }
    },
    "hyo_kobe_sakura": {
        "city_code": "kobe",
        "prefecture": "兵庫県",
        "corridor_tags": ["rokko", "sannomiya"],
        "cost": {"admission_jpy": 0, "typical_spend_jpy": 1000, "budget_tier": "budget"},
        "descriptions": {
            "why_selected": "神戸市内に複数の桜名所が点在。須磨浦公園はロープウェイからの大阪湾×桜の絶景が特に独自性が高い",
            "what_to_expect": "王子公園（約2000本）・生田川公園（市中心徒歩圏）・須磨浦公園（海+山+桜）を好みで選択",
            "skip_if": "姫路城桜を既に予定している場合は重複感あり"
        }
    },
    "hyo_awaji_flower_expo": {
        "city_code": "awaji",
        "prefecture": "兵庫県",
        "corridor_tags": ["awaji_north"],
        "cost": {"admission_jpy": 450, "typical_spend_jpy": 1500, "budget_tier": "budget"},
        "descriptions": {
            "why_selected": "2000年淡路花博の舞台で毎春開催される大規模フラワーフェスタ。チューリップ→ラベンダー→バラの順に圧巻の花景色が続く",
            "what_to_expect": "国営明石海峡公園と淡路花博記念公園パルシェが中心会場。自転車でめぐるのが最も効率的",
            "skip_if": "花・ガーデニングに興味がない方"
        }
    },
    "hyo_kobe_jazz": {
        "city_code": "kobe",
        "prefecture": "兵庫県",
        "corridor_tags": ["kitano", "sannomiya"],
        "cost": {"admission_jpy": 0, "typical_spend_jpy": 2000, "budget_tier": "budget"},
        "descriptions": {
            "why_selected": "1981年から続く神戸を代表する音楽イベント。港町神戸とジャズは文化的に深く結びついており、北野異人館街区全体が会場に変わる",
            "what_to_expect": "北野・旧居留地エリアの100以上の会場で無料演奏が繰り広げられる2日間。秋の神戸観光と完璧に組み合わさる",
            "skip_if": "10月上旬以外の訪問者"
        }
    },
    "hyo_rokko_autumn_leaves": {
        "city_code": "kobe",
        "prefecture": "兵庫県",
        "corridor_tags": ["rokko", "arima_town"],
        "cost": {"admission_jpy": 0, "typical_spend_jpy": 3000, "budget_tier": "mid"},
        "descriptions": {
            "why_selected": "標高931mの六甲山は市内より2〜3週間早く紅葉が始まる。六甲〜有馬のロープウェイを使えば紅葉＋温泉を1日で完結できる",
            "what_to_expect": "六甲ガーデンテラスや記念碑台周辺の紅葉が最も見事。六甲有馬ロープウェイで有馬温泉に下りる黄金ルートが人気",
            "skip_if": "11月以外の訪問者"
        }
    }
}

# ─── Apply to spots ────────────────────────────────────────────────────────────
spots_updated = 0
missing_spots = []
for spot in data["spots"]:
    sid = spot["id"]
    if sid in spot_enrichment:
        e = spot_enrichment[sid]
        spot["city_code"] = e["city_code"]
        spot["prefecture"] = e["prefecture"]
        spot["address_ja"] = e["address_ja"]
        spot["nearest_station"] = e["nearest_station"]
        spot["when"] = e["when"]
        spot["cost"] = e["cost"]
        spot["review_signals"] = e["review_signals"]
        spot["queue_wait_minutes"] = e["queue_wait_minutes"]
        spot["corridor_tags"] = e["corridor_tags"]
        spot["risk_flags"] = e["risk_flags"]
        spot["descriptions"] = e["descriptions"]
        spots_updated += 1
    else:
        missing_spots.append(sid)

# ─── Apply to seasonal_events ──────────────────────────────────────────────────
events_updated = 0
missing_events = []
for event in data["seasonal_events"]:
    eid = event["id"]
    if eid in event_enrichment:
        e = event_enrichment[eid]
        event["city_code"] = e["city_code"]
        event["prefecture"] = e["prefecture"]
        event["corridor_tags"] = e["corridor_tags"]
        event["cost"] = e["cost"]
        event["descriptions"] = e["descriptions"]
        events_updated += 1
    else:
        missing_events.append(eid)

# ─── Write ─────────────────────────────────────────────────────────────────────
with open(SRC, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Spots enriched:  {spots_updated}/{len(data['spots'])}")
print(f"Events enriched: {events_updated}/{len(data['seasonal_events'])}")
if missing_spots:
    print("MISSING spots:", missing_spots)
if missing_events:
    print("MISSING events:", missing_events)
