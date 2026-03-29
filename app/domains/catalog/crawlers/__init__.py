"""
数据采集爬虫模块

数据源优先级：
  日本: Google Places → OSM/Tabelog → AI fallback
  中国: 携程/大众点评 → 高德 → AI fallback

所有爬虫输出统一格式，兼容 upsert_entity() 字段白名单。
"""
