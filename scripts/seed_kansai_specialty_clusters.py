# -*- coding: utf-8 -*-
"""
seed_kansai_specialty_clusters.py
专属骨架 cluster 补充：摄影/季节线、亲子、纯美食、小众建筑。
幂等：ON CONFLICT DO NOTHING
"""

import asyncio, sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.db.session import AsyncSessionLocal
from sqlalchemy import text

CLUSTERS = [
    # ── 摄影/季节 ───────────────────────────────────────────────
    {"cluster_id":"kyo_sakura_photo_circuit","circle_id":"kansai_classic_circle","name_zh":"京都樱花摄影深度线","name_en":"Kyoto Sakura Photography Circuit","primary_corridor":"philosopher_path","level":"A","default_selected":False,"profile_fit":["photo","sakura","couple","solo","nature"],"must_have_tags":["photo","sakura"],"capacity_units":1.0,"core_visit_minutes":240,"queue_buffer_minutes":30,"photo_buffer_minutes":90,"meal_break_minutes":60,"transit_minutes":45,"slack_minutes":30,"fatigue_weight":0.8,"season_fit":["spring"],"day_type_hint":"normal","typical_start_time":"06:30","description_zh":"哲学之道→南禅寺→平安神宫→圆山公园，涵盖京都最密集的樱花点，晨光拍摄最佳"},
    {"cluster_id":"kyo_night_sakura_gion","circle_id":"kansai_classic_circle","name_zh":"祇园夜樱·白川运河","name_en":"Gion Night Sakura","primary_corridor":"gion","level":"A","default_selected":False,"profile_fit":["photo","sakura","couple","romantic","night"],"must_have_tags":["photo","sakura"],"capacity_units":0.5,"core_visit_minutes":120,"queue_buffer_minutes":10,"photo_buffer_minutes":60,"meal_break_minutes":0,"transit_minutes":20,"slack_minutes":20,"fatigue_weight":0.4,"season_fit":["spring"],"day_type_hint":"half_day_pm","typical_start_time":"18:30","description_zh":"白川水路·巽桥夜樱倒影，花见小路灯笼照明"},
    {"cluster_id":"kyo_daigo_sakura","circle_id":"kansai_classic_circle","name_zh":"醍醐寺·丰臣秀吉花见之地","name_en":"Daigoji Temple Sakura","primary_corridor":"daigo","level":"A","default_selected":False,"profile_fit":["photo","sakura","history","culture","solo"],"must_have_tags":["sakura"],"capacity_units":1.0,"core_visit_minutes":180,"queue_buffer_minutes":40,"photo_buffer_minutes":60,"meal_break_minutes":60,"transit_minutes":50,"slack_minutes":30,"fatigue_weight":0.9,"season_fit":["spring"],"day_type_hint":"normal","typical_start_time":"09:00","description_zh":"世界遗产，400棵染井吉野，丰太阁花见遗址"},
    {"cluster_id":"kyo_autumn_foliage_circuit","circle_id":"kansai_classic_circle","name_zh":"京都红叶深度摄影线","name_en":"Kyoto Autumn Foliage Photo Circuit","primary_corridor":"higashiyama","level":"A","default_selected":False,"profile_fit":["photo","autumn","foliage","solo","couple","nature"],"must_have_tags":["photo","autumn"],"capacity_units":1.0,"core_visit_minutes":270,"queue_buffer_minutes":60,"photo_buffer_minutes":90,"meal_break_minutes":60,"transit_minutes":50,"slack_minutes":30,"fatigue_weight":1.0,"season_fit":["autumn"],"day_type_hint":"normal","typical_start_time":"07:00","description_zh":"永观堂→真如堂→南禅寺→哲学之道，京都红叶最密集走廊"},
    {"cluster_id":"kyo_wisteria_byodoin","circle_id":"kansai_classic_circle","name_zh":"宇治·藤花·平等院","name_en":"Uji Wisteria Byodoin","primary_corridor":"uji","level":"B","default_selected":False,"profile_fit":["photo","wisteria","couple","nature","culture"],"must_have_tags":["photo"],"capacity_units":1.0,"core_visit_minutes":180,"queue_buffer_minutes":30,"photo_buffer_minutes":60,"meal_break_minutes":60,"transit_minutes":40,"slack_minutes":30,"fatigue_weight":0.7,"season_fit":["spring"],"day_type_hint":"normal","typical_start_time":"09:00","description_zh":"平等院藤花盥洗，4-5月顶期"},
    # ── 建筑/庭园 ───────────────────────────────────────────────
    {"cluster_id":"kyo_ando_architecture","circle_id":"kansai_classic_circle","name_zh":"安藤忠雄关西建筑巡礼","name_en":"Tadao Ando Architecture Trail","primary_corridor":"nishikyo","level":"B","default_selected":False,"profile_fit":["architecture","solo","design","photo"],"must_have_tags":["architecture"],"capacity_units":1.0,"core_visit_minutes":240,"queue_buffer_minutes":20,"photo_buffer_minutes":60,"meal_break_minutes":60,"transit_minutes":90,"slack_minutes":30,"fatigue_weight":0.8,"season_fit":["all"],"day_type_hint":"normal","typical_start_time":"09:30","description_zh":"大山崎山庄美术馆（安藤新馆）→光之教堂，混凝土诗学"},
    {"cluster_id":"miho_museum_day_trip","circle_id":"kansai_classic_circle","name_zh":"MIHO MUSEUM·深山美术馆","name_en":"MIHO Museum Day Trip","primary_corridor":"shiga","level":"B","default_selected":False,"profile_fit":["architecture","design","solo","couple","art"],"must_have_tags":["architecture"],"capacity_units":1.0,"core_visit_minutes":240,"queue_buffer_minutes":15,"photo_buffer_minutes":45,"meal_break_minutes":60,"transit_minutes":90,"slack_minutes":45,"fatigue_weight":0.9,"season_fit":["all"],"day_type_hint":"normal","typical_start_time":"09:00","description_zh":"贝聿铭设计，藏于信乐深山，馆藏丝绸之路古物"},
    {"cluster_id":"kyo_daitokuji_zen_complex","circle_id":"kansai_classic_circle","name_zh":"大德寺·枯山水握紧ศ","name_en":"Daitokuji Zen Temple Complex","primary_corridor":"kita_ku","level":"A","default_selected":False,"profile_fit":["architecture","zen","culture","solo","photo"],"must_have_tags":["zen"],"capacity_units":1.0,"core_visit_minutes":210,"queue_buffer_minutes":15,"photo_buffer_minutes":60,"meal_break_minutes":60,"transit_minutes":35,"slack_minutes":30,"fatigue_weight":0.7,"season_fit":["all"],"day_type_hint":"normal","typical_start_time":"09:00","description_zh":"大仙院·瑞峯院·龙源院，22座塔头，枯山水最高密度"},
    {"cluster_id":"kyo_garden_imperial_circuit","circle_id":"kansai_classic_circle","name_zh":"京都御所·仙洞御所庭园线","name_en":"Imperial Gardens Circuit","primary_corridor":"gosho","level":"B","default_selected":False,"profile_fit":["architecture","culture","history","garden","solo"],"must_have_tags":["architecture","culture"],"capacity_units":0.5,"core_visit_minutes":150,"queue_buffer_minutes":30,"photo_buffer_minutes":30,"meal_break_minutes":0,"transit_minutes":25,"slack_minutes":20,"fatigue_weight":0.5,"season_fit":["spring","autumn"],"day_type_hint":"half_day","typical_start_time":"10:00","description_zh":"京都御所免费参观→仙洞御所庭园，皇家禁苑级苔藓与石组"},
    # ── 亲子 ────────────────────────────────────────────────────
    {"cluster_id":"nara_family_deer_park","circle_id":"kansai_classic_circle","name_zh":"奈良亲子·喂鹿+东大寺","name_en":"Nara Family Deer Todaiji","primary_corridor":"nara_park","level":"A","default_selected":False,"profile_fit":["family_child","nature","couple","first_timer"],"must_have_tags":["family_child"],"capacity_units":1.0,"core_visit_minutes":180,"queue_buffer_minutes":30,"photo_buffer_minutes":60,"meal_break_minutes":90,"transit_minutes":60,"slack_minutes":45,"fatigue_weight":0.7,"season_fit":["all"],"day_type_hint":"normal","typical_start_time":"09:30","description_zh":"奈良公园喂鹿→东大寺大佛殿，平坦路线适合儿童"},
    {"cluster_id":"osa_kids_science_circuit","circle_id":"kansai_classic_circle","name_zh":"大阪亲子科学日","name_en":"Osaka Kids Science Day","primary_corridor":"osa_nakanoshima","level":"B","default_selected":False,"profile_fit":["family_child","education","indoor"],"must_have_tags":["family_child"],"capacity_units":1.0,"core_visit_minutes":210,"queue_buffer_minutes":45,"photo_buffer_minutes":20,"meal_break_minutes":60,"transit_minutes":30,"slack_minutes":45,"fatigue_weight":0.6,"season_fit":["all"],"day_type_hint":"normal","typical_start_time":"10:00","description_zh":"大阪科学馆→自然史博物馆，室内为主，雨天备选"},
    # ── 纯美食 ──────────────────────────────────────────────────
    {"cluster_id":"kyo_nishiki_gourmet","circle_id":"kansai_classic_circle","name_zh":"锦市场·京都饮食文化半日线","name_en":"Nishiki Market Food Culture","primary_corridor":"kawaramachi","level":"A","default_selected":False,"profile_fit":["food","gourmet","couple","solo","culture"],"must_have_tags":["food"],"capacity_units":0.5,"core_visit_minutes":120,"queue_buffer_minutes":20,"photo_buffer_minutes":30,"meal_break_minutes":90,"transit_minutes":20,"slack_minutes":20,"fatigue_weight":0.4,"season_fit":["all"],"day_type_hint":"half_day","typical_start_time":"10:30","description_zh":"锦市场边走边吃→寺町商店街，京都饮食DNA最密集街道"},
    {"cluster_id":"osa_ramen_street_food","circle_id":"kansai_classic_circle","name_zh":"大阪拉面街道美食巡游","name_en":"Osaka Ramen Street Food","primary_corridor":"namba","level":"B","default_selected":False,"profile_fit":["food","ramen","friends","solo","budget"],"must_have_tags":["food"],"capacity_units":0.5,"core_visit_minutes":90,"queue_buffer_minutes":60,"photo_buffer_minutes":20,"meal_break_minutes":120,"transit_minutes":20,"slack_minutes":20,"fatigue_weight":0.3,"season_fit":["all"],"day_type_hint":"half_day_pm","typical_start_time":"18:00","description_zh":"难波拉面激战区→黑门市场夜市"},
    {"cluster_id":"kyo_kaiseki_gion_evening","circle_id":"kansai_classic_circle","name_zh":"祇园·怀石料理·花街晚宴","name_en":"Gion Kaiseki Evening","primary_corridor":"gion","level":"B","default_selected":False,"profile_fit":["food","gourmet","couple","luxury","romantic"],"must_have_tags":["food","gourmet"],"capacity_units":0.5,"core_visit_minutes":60,"queue_buffer_minutes":0,"photo_buffer_minutes":30,"meal_break_minutes":150,"transit_minutes":15,"slack_minutes":15,"fatigue_weight":0.3,"season_fit":["all"],"day_type_hint":"half_day_pm","typical_start_time":"17:30","description_zh":"祇园花见小路怀石料理晚宴→白川夜散步"},
    # ── 小众 ────────────────────────────────────────────────────
    {"cluster_id":"kyo_fushimi_momoyama_history","circle_id":"kansai_classic_circle","name_zh":"伏见·桃山历史线（非稻荷）","name_en":"Fushimi Momoyama History","primary_corridor":"fushimi","level":"B","default_selected":False,"profile_fit":["history","culture","solo","niche","sake"],"must_have_tags":["history"],"capacity_units":1.0,"core_visit_minutes":180,"queue_buffer_minutes":10,"photo_buffer_minutes":40,"meal_break_minutes":60,"transit_minutes":35,"slack_minutes":30,"fatigue_weight":0.6,"season_fit":["all"],"day_type_hint":"normal","typical_start_time":"10:00","description_zh":"伏见桃山城→寺田屋→月桂冠酒藏，完全避开稻荷拥挤人群"},
    {"cluster_id":"kyo_upper_arashiyama_niche","circle_id":"kansai_classic_circle","name_zh":"岚山·清凉寺·二尊院深处线","name_en":"Upper Arashiyama Hidden Temples","primary_corridor":"arashiyama","level":"B","default_selected":False,"profile_fit":["niche","culture","solo","nature","photo"],"must_have_tags":["niche"],"capacity_units":1.0,"core_visit_minutes":210,"queue_buffer_minutes":5,"photo_buffer_minutes":60,"meal_break_minutes":60,"transit_minutes":30,"slack_minutes":30,"fatigue_weight":0.7,"season_fit":["all"],"day_type_hint":"normal","typical_start_time":"08:30","description_zh":"二尊院→祇王寺（苔藓庭园）→清凉寺，岚山人流不到主线1/5"},
    {"cluster_id":"osa_tsuruhashi_korea_town","circle_id":"kansai_classic_circle","name_zh":"鹤桥·在日韩国城美食线","name_en":"Tsuruhashi Korea Town Food","primary_corridor":"tsuruhashi","level":"C","default_selected":False,"profile_fit":["food","niche","solo","friends","budget"],"must_have_tags":["food","niche"],"capacity_units":0.5,"core_visit_minutes":60,"queue_buffer_minutes":15,"photo_buffer_minutes":20,"meal_break_minutes":90,"transit_minutes":20,"slack_minutes":15,"fatigue_weight":0.3,"season_fit":["all"],"day_type_hint":"half_day","typical_start_time":"11:00","description_zh":"日本最大韩国城，烤肉·拌饭·泡菜市场"},
]

