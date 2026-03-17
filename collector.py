#!/usr/bin/env python3
"""
GitHub Trending AI 采集器
- 支持 daily / weekly / monthly
- 过滤 AI / 具身智能相关项目
- 生成标准化 JSON / Markdown 数据
- 优先使用 OpenRouter 大模型生成中文简介，失败时回退到术语摘要
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent
PERIOD = os.getenv("TRENDING_PERIOD", "weekly").strip().lower() or "weekly"
if PERIOD not in {"daily", "weekly", "monthly"}:
    PERIOD = "weekly"
DATA_DIR = BASE_DIR / "data" / PERIOD
TRENDING_URL = f"https://github.com/trending?since={PERIOD}"
MIN_PARSED_PROJECTS = 5
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = os.getenv("TRANSLATION_MODEL", "openrouter/openai/gpt-5.4")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

TAG_MAP = {
    "agent": ["agent", "agentic", "autonomous"],
    "llm": ["llm", "gpt", "claude", "gemini", "language model"],
    "robotics": ["robotics", "robot", "embodied", "humanoid", "physical ai", "slam", "navigation", "mapping", "manipulation", "grasp", "dexterous"],
    "vision": ["vision", "computer vision", "cv"],
    "multimodal": ["multimodal", "vlm", "image-text", "video-understanding"],
    "speech": ["speech", "tts", "stt", "voice", "audio"],
    "rag": ["rag", "retrieval", "knowledge graph"],
    "training": ["training", "inference", "cuda", "gpu", "neural", "deep learning"],
}

KEYWORD_SPECS = [
    (r"\bai\b", "ai", 2), (r"\bllm\b", "llm", 3), (r"\bgpt\b", "gpt", 2),
    (r"\bclaude\b", "claude", 2), (r"\bgemini\b", "gemini", 2), (r"\bagent\b", "agent", 3),
    (r"\bagentic\b", "agentic", 3), (r"\bautonomous\b", "autonomous", 2),
    (r"\brobotics?\b", "robotics", 3), (r"\brobot\b", "robot", 2), (r"\bembodied\b", "embodied", 3),
    (r"\bhumanoid\b", "humanoid", 3), (r"\bcomputer vision\b", "computer vision", 3),
    (r"\bcv\b", "cv", 1), (r"\bvision\b", "vision", 1), (r"\bmultimodal\b", "multimodal", 3),
    (r"\bvlm\b", "vlm", 3), (r"\bmachine learning\b", "machine learning", 2), (r"\bdeep learning\b", "deep learning", 2),
    (r"\bneural\b", "neural", 1), (r"\bspeech\b", "speech", 2), (r"\btts\b", "tts", 3), (r"\bstt\b", "stt", 3),
    (r"\bvoice\b", "voice", 1), (r"\baudio\b", "audio", 1), (r"\brag\b", "rag", 3),
    (r"\bretrieval\b", "retrieval", 2), (r"\bknowledge graph\b", "knowledge graph", 2),
    (r"\bcuda\b", "cuda", 2), (r"\bgpu\b", "gpu", 2), (r"\binference\b", "inference", 2),
    (r"\btraining\b", "training", 2), (r"\bslam\b", "slam", 3), (r"\bnavigation\b", "navigation", 2),
    (r"\bmapping\b", "mapping", 1), (r"\bmanipulation\b", "manipulation", 3), (r"\bgrasp\b", "grasp", 2),
    (r"\bdexterous\b", "dexterous", 2),
]

GLOSSARY = {
    "agent": "智能体", "agents": "智能体", "agentic": "智能体化", "framework": "框架",
    "inference": "推理", "training": "训练", "speech": "语音", "browser": "浏览器",
    "robot": "机器人", "robotics": "机器人技术", "multimodal": "多模态", "vision": "视觉",
    "database": "数据库", "memory": "记忆", "skills": "技能", "context": "上下文",
    "plugin": "插件", "plugins": "插件",
}


def fetch_trending() -> str:
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(TRENDING_URL, headers=headers, timeout=30)
    response.raise_for_status()
    return response.text


def parse_int(raw: str) -> int:
    digits = re.sub(r"[^\d]", "", raw or "")
    return int(digits) if digits else 0


def parse_trending(html: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    articles = soup.find_all("article", class_="Box-row")
    projects: list[dict[str, Any]] = []
    for article in articles:
        try:
            h2 = article.find("h2")
            repo_link = h2.find("a") if h2 else None
            if not repo_link:
                continue
            full_name = repo_link.get_text("", strip=True).replace(" ", "")
            parts = full_name.split("/")
            if len(parts) != 2:
                continue
            owner, repo = parts
            url = "https://github.com" + repo_link.get("href")
            desc_node = article.find("p")
            description_en = desc_node.get_text(" ", strip=True) if desc_node else ""
            star_link = article.find("a", href=lambda x: x and x.endswith("/stargazers"))
            fork_link = article.find("a", href=lambda x: x and x.endswith("/forks"))
            stars_period = 0
            for span in article.find_all("span"):
                text = span.get_text(" ", strip=True).lower()
                if any(k in text for k in ("stars today", "stars this week", "stars this month")):
                    stars_period = parse_int(text)
                    break
            projects.append({
                "name": full_name,
                "owner": owner,
                "repo": repo,
                "url": url,
                "description_en": description_en,
                "description_zh": description_en,
                "stars": parse_int(star_link.get_text(strip=True) if star_link else "0"),
                "forks": parse_int(fork_link.get_text(strip=True) if fork_link else "0"),
                "stars_period": stars_period,
            })
        except Exception as exc:
            print(f"解析项目时出错: {exc}")
    if len(projects) < MIN_PARSED_PROJECTS:
        raise RuntimeError(f"解析结果过少，仅 {len(projects)} 个项目，页面结构可能已变化")
    return projects


def match_keywords(text: str) -> tuple[list[str], int]:
    matched, score = [], 0
    for pattern, label, weight in KEYWORD_SPECS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            matched.append(label)
            score += weight
    return sorted(set(matched)), score


def derive_tags(matched_keywords: list[str]) -> list[str]:
    tags: set[str] = set()
    lowered = [kw.lower() for kw in matched_keywords]
    for tag, tag_keywords in TAG_MAP.items():
        if any(any(tk in kw for tk in tag_keywords) for kw in lowered):
            tags.add(tag)
    if not tags and lowered:
        tags.add("ai")
    return sorted(tags)


def fallback_translate_to_zh(description_en: str, max_len: int = 200) -> str:
    translated = description_en or ""
    replacements = {
        "agent": "智能体",
        "agents": "智能体",
        "framework": "框架",
        "tool": "工具",
        "tools": "工具",
        "browser": "浏览器",
        "speech": "语音",
        "robot": "机器人",
        "robotics": "机器人技术",
        "vision": "视觉",
        "multimodal": "多模态",
        "memory": "记忆",
        "database": "数据库",
        "open source": "开源",
        "inference": "推理",
        "training": "训练",
    }
    for en, zh in replacements.items():
        translated = re.sub(rf"\b{re.escape(en)}\b", zh, translated, flags=re.IGNORECASE)
    translated = translated.strip()
    if not translated:
        return ""
    return ("这是一个" + translated)[:max_len] + ("..." if len(translated) > max_len else "")


def generate_summary_with_openrouter(project: dict[str, Any], max_len: int = 200) -> str:
    description_en = project.get("description_en", "")
    if not description_en:
        return ""
    if not OPENROUTER_API_KEY:
        return fallback_translate_to_zh(description_en, max_len)
    prompt = (
        "请基于下面这个 GitHub 开源项目的信息，生成一段产品介绍型的中文简介。"
        "要求：\n"
        "1. 不要逐字翻译原文；\n"
        "2. 风格像中文产品介绍或技术媒体项目卡片；\n"
        "3. 重点说明这个项目是什么、主要做什么、适合什么场景；\n"
        "4. 语气简洁、自然、专业；\n"
        "5. 尽量全部改写成自然中文，除非项目名或极少数无法自然翻译的专有名词；\n"
        "6. 不要编造原文没有的信息；\n"
        "7. 只输出 1 句话中文简介。\n"
        "8. 尽量采用类似这样的表达：『这是一个……的开源项目/工具/框架，适合……场景。』\n\n"
        f"项目名：{project.get('name', '')}\n"
        f"英文简介：{description_en}\n"
        f"标签：{', '.join(project.get('tags', []))}\n"
        f"相关关键词：{', '.join(project.get('matched_keywords', []))}"
    )
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": "你是一个专业的技术编辑，擅长把英文项目说明改写成简洁准确的中文项目简介。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
    }
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/Samn10954/github-trending-ai",
        "X-Title": "github-trending-ai-translator",
    }
    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=45)
        response.raise_for_status()
        data = response.json()
        translated = data["choices"][0]["message"]["content"].strip()
        return translated[:max_len] + ("..." if len(translated) > max_len else "")
    except Exception as exc:
        print(f"OpenRouter 翻译失败: {exc}，回退到术语翻译")
        return fallback_translate_to_zh(description_en, max_len)


def filter_projects(projects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    filtered = []
    for project in projects:
        keywords_name, score_name = match_keywords(project["name"])
        keywords_desc, score_desc = match_keywords(project["description_en"])
        matched_keywords = sorted(set(keywords_name + keywords_desc))
        score = score_name * 2 + score_desc
        if matched_keywords and score >= 3:
            project["matched_keywords"] = matched_keywords
            project["tags"] = derive_tags(matched_keywords)
            project["relevance_score"] = score
            project["description_zh"] = generate_summary_with_openrouter(project)
            filtered.append(project)
    return filtered


def save_results(projects: list[dict[str, Any]], date_str: str) -> tuple[Path, Path]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"date": date_str, "period": PERIOD, "count": len(projects), "projects": projects}
    json_path = DATA_DIR / f"{date_str}.json"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path = DATA_DIR / f"{date_str}.md"
    lines = [
        f"# GitHub Trending AI 项目 ({date_str})", "", f"周期：**{PERIOD}**", "",
        f"共收集 **{len(projects)}** 个相关项目", "",
        "| 项目 | 中文简介 | Stars | 周期新增 | Forks | Tags |",
        "|------|----------|-------|----------|-------|------|",
    ]
    for p in projects:
        desc = p["description_zh"][:60] + ("..." if len(p["description_zh"]) > 60 else "")
        tags = ", ".join(p.get("tags", []))
        lines.append(f"| [{p['name']}]({p['url']}) | {desc} | {p['stars']} | {p['stars_period']} | {p['forks']} | {tags} |")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def update_index() -> None:
    index_path = DATA_DIR / "index.json"
    dates = sorted([p.stem for p in DATA_DIR.glob("*.json") if p.name != "index.json"], reverse=True)
    index_path.write_text(json.dumps({"dates": dates}, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始采集 GitHub Trending ({PERIOD})...")
    html = fetch_trending()
    raw_projects = parse_trending(html)
    filtered_projects = filter_projects(raw_projects)
    filtered_projects.sort(key=lambda i: (i["stars_period"], i["stars"]), reverse=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    json_path, md_path = save_results(filtered_projects, date_str)
    update_index()
    print(f"结果已保存: {json_path} / {md_path}")


if __name__ == "__main__":
    main()
