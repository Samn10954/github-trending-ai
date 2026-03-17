# GitHub Trending AI 每日精选

每天自动收集 GitHub Trending 中与 AI、具身智能相关的开源项目，并生成可按日期浏览、按标签筛选、按周期切换的静态网页。

## 当前能力

- 支持 **daily / weekly / monthly** 三套榜单
- 支持 **按日期查看** 历史结果
- 支持 **标签筛选**、**排序**、**收藏**
- 支持 **项目级趋势图**（查看同一项目在历史日期中的变化）
- 趋势图支持切换指标：**周期新增 / 总 Stars**
- 支持基础的 **收藏页**：`favorites.html`
- 简介优先使用 OpenRouter 大模型生成**产品介绍型**中文项目简介，失败时回退到术语摘要

## 数据目录

```text
data/
  daily/
    YYYY-MM-DD.json
  weekly/
    YYYY-MM-DD.json
  monthly/
    YYYY-MM-DD.json
```

## 本地运行

```bash
export OPENROUTER_API_KEY=你的key
TRENDING_PERIOD=daily python3 collector.py
TRENDING_PERIOD=weekly python3 collector.py
TRENDING_PERIOD=monthly python3 collector.py
python3 generate_html.py
python3 server.py
```

## GitHub Actions

GitHub Actions 每天北京时间 08:00 自动执行，并分别采集：
- daily
- weekly
- monthly

需要在仓库 Secrets 中配置：
- `OPENROUTER_API_KEY`