INSERT_SQL = text("""
INSERT INTO activity_clusters (
    cluster_id, circle_id, name_zh, name_en,
    primary_corridor, level, default_selected, profile_fit,
    must_have_tags, capacity_units,
    core_visit_minutes, queue_buffer_minutes, photo_buffer_minutes,
    meal_break_minutes, transit_minutes, slack_minutes, fatigue_weight,
    season_fit, day_type_hint, typical_start_time, description_zh,
    is_active,
    seasonality, default_duration, trip_role, can_drive_hotel,
    time_window_strength, reservation_pressure, secondary_attach_capacity
) VALUES (
    :cluster_id, :circle_id, :name_zh, :name_en,
    :primary_corridor, :level, :default_selected, :profile_fit,
    :must_have_tags, :capacity_units,
    :core_visit_minutes, :queue_buffer_minutes, :photo_buffer_minutes,
    :meal_break_minutes, :transit_minutes, :slack_minutes, :fatigue_weight,
    :season_fit, :day_type_hint, :typical_start_time, :description_zh,
    true,
    '["all_year"]'::jsonb, 'full_day', 'major', false,
    'flexible', 'low', 2
)
ON CONFLICT (cluster_id) DO NOTHING
""")

async def main():
    async with AsyncSessionLocal() as s:
        new_c = skip_c = 0
        for c in CLUSTERS:
            params = dict(c)
            for k in ("profile_fit", "must_have_tags", "season_fit"):
                if isinstance(params.get(k), list):
                    params[k] = json.dumps(params[k], ensure_ascii=False)
            r = await s.execute(INSERT_SQL, params)
            if r.rowcount:
                new_c += 1
                print(f"  NEW  {c['cluster_id']}")
            else:
                skip_c += 1
                print(f"  SKIP {c['cluster_id']}")
        await s.commit()
    print(f"done: {new_c} NEW / {skip_c} SKIP")

if __name__ == "__main__":
    asyncio.run(main())