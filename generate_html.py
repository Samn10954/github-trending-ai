#!/usr/bin/env python3
"""
生成静态页面：
- index.html 展示最新日期 + 历史日期入口
- 每个 data/YYYY-MM-DD.json 对应一个 YYYY-MM-DD.html
- 支持日期浏览、tag filter、排序、趋势图、收藏
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
INDEX_FILE = BASE_DIR / "index.html"

TAG_META = [
    ("all", "全部"),
    ("agent", "Agent"),
    ("llm", "LLM"),
    ("robotics", "机器人/具身"),
    ("vision", "视觉/CV"),
    ("multimodal", "多模态"),
    ("speech", "语音/TTS"),
    ("rag", "RAG"),
    ("training", "训练/推理"),
]
PERIOD_META = [("daily", "日榜"), ("weekly", "周榜"), ("monthly", "月榜")]
SORT_META = [
    ("stars_period", "按周期新增排序"),
    ("stars", "按总 Stars 排序"),
    ("forks", "按 Forks 排序"),
    ("relevance_score", "按相关性排序"),
]


def load_all_data() -> list[dict[str, Any]]:
    records = []
    for path in sorted(DATA_DIR.glob("*.json"), reverse=True):
        if path.name == "index.json":
            continue
        records.append(json.loads(path.read_text(encoding="utf-8")))
    return records


def format_date_label(date_str: str) -> str:
    d = datetime.strptime(date_str, "%Y-%m-%d")
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    if date_str == today.strftime("%Y-%m-%d"):
        return "今天"
    if date_str == yesterday.strftime("%Y-%m-%d"):
        return "昨天"
    return f"{d.month}月{d.day}日"


def build_date_nav(records: list[dict[str, Any]], current_date: str) -> str:
    parts = []
    for r in records:
        active = " active" if r["date"] == current_date else ""
        parts.append(f'<a href="./{r["date"]}.html" class="date-btn{active}">{format_date_label(r["date"])}' + '</a>')
    return "\n".join(parts)


def build_tag_buttons() -> str:
    return "\n".join(
        f'<button class="tag-btn{" active" if key == "all" else ""}" data-tag="{key}">{label}</button>'
        for key, label in TAG_META
    )


def build_period_buttons(current_period: str) -> str:
    return "\n".join(
        f'<button class="tag-btn period-btn{" active" if key == current_period else ""}" data-period="{key}">{label}</button>'
        for key, label in PERIOD_META
    )


def build_sort_options() -> str:
    return "\n".join(f'<option value="{k}">{v}</option>' for k, v in SORT_META)


def build_archive(records: list[dict[str, Any]]) -> str:
    parts = []
    for r in records:
        count = r.get("count", len(r.get("projects", [])))
        parts.append(
            f'<a class="archive-item" href="./{r["date"]}.html"><span>{format_date_label(r["date"])} / {r["date"]}</span><span>{count} 个项目</span></a>'
        )
    return "\n".join(parts)


def render_page(record: dict[str, Any], all_records: list[dict[str, Any]], *, is_index: bool = False) -> str:
    projects = record.get("projects", [])
    current_date = record["date"]
    current_period = record.get("period", "weekly")
    total_stars = sum(p.get("stars_period", 0) for p in projects)
    title = "GitHub Trending AI - 每日精选" if is_index else f"GitHub Trending AI - {current_date}"
    trend_data = [
        {"date": r["date"], "count": len(r.get("projects", [])), "stars_period": sum(p.get("stars_period", 0) for p in r.get("projects", []))}
        for r in reversed(all_records)
    ]

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
    * {{ box-sizing:border-box; margin:0; padding:0; }}
    body {{ font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; background:#0d1117; color:#c9d1d9; }}
    .container {{ max-width:1200px; margin:0 auto; padding:20px; }}
    header {{ text-align:center; padding:40px 0 24px; border-bottom:1px solid #30363d; margin-bottom:24px; }}
    h1 {{ font-size:2.5rem; background:linear-gradient(90deg,#58a6ff,#a371f7); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }}
    .subtitle {{ color:#8b949e; margin-top:10px; }}
    .section-title {{ font-size:1rem; color:#e6edf3; margin-bottom:12px; }}
    .date-nav,.tag-filter {{ display:flex; flex-wrap:wrap; gap:10px; justify-content:center; }}
    .date-nav {{ margin-bottom:20px; }}
    .date-btn,.tag-btn,.sort-select {{ border:1px solid #30363d; background:#21262d; color:#58a6ff; text-decoration:none; padding:8px 14px; border-radius:8px; }}
    .date-btn.active,.tag-btn.active {{ background:#238636; border-color:#238636; color:#fff; }}
    .toolbar {{ display:grid; gap:16px; margin:18px 0 22px; }}
    .filter-section,.archive-section,.chart-section {{ background:#161b22; border:1px solid #30363d; border-radius:10px; padding:15px; }}
    .filter-label {{ color:#8b949e; margin-bottom:10px; }}
    .filter-row {{ display:flex; gap:12px; flex-wrap:wrap; align-items:center; justify-content:space-between; }}
    .sort-wrap {{ display:flex; align-items:center; gap:8px; color:#8b949e; }}
    .stats {{ display:flex; justify-content:center; gap:36px; margin-bottom:24px; color:#8b949e; flex-wrap:wrap; }}
    .stats strong {{ color:#58a6ff; font-size:1.4rem; }}
    .content-grid {{ display:grid; grid-template-columns:1fr 280px; gap:20px; }}
    .project-list {{ display:grid; gap:16px; }}
    .project-card {{ background:#161b22; border:1px solid #30363d; border-radius:10px; padding:18px; }}
    .project-header {{ display:flex; justify-content:space-between; gap:16px; align-items:flex-start; margin-bottom:12px; }}
    .project-name {{ color:#58a6ff; text-decoration:none; font-size:1.1rem; font-weight:600; }}
    .project-stats {{ display:flex; gap:14px; flex-wrap:wrap; color:#8b949e; font-size:.92rem; }}
    .stat.star {{ color:#e3b341; }} .stat.period {{ color:#238636; }}
    .project-desc-zh {{ color:#e6edf3; line-height:1.6; margin-bottom:8px; }}
    .project-desc-en {{ color:#8b949e; line-height:1.5; margin-bottom:12px; font-size:.95rem; }}
    .keywords {{ display:flex; gap:8px; flex-wrap:wrap; }}
    .keyword {{ background:#21262d; color:#a371f7; border-radius:999px; padding:3px 9px; font-size:.8rem; }}
    .archive-list {{ display:grid; gap:8px; }}
    .archive-item {{ display:flex; justify-content:space-between; gap:12px; background:#0d1117; color:#c9d1d9; text-decoration:none; border:1px solid #30363d; border-radius:8px; padding:10px 12px; font-size:.92rem; }}
    .chart-canvas {{ width:100%; height:220px; display:block; background:#0d1117; border:1px solid #30363d; border-radius:8px; }}
    .card-actions {{ margin-top:12px; display:flex; gap:10px; }}
    .fav-btn {{ border:1px solid #30363d; background:#21262d; color:#f778ba; border-radius:8px; padding:6px 10px; cursor:pointer; }}
    .fav-btn.active {{ background:#f778ba; color:#0d1117; border-color:#f778ba; }}
    .empty {{ text-align:center; color:#8b949e; padding:32px; background:#161b22; border:1px solid #30363d; border-radius:10px; }}
    @media (max-width:900px) {{ .content-grid {{ grid-template-columns:1fr; }} }}
    @media (max-width:768px) {{ .project-header {{ flex-direction:column; }} .filter-row {{ align-items:flex-start; }} }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>🤖 GitHub Trending AI</h1>
      <p class="subtitle">每日 AI、具身智能热门开源项目精选 · 当前日期 {current_date} · 周期 {current_period}</p>
    </header>

    <div class="date-nav">{build_date_nav(all_records, current_date)}</div>

    <div class="toolbar">
      <div class="filter-section">
        <div class="filter-row">
          <div><div class="filter-label">🏷️ 标签筛选</div><div class="tag-filter">{build_tag_buttons()}</div></div>
          <div><div class="filter-label">📅 榜单周期</div><div class="tag-filter">{build_period_buttons(current_period)}</div></div>
          <div class="sort-wrap"><label for="sortSelect">排序</label><select id="sortSelect" class="sort-select">{build_sort_options()}</select></div>
        </div>
      </div>
    </div>

    <div class="stats"><div>项目数: <strong id="totalCount">{len(projects)}</strong></div><div>周期新增: <strong id="totalStars">{total_stars}</strong> ⭐</div></div>

    <section class="chart-section" style="margin-bottom:20px;"><div class="section-title">趋势图</div><canvas id="trendChart" class="chart-canvas" width="1000" height="220"></canvas></section>

    <div class="content-grid">
      <div class="project-list" id="projectList"></div>
      <aside class="archive-section"><div class="section-title">历史日期</div><div class="archive-list">{build_archive(all_records)}</div></aside>
    </div>
  </div>

  <script id="projects-data" type="application/json">{json.dumps(projects, ensure_ascii=False)}</script>
  <script id="trend-data" type="application/json">{json.dumps(trend_data, ensure_ascii=False)}</script>
  <script>
    const projects = JSON.parse(document.getElementById('projects-data').textContent);
    const trendSeries = JSON.parse(document.getElementById('trend-data').textContent);
    const favoritesKey = 'github-trending-ai-favorites';
    let favorites = JSON.parse(localStorage.getItem(favoritesKey) || '[]');
    let activeTag = 'all';
    let activeSort = 'stars_period';

    function formatNumber(n) {{ return n >= 1000 ? (n / 1000).toFixed(1) + 'k' : String(n); }}
    function sortProjects(items) {{ return [...items].sort((a,b) => (b[activeSort] || 0) - (a[activeSort] || 0)); }}
    function escapeHtml(s) {{ return String(s || '').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;'); }}

    function toggleFavorite(name) {{
      if (favorites.includes(name)) favorites = favorites.filter(x => x !== name);
      else favorites.push(name);
      localStorage.setItem(favoritesKey, JSON.stringify(favorites));
      renderProjects();
    }}

    function renderProjects() {{
      const listEl = document.getElementById('projectList');
      const filtered = activeTag === 'all' ? projects : projects.filter(p => (p.tags || []).includes(activeTag));
      const sorted = sortProjects(filtered);
      document.getElementById('totalCount').textContent = sorted.length;
      document.getElementById('totalStars').textContent = sorted.reduce((s,p) => s + (p.stars_period || 0), 0).toLocaleString();
      if (!sorted.length) {{ listEl.innerHTML = '<div class="empty">没有找到匹配项目</div>'; return; }}
      listEl.innerHTML = sorted.map(p => {{
        const fav = favorites.includes(p.name);
        const tags = (p.tags || []).map(tag => '<span class="keyword">' + escapeHtml(tag) + '</span>').join('');
        return '<div class="project-card">'
          + '<div class="project-header">'
          + '<a class="project-name" href="' + escapeHtml(p.url) + '" target="_blank" rel="noopener noreferrer">' + escapeHtml(p.name) + '</a>'
          + '<div class="project-stats">'
          + '<span class="stat star">⭐ ' + formatNumber(p.stars) + '</span>'
          + '<span class="stat period">+' + ((p.stars_period || 0).toLocaleString()) + '</span>'
          + '<span class="stat">⑂ ' + formatNumber(p.forks) + '</span>'
          + '<span class="stat">相关性 ' + (p.relevance_score || 0) + '</span>'
          + '</div></div>'
          + '<div class="project-desc-zh">' + escapeHtml(p.description_zh || '暂无中文简介') + '</div>'
          + '<div class="project-desc-en">' + escapeHtml(p.description_en || '') + '</div>'
          + '<div class="keywords">' + tags + '</div>'
          + '<div class="card-actions"><button class="fav-btn ' + (fav ? 'active' : '') + '" data-name="' + escapeHtml(p.name) + '">' + (fav ? '★ 已收藏' : '☆ 收藏') + '</button></div>'
          + '</div>';
      }}).join('');
      document.querySelectorAll('.fav-btn').forEach(btn => btn.addEventListener('click', () => toggleFavorite(btn.dataset.name)));
    }}

    function drawTrendChart() {{
      const canvas = document.getElementById('trendChart');
      const ctx = canvas.getContext('2d');
      const w = canvas.width, h = canvas.height;
      ctx.clearRect(0, 0, w, h);
      ctx.fillStyle = '#0d1117'; ctx.fillRect(0, 0, w, h);
      if (!trendSeries.length) return;
      const values = trendSeries.map(x => x.stars_period || 0);
      const maxVal = Math.max(...values, 1);
      const left = 50, right = 20, top = 20, bottom = 40;
      const plotW = w - left - right, plotH = h - top - bottom;
      ctx.strokeStyle = '#30363d'; ctx.beginPath(); ctx.moveTo(left, top); ctx.lineTo(left, h - bottom); ctx.lineTo(w - right, h - bottom); ctx.stroke();
      ctx.strokeStyle = '#58a6ff'; ctx.lineWidth = 2; ctx.beginPath();
      trendSeries.forEach((point, i) => {{
        const x = left + (plotW * i) / Math.max(trendSeries.length - 1, 1);
        const y = top + plotH - ((point.stars_period || 0) / maxVal) * plotH;
        if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      }});
      ctx.stroke();
      ctx.fillStyle = '#8b949e'; ctx.font = '12px sans-serif';
      trendSeries.forEach((point, i) => {{
        const x = left + (plotW * i) / Math.max(trendSeries.length - 1, 1);
        ctx.fillText(String(point.date).slice(5), x - 18, h - 15);
      }});
    }}

    document.querySelectorAll('.tag-btn:not(.period-btn)').forEach(btn => btn.addEventListener('click', () => {{
      document.querySelectorAll('.tag-btn:not(.period-btn)').forEach(node => node.classList.remove('active'));
      btn.classList.add('active');
      activeTag = btn.dataset.tag;
      renderProjects();
    }}));
    document.querySelectorAll('.period-btn').forEach(btn => btn.addEventListener('click', () => {{
      const period = btn.dataset.period;
      const url = new URL(window.location.href);
      url.searchParams.set('period', period);
      window.location.href = url.pathname + '?period=' + period;
    }}));
    document.getElementById('sortSelect').addEventListener('change', (event) => {{ activeSort = event.target.value; renderProjects(); }});

    drawTrendChart();
    renderProjects();
  </script>
</body>
</html>'''


def main() -> None:
    records = load_all_data()
    if not records:
        raise SystemExit("No data files found in data/")
    for record in records:
        (BASE_DIR / f"{record['date']}.html").write_text(render_page(record, records), encoding="utf-8")
    INDEX_FILE.write_text(render_page(records[0], records, is_index=True), encoding="utf-8")
    print(f"Generated {len(records)} date pages + index.html")


if __name__ == "__main__":
    main()
