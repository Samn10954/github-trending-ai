#!/usr/bin/env python3
"""
生成静态页面：
- index.html 指向最新日期
- 每个 data/YYYY-MM-DD.json 对应一个 YYYY-MM-DD.html
- 支持日期浏览与 tag filter
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


def load_all_data() -> list[dict[str, Any]]:
    records = []
    for path in sorted(DATA_DIR.glob("*.json"), reverse=True):
        if path.name == "index.json":
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        records.append(payload)
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
    buttons = []
    for record in records:
        date_str = record["date"]
        active_class = " active" if date_str == current_date else ""
        buttons.append(
            f'<a href="./{date_str}.html" class="date-btn{active_class}">{format_date_label(date_str)}</a>'
        )
    return "\n".join(buttons)


def build_tag_buttons() -> str:
    parts = []
    for key, label in TAG_META:
        active_class = " active" if key == "all" else ""
        parts.append(f'<button class="tag-btn{active_class}" data-tag="{key}">{label}</button>')
    return "\n".join(parts)


def render_page(record: dict[str, Any], all_records: list[dict[str, Any]]) -> str:
    projects = record.get("projects", [])
    current_date = record["date"]
    current_period = record.get("period", "weekly")
    total_stars = sum(project.get("stars_period", 0) for project in projects)
    projects_json = json.dumps(projects, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"UTF-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
  <title>GitHub Trending AI - {current_date}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system,BlinkMacSystemFont,\"Segoe UI\",Roboto,sans-serif; background:#0d1117; color:#c9d1d9; }}
    .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
    header {{ text-align:center; padding:40px 0 24px; border-bottom:1px solid #30363d; margin-bottom:24px; }}
    h1 {{ font-size: 2.5rem; background: linear-gradient(90deg,#58a6ff,#a371f7); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }}
    .subtitle {{ color:#8b949e; margin-top: 10px; }}
    .date-nav, .tag-filter {{ display:flex; flex-wrap:wrap; gap:10px; justify-content:center; }}
    .date-nav {{ margin-bottom: 20px; }}
    .date-btn, .tag-btn {{ border:1px solid #30363d; background:#21262d; color:#58a6ff; text-decoration:none; padding:8px 14px; border-radius:8px; cursor:pointer; }}
    .date-btn.active, .tag-btn.active {{ background:#238636; border-color:#238636; color:#fff; }}
    .filter-section {{ margin: 18px 0 22px; background:#161b22; border:1px solid #30363d; border-radius:10px; padding:15px; }}
    .filter-label {{ color:#8b949e; margin-bottom:10px; }}
    .stats {{ display:flex; justify-content:center; gap:36px; margin-bottom:24px; color:#8b949e; flex-wrap:wrap; }}
    .stats strong {{ color:#58a6ff; font-size:1.4rem; }}
    .project-list {{ display:grid; gap:16px; }}
    .project-card {{ background:#161b22; border:1px solid #30363d; border-radius:10px; padding:18px; }}
    .project-header {{ display:flex; justify-content:space-between; gap:16px; align-items:flex-start; margin-bottom:12px; }}
    .project-name {{ color:#58a6ff; text-decoration:none; font-size:1.1rem; font-weight:600; }}
    .project-stats {{ display:flex; gap:14px; flex-wrap:wrap; color:#8b949e; font-size:.92rem; }}
    .stat.star {{ color:#e3b341; }}
    .stat.period {{ color:#238636; }}
    .project-desc-zh {{ color:#e6edf3; line-height:1.6; margin-bottom:8px; }}
    .project-desc-en {{ color:#8b949e; line-height:1.5; margin-bottom:12px; font-size:.95rem; }}
    .keywords {{ display:flex; gap:8px; flex-wrap:wrap; }}
    .keyword {{ background:#21262d; color:#a371f7; border-radius:999px; padding:3px 9px; font-size:.8rem; }}
    .empty {{ text-align:center; color:#8b949e; padding:32px; }}
    @media (max-width: 768px) {{ .project-header {{ flex-direction:column; }} }}
  </style>
</head>
<body>
  <div class=\"container\">
    <header>
      <h1>🤖 GitHub Trending AI</h1>
      <p class=\"subtitle\">每日 AI、具身智能热门开源项目精选 · 当前日期 {current_date} · 周期 {current_period}</p>
    </header>

    <div class=\"date-nav\">
      {build_date_nav(all_records, current_date)}
    </div>

    <div class=\"filter-section\">
      <div class=\"filter-label\">🏷️ 标签筛选</div>
      <div class=\"tag-filter\">
        {build_tag_buttons()}
      </div>
    </div>

    <div class=\"stats\">
      <div>项目数: <strong id=\"totalCount\">{len(projects)}</strong></div>
      <div>周期新增: <strong id=\"totalStars\">{total_stars}</strong> ⭐</div>
    </div>

    <div class=\"project-list\" id=\"projectList\"></div>
  </div>

  <script>
    const projects = {projects_json};
    let activeTag = 'all';

    function formatNumber(n) {{
      return n >= 1000 ? (n / 1000).toFixed(1) + 'k' : String(n);
    }}

    function renderProjects() {{
      const listEl = document.getElementById('projectList');
      const filtered = activeTag === 'all'
        ? projects
        : projects.filter(p => (p.tags || []).includes(activeTag));

      document.getElementById('totalCount').textContent = filtered.length;
      document.getElementById('totalStars').textContent = filtered.reduce((sum, p) => sum + (p.stars_period || 0), 0).toLocaleString();

      if (!filtered.length) {{
        listEl.innerHTML = '<div class="empty">没有找到匹配项目</div>';
        return;
      }}

      listEl.innerHTML = filtered.map(p => `
        <div class="project-card">
          <div class="project-header">
            <a class="project-name" href="${{p.url}}" target="_blank" rel="noopener noreferrer">${{p.name}}</a>
            <div class="project-stats">
              <span class="stat star">⭐ ${{formatNumber(p.stars)}}</span>
              <span class="stat period">+${{(p.stars_period || 0).toLocaleString()}}</span>
              <span class="stat">⑂ ${{formatNumber(p.forks)}}</span>
            </div>
          </div>
          <div class="project-desc-zh">${{p.description_zh || '暂无中文简介'}}</div>
          <div class="project-desc-en">${{p.description_en || ''}}</div>
          <div class="keywords">
            ${{(p.tags || []).map(tag => `<span class="keyword">${{tag}}</span>`).join('')}}
          </div>
        </div>
      `).join('');
    }}

    document.querySelectorAll('.tag-btn').forEach(btn => {{
      btn.addEventListener('click', () => {{
        document.querySelectorAll('.tag-btn').forEach(node => node.classList.remove('active'));
        btn.classList.add('active');
        activeTag = btn.dataset.tag;
        renderProjects();
      }});
    }});

    renderProjects();
  </script>
</body>
</html>
"""


def main() -> None:
    records = load_all_data()
    if not records:
        raise SystemExit("No data files found in data/")

    latest_date = records[0]["date"]
    for record in records:
        out_path = BASE_DIR / f"{record['date']}.html"
        out_path.write_text(render_page(record, records), encoding="utf-8")

    INDEX_FILE.write_text(render_page(records[0], records).replace(f"./{latest_date}.html", "./index.html", 1), encoding="utf-8")
    print(f"Generated {len(records)} date pages + index.html")


if __name__ == "__main__":
    main()
