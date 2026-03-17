# GitHub Trending AI 每日精选

每天自动收集 GitHub Trending 中与 AI、具身智能相关的开源项目，并生成可按日期浏览、按标签筛选的静态网页。

## 功能

- 每天早上 8:00（北京时间）自动采集
- 数据源：GitHub Trending weekly
- 按日期查看历史结果
- 按标签筛选：Agent / LLM / 机器人/具身 / 视觉 / 多模态 / 语音 / RAG / 训练推理
- 输出 JSON、Markdown、静态 HTML

## 本地运行

```bash
python3 collector.py
python3 generate_html.py
python3 server.py
```

打开：<http://localhost:8080>

## 数据结构

每个 `data/YYYY-MM-DD.json` 包含：

- `date`: 数据日期
- `period`: 统计周期（当前为 `weekly`）
- `count`: 项目数
- `projects[]`:
  - `name`
  - `url`
  - `description_en`
  - `description_zh`
  - `stars`
  - `forks`
  - `stars_period`
  - `matched_keywords`
  - `tags`
  - `relevance_score`

## 自动更新

GitHub Actions 已配置为：
- 每天北京时间 08:00 自动执行
- 也可手动在 Actions 页面触发

流程：
1. 运行 `collector.py`
2. 运行 `generate_html.py`
3. 自动提交更新后的数据和页面

## 后续可继续优化

- 接入中文翻译 API，真正生成 `description_zh`
- 增加排序（按 star / 新增 star）
- 增加更多标签和更精细的分类
- 改为 GitHub API + HTML fallback 双通道采集
