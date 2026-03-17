#!/usr/bin/env python3
"""
GitHub Trending AI 采集器
采集 AI、具身智能相关的热门开源项目
"""

import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import re

# 配置
TRENDING_URL = "https://github.com/trending?since=weekly"
OUTPUT_DIR = "/Users/doudou/.openclaw/workspace/github-trending-ai/data"

# 过滤关键词（不区分大小写）
KEYWORDS = [
    "ai", "llm", "large language model", "gpt", "claude", "gemini",
    "agent", "agentic", "autonomous", "agent framework",
    "robotics", "robot", "embodied", "physical ai", "humanoid",
    "computer vision", "cv", "vision", "multimodal", "vlm",
    "deep learning", "neural", "machine learning", "ml",
    "speech", "tts", "stt", "voice", "audio",
    "image generation", "diffusion", "stable diffusion", "image synthesis",
    "rag", "retrieval", "knowledge graph",
    "cuda", "gpu", "inference", "training",
    "automation", " autonomous driving", "self-driving",
    "gesture", "pose", "motion", "control",
    "slam", "navigation", "mapping",
    "manipulation", "grasp", "dexterous"
]

def fetch_trending():
    """获取 GitHub Trending 页面"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    resp = requests.get(TRENDING_URL, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.text

def parse_trending(html):
    """解析 HTML 获取项目信息"""
    soup = BeautifulSoup(html, "html.parser")
    articles = soup.find_all("article", class_="Box-row")
    
    projects = []
    for article in articles:
        try:
            # 项目名和链接
            h2 = article.find("h2")
            if not h2:
                continue
            repo_link = h2.find("a")
            if not repo_link:
                continue
            
            full_name = repo_link.get_text(strip=True).replace("\n", "").replace(" ", "")
            owner, name = full_name.split("/")
            url = "https://github.com" + repo_link.get("href")
            
            # 简介
            p = article.find("p")
            description = p.get_text(strip=True) if p else ""
            
            # Star 和 Fork 数量
            star_link = article.find("a", href=lambda x: x and "/stargazers" in x)
            fork_link = article.find("a", href=lambda x: x and "/forks" in x)
            
            stars = star_link.get_text(strip=True).replace(",", "") if star_link else "0"
            forks = fork_link.get_text(strip=True).replace(",", "") if fork_link else "0"
            
            # 当日/周新增 - 查找包含 "stars today" 或 "stars this week" 的元素
            stars_today = "0"
            for span in article.find_all("span"):
                text = span.get_text()
                if "stars today" in text.lower() or "stars this week" in text.lower():
                    match = re.search(r"([\d,]+)", text)
                    if match:
                        stars_today = match.group(1).replace(",", "")
                    break
            
            projects.append({
                "name": full_name,
                "url": url,
                "description": description,
                "stars": int(stars) if stars.isdigit() else 0,
                "forks": int(forks) if forks.isdigit() else 0,
                "stars_today": int(stars_today) if stars_today.isdigit() else 0,
                "owner": owner,
                "repo": name
            })
        except Exception as e:
            print(f"解析项目时出错: {e}")
            continue
    
    return projects

def filter_by_keywords(projects):
    """根据关键词过滤项目"""
    filtered = []
    for p in projects:
        text = f"{p['name']} {p['description']}".lower()
        if any(kw.lower() in text for kw in KEYWORDS):
            p["matched_keywords"] = [kw for kw in KEYWORDS if kw.lower() in text]
            filtered.append(p)
    return filtered

def translate_description(description, max_len=500):
    """简单的翻译（调用免费 API 或返回原文）"""
    # 这里先返回原文，后续可以接入翻译 API
    return description

def save_results(projects, date_str):
    """保存结果到本地"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # JSON 格式
    json_path = os.path.join(OUTPUT_DIR, f"{date_str}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "date": date_str,
            "count": len(projects),
            "projects": projects
        }, f, ensure_ascii=False, indent=2)
    
    # Markdown 格式
    md_path = os.path.join(OUTPUT_DIR, f"{date_str}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# GitHub Trending AI 项目 ({date_str})\n\n")
        f.write(f"共收集 **{len(projects)}** 个相关项目\n\n")
        f.write("| 项目 | 简介 | Stars | 今日新增 | Forks |\n")
        f.write("|------|------|-------|----------|-------|\n")
        for p in projects:
            desc = p["description"][:50] + "..." if len(p["description"]) > 50 else p["description"]
            f.write(f"| [{p['name']}]({p['url']}) | {desc} | {p['stars']} | {p['stars_today']} | {p['forks']} |\n")
    
    return json_path, md_path

def update_index(date_str):
    """更新索引文件"""
    index_path = os.path.join(OUTPUT_DIR, "index.json")
    dates = []
    if os.path.exists(index_path):
        with open(index_path, "r") as f:
            dates = json.load(f)
    if date_str not in dates:
        dates.insert(0, date_str)
    with open(index_path, "w") as f:
        json.dump(dates, f)

def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始采集 GitHub Trending...")
    
    # 获取页面
    html = fetch_trending()
    
    # 解析
    projects = parse_trending(html)
    print(f"共获取 {len(projects)} 个Trending项目")
    
    # 过滤
    filtered = filter_by_keywords(projects)
    print(f"AI/具身智能相关项目: {len(filtered)} 个")
    
    # 保存
    date_str = datetime.now().strftime("%Y-%m-%d")
    json_path, md_path = save_results(filtered, date_str)
    
    print(f"结果已保存:")
    print(f"  - JSON: {json_path}")
    print(f"  - Markdown: {md_path}")
    
    # 更新索引
    update_index(date_str)
    
    # 打印预览
    print("\n=== 预览 (前5个) ===")
    for p in filtered[:5]:
        print(f"- {p['name']}: {p['description'][:60]}... ⭐{p['stars_today']}")

if __name__ == "__main__":
    main()
