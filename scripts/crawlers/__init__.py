"""
通用爬虫框架 (Universal Crawler Toolkit)
=========================================
可跨项目复用的异步爬虫工具包。

模块：
  base.py      — BaseCrawler：会话管理/反爬/限速/重试/代理
  tabelog.py   — TabelogCrawler：Tabelog 列表页+详情页采集
  exporters.py — 数据导出（JSON / CSV / DB）

用法：
  # CLI 一键爬取
  python scripts/tabelog_crawl.py --city tokyo --cuisine sushi --pages 3

  # 代码调用
  from scripts.crawlers.tabelog import TabelogCrawler
  async with TabelogCrawler() as crawler:
      data = await crawler.crawl_city("tokyo", cuisines=["sushi", "ramen"])
"""
