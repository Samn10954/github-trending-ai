#!/usr/bin/env python3
"""
自动生成静态 HTML 页面
从 data/*.json 读取数据，生成 index.html
"""

import json
import os
from datetime import datetime, timedelta

DATA_DIR = "data"
OUTPUT_FILE = "index.html"

TAG_MAP = {
    'agent': ['agent', 'agentic', 'autonomous'],
    'llm': ['llm', 'gpt', 'claude', 'gemini'],
    'robotics': ['robotics', 'robot', 'embodied', 'humanoid'],
    'vision': ['vision', 'cv', 'computer vision', 'multimodal', 'vlm'],
    'speech': ['speech', 'tts', 'stt', 'voice', 'audio'],
    'rag': ['rag', 'retrieval', 'knowledge graph'],
    'training': ['training', 'inference', 'cuda', 'gpu']
}

def load_latest_data():
    json_files = sorted([f for f in os.listdir(DATA_DIR) if f.endswith('.json') and f != 'index.json'])
    if not json_files:
        return None, []
    
    latest_file = json_files[-1]
    with open(os.path.join(DATA_DIR, latest_file), 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    dates = []
    for f in json_files:
        date = f.replace('.json', '')
        label = format_date_label(date)
        dates.append({'date': date, 'label': label})
    
    dates.reverse()
    return data, dates

def format_date_label(date_str):
    d = datetime.strptime(date_str, '%Y-%m-%d')
    today = datetime.now()
    yesterday = datetime.now() - timedelta(days=1)
    
    if date_str == today.strftime('%Y-%m-%d'):
        return '今天'
    elif date_str == yesterday.strftime('%Y-%m-%d'):
        return '昨天'
    else:
        return f"{d.month}月{d.day}日"

def extract_tags(project):
    keywords = project.get('matched_keywords', [])
    tags = set()
    
    for kw in keywords:
        kw_lower = kw.lower()
        for tag, tag_keywords in TAG_MAP.items():
            if any(tk in kw_lower for tk in tag_keywords):
                tags.add(tag)
    
    if not tags:
        tags.add('ai')
    
    return list(tags)

def format_number(n):
    if n >= 1000:
        return f"{n/1000:.1f}k"
    return str(n)

def generate_html(data, dates):
    projects_js = []
    for p in data.get('projects', []):
        tags = extract_tags(p)
        desc = (p.get('description') or '').replace('"', '\\"')
        proj = {
            "name": p['name'],
            "url": p['url'],
            "description": desc,
            "stars": p['stars'],
            "forks": p['forks'],
            "stars_today": p['stars_today'],
            "tags": tags
        }
        projects_js.append(json.dumps(proj))
    
    dates_js = json.dumps(dates)
    
    total_projects = len(data.get('projects', []))
    total_stars = sum(p.get('stars_today', 0) for p in data.get('projects', []))
    
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GitHub Trending AI - 每日精选</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #0d1117;
            color: #c9d1d9;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        header {{
            text-align: center;
            padding: 40px 0;
            border-bottom: 1px solid #30363d;
            margin-bottom: 30px;
        }}
        h1 {{
            font-size: 2.5rem;
            background: linear-gradient(90deg, #58a6ff, #a371f7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }}
        .subtitle {{ color: #8b949e; }}
        
        .date-nav {{
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}
        .date-btn {{
            background: #21262d;
            border: 1px solid #30363d;
            color: #58a6ff;
            padding: 8px 16px;
            border-radius: 6px;
            text-decoration: none;
            transition: all 0.2s;
        }}
        .date-btn:hover {{ background: #30363d; }}
        
        .filter-section {{
            margin-bottom: 20px;
            padding: 15px;
            background: #161b22;
            border-radius: 8px;
            border: 1px solid #30363d;
        }}
        .filter-label {{
            color: #8b949e;
            margin-bottom: 10px;
            font-size: 0.9rem;
        }}
        .tag-filter {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }}
        .tag-btn {{
            background: #21262d;
            border: 1px solid #30363d;
            color: #8b949e;
            padding: 4px 12px;
            border-radius: 16px;
            font-size: 0.85rem;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .tag-btn:hover {{ border-color: #58a6ff; color: #58a6ff; }}
        .tag-btn.active {{
            background: #238636;
            border-color: #238636;
            color: white;
        }}
        
        .stats {{
            display: flex;
            justify-content: center;
            gap: 40px;
            margin-bottom: 30px;
            color: #8b949e;
        }}
        .stats strong {{ color: #58a6ff; font-size: 1.5rem; }}
        
        .project-list {{ display: grid; gap: 16px; }}
        .project-card {{
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 20px;
            transition: border-color 0.2s;
        }}
        .project-card:hover {{ border-color: #58a6ff; }}
        .project-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 12px;
        }}
        .project-name {{
            font-size: 1.2rem;
            color: #58a6ff;
            text-decoration: none;
        }}
        .project-name:hover {{ text-decoration: underline; }}
        .project-stats {{
            display: flex;
            gap: 16px;
            font-size: 0.9rem;
        }}
        .stat {{
            display: flex;
            align-items: center;
            gap: 4px;
        }}
        .stat.star {{ color: #e3b341; }}
        .stat.fork {{ color: #8b949e; }}
        .stat.today {{ color: #238636; }}
        .project-desc {{
            color: #8b949e;
            line-height: 1.6;
            margin-bottom: 12px;
        }}
        .keywords {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }}
        .keyword {{
            background: #21262d;
            color: #a371f7;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
        }}
        
        .no-results {{
            text-align: center;
            padding: 40px;
            color: #8b949e;
        }}
        
        @media (max-width: 768px) {{
            .project-header {{ flex-direction: column; gap: 10px; }}
            .stats {{ flex-direction: column; gap: 10px; align-items: center; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🤖 GitHub Trending AI</h1>
            <p class="subtitle">每日 AI、具身智能热门开源项目精选</p>
        </header>
        
        <div class="date-nav" id="dateNav"></div>
        
        <div class="filter-section">
            <div class="filter-label">🏷️ 标签筛选：</div>
            <div class="tag-filter" id="tagFilter">
                <button class="tag-btn active" data-tag="all">全部</button>
                <button class="tag-btn" data-tag="agent">Agent</button>
                <button class="tag-btn" data-tag="llm">LLM</button>
                <button class="tag-btn" data-tag="robotics">机器人/具身</button>
                <button class="tag-btn" data-tag="vision">视觉/CV</button>
                <button class="tag-btn" data-tag="speech">语音/TTS</button>
                <button class="tag-btn" data-tag="rag">RAG</button>
                <button class="tag-btn" data-tag="training">训练/推理</button>
            </div>
        </div>
        
        <div class="stats">
            <div>项目数: <strong id="totalCount">{total_projects}</strong></div>
            <div>本周新增: <strong id="totalStars">{total_stars:,}</strong> ⭐</div>
        </div>
        
        <div class="project-list" id="projectList"></div>
    </div>

    <script>
        const projectsData = [{", ".join(projects_js)}];
        const dates = {dates_js};

        let currentTag = 'all';

        const tagMap = {{
            'agent': ['agent', 'agentic', 'autonomous'],
            'llm': ['llm', 'gpt', 'claude', 'gemini'],
            'robotics': ['robotics', 'robot', 'embodied', 'humanoid'],
            'vision': ['vision', 'cv', 'computer vision', 'multimodal', 'vlm'],
            'speech': ['speech', 'tts', 'stt', 'voice', 'audio'],
            'rag': ['rag', 'retrieval', 'knowledge graph'],
            'training': ['training', 'inference', 'cuda', 'gpu']
        }};

        function init() {{
            renderDateNav();
            renderProjects();
            initTagFilter();
        }}

        function renderDateNav() {{
            const nav = document.getElementById('dateNav');
            nav.innerHTML = dates.map(d => 
                `<a href="./${{d.date}}.html" class="date-btn">${{d.label}}</a>`
            ).join('');
        }}

        function initTagFilter() {{
            const buttons = document.querySelectorAll('.tag-btn');
            buttons.forEach(btn => {{
                btn.addEventListener('click', () => {{
                    buttons.forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    currentTag = btn.dataset.tag;
                    renderProjects();
                }});
            }});
        }}

        function renderProjects() {{
            const listEl = document.getElementById('projectList');
            
            let filtered = projectsData;
            if (currentTag !== 'all') {{
                const keywords = tagMap[currentTag] || [currentTag];
                filtered = projectsData.filter(p => 
                    p.tags.some(t => keywords.includes(t))
                );
            }}

            document.getElementById('totalCount').textContent = filtered.length;
            const totalStars = filtered.reduce((sum, p) => sum + p.stars_today, 0);
            document.getElementById('totalStars').textContent = totalStars.toLocaleString();

            if (filtered.length === 0) {{
                listEl.innerHTML = '<div class="no-results">没有找到匹配的项目</div>';
                return;
            }}

            listEl.innerHTML = filtered.map(p => `
                <div class="project-card">
                    <div class="project-header">
                        <a href="${{p.url}}" target="_blank" class="project-name">${{p.name}}</a>
                        <div class="project-stats">
                            <span class="stat star">⭐ ${{formatNumber(p.stars)}}</span>
                            <span class="stat today">+${{p.stars_today.toLocaleString()}} this week</span>
                            <span class="stat fork">⑂ ${{formatNumber(p.forks)}}</span>
                        </div>
                    </div>
                    <p class="project-desc">${{p.description || '暂无简介'}}</p>
                    <div class="keywords">
                        ${{p.tags.map(t => `<span class="keyword">${{t}}</span>`).join('')}}
                    </div>
                </div>
            `).join('');
        }}

        function formatNumber(n) {{
            if (n >= 1000) return (n / 1000).toFixed(1) + 'k';
            return n;
        }}

        init();
    </script>
</body>
</html>'''
    
    return html

def main():
    data, dates = load_latest_data()
    if not data:
        print("No data found!")
        return
    
    html = generate_html(data, dates)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Generated {OUTPUT_FILE} with {len(data.get('projects', []))} projects")

if __name__ == "__main__":
    main()
