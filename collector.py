#!/usr/bin/env python3
"""
GitHub Trending AI 采集器
- 抓取 GitHub Trending（weekly）
- 过滤 AI / 具身智能相关项目
- 生成标准化 JSON / Markdown 数据
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
TRENDING_URL = "https://github.com/trending?since=weekly"
PERIOD = "weekly"
MIN_PARSED_PROJECTS = 5

TAG_MAP = {
    "agent": ["agent", "agentic", "autonomous"],
    "llm": ["llm", "gpt", "claude", "gemini", "language model"],
    "robotics": [
        "robotics", "robot", "embodied", "humanoid", "physical ai",
        "slam", "navigation", "mapping", "manipulation", "grasp", "dexterous",
    ],
    "vision": ["vision", "computer vision", "cv"],
    "multimodal": ["multimodal", "vlm", "image-text", "video-understanding"],
    "speech": ["speech", "tts", "stt", "voice", "audio"],
    "rag": ["rag", "retrieval", "knowledge graph"],
    "training": ["training", "inference", "cuda", "gpu", "neural", "deep learning"],
}

KEYWORD_SPECS = [
    (r"\bai\b", "ai", 2),
    (r"\bllm\b", "llm", 3),
    (r"\bgpt\b", "gpt", 2),
    (r"\bclaude\b", "claude", 2),
    (r"\bgemini\b", "gemini", 2),
    (r"\bagent\b", "agent", 3),
    (r"\bagentic\b", "agentic", 3),
    (r"\bautonomous\b", "autonomous", 2),
    (r"\brobotics?\b", "robotics", 3),
    (r"\brobot\b", "robot", 2),
    (r"\bembodied\b", "embodied", 3),
    (r"\bhumanoid\b", "humanoid", 3),
    (r"\bcomputer vision\b", "computer vision", 3),
    (r"\bcv\b", "cv", 1),
    (r"\bvision\b", "vision", 1),
    (r"\bmultimodal\b", "multimodal", 3),
    (r"\bvlm\b", "vlm", 3),
    (r"\bmachine learning\b", "machine learning", 2),
    (r"\bdeep learning\b", "deep learning", 2),
    (r"\bneural\b", "neural", 1),
    (r"\bspeech\b", "speech", 2),
    (r"\btts\b", "tts", 3),
    (r"\bstt\b", "stt", 3),
    (r"\bvoice\b", "voice", 1),
    (r"\baudio\b", "audio", 1),
    (r"\brag\b", "rag", 3),
    (r"\bretrieval\b", "retrieval", 2),
    (r"\bknowledge graph\b", "knowledge graph", 2),
    (r"\bcuda\b", "cuda", 2),
    (r"\bgpu\b", "gpu", 2),
    (r"\binference\b", "inference", 2),
    (r"\btraining\b", "training", 2),
    (r"\bslam\b", "slam", 3),
    (r"\bnavigation\b", "navigation", 2),
    (r"\bmapping\b", "mapping", 1),
    (r"\bmanipulation\b", "manipulation", 3),
    (r"\bgrasp\b", "grasp", 2),
    (r"\bdexterous\b", "dexterous", 2),
]


def fetch_trending() -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122 Safari/537.36"
        )
    }
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
                if "stars today" in text or "stars this week" in text:
                    stars_period = parse_int(text)
                    break

            projects.append(
                {
                    "name": full_name,
                    "owner": owner,
                    "repo": repo,
                    "url": url,
                    "description_en": description_en,
                    "description_zh": description_en,
                    "stars": parse_int(star_link.get_text(strip=True) if star_link else "0"),
                    "forks": parse_int(fork_link.get_text(strip=True) if fork_link else "0"),
                    "stars_period": stars_period,
                }
            )
        except Exception as exc:  # noqa: BLE001
            print(f"解析项目时出错: {exc}")

    if len(projects) < MIN_PARSED_PROJECTS:
        raise RuntimeError(f"解析结果过少，仅 {len(projects)} 个项目，页面结构可能已变化")

    return projects


def match_keywords(text: str) -> tuple[list[str], int]:
    matched: list[str] = []
    score = 0
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


def translate_to_zh(description_en: str, max_len: int = 200) -> str:
    """使用 Google Translate API 翻译简介"""
    from googletrans import Translator
    translator = Translator()
    
    if not description_en or len(description_en) > max_len * 2:
        return description_en[:max_len] + "..." if len(description_en) > max_len else description_en
    
    try:
        result = translator.translate(description_en, dest='zh-cn')
        translated = result.text
        return translated[:max_len] + "..." if len(translated) > max_len else translated
    except Exception as e:
        print(f"翻译失败: {e}, 使用原文")
        return description_en[:max_len] + "..." if len(description_en) > max_len else description_en


def filter_projects(projects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    filtered: list[dict[str, Any]] = []
    for project in projects:
        name_text = project["name"]
        desc_text = project["description_en"]
        keywords_name, score_name = match_keywords(name_text)
        keywords_desc, score_desc = match_keywords(desc_text)
        matched_keywords = sorted(set(keywords_name + keywords_desc))
        score = score_name * 2 + score_desc
        if matched_keywords and score >= 3:
            project["matched_keywords"] = matched_keywords
            project["tags"] = derive_tags(matched_keywords)
            project["relevance_score"] = score
            project["description_zh"] = translate_to_zh(project["description_en"])
            filtered.append(project)
    return filtered


def save_results(projects: list[dict[str, Any]], date_str: str) -> tuple[Path, Path]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    payload = {
        "date": date_str,
        "period": PERIOD,
        "count": len(projects),
        "projects": projects,
    }

    json_path = DATA_DIR / f"{date_str}.json"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md_path = DATA_DIR / f"{date_str}.md"
    lines = [
        f"# GitHub Trending AI 项目 ({date_str})",
        "",
        f"周期：**{PERIOD}**",
        "",
        f"共收集 **{len(projects)}** 个相关项目",
        "",
        "| 项目 | 中文简介 | Stars | 周期新增 | Forks | Tags |",
        "|------|----------|-------|----------|-------|------|",
    ]
    for p in projects:
        desc = p["description_zh"][:60] + ("..." if len(p["description_zh"]) > 60 else "")
        tags = ", ".join(p.get("tags", []))
        lines.append(
            f"| [{p['name']}]({p['url']}) | {desc} | {p['stars']} | {p['stars_period']} | {p['forks']} | {tags} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return json_path, md_path


def update_index() -> None:
    index_path = DATA_DIR / "index.json"
    dates = sorted(
        [path.stem for path in DATA_DIR.glob("*.json") if path.name != "index.json"],
        reverse=True,
    )
    index_path.write_text(json.dumps({"dates": dates}, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始采集 GitHub Trending...")
    html = fetch_trending()
    raw_projects = parse_trending(html)
    print(f"共获取 {len(raw_projects)} 个 Trending 项目")

    filtered_projects = filter_projects(raw_projects)
    filtered_projects.sort(key=lambda item: (item["stars_period"], item["stars"]), reverse=True)
    print(f"AI/具身智能相关项目: {len(filtered_projects)} 个")

    date_str = datetime.now().strftime("%Y-%m-%d")
    json_path, md_path = save_results(filtered_projects, date_str)
    update_index()

    print("结果已保存:")
    print(f"  - JSON: {json_path}")
    print(f"  - Markdown: {md_path}")
    print("\n=== 预览 (前5个) ===")
    for project in filtered_projects[:5]:
        print(f"- {project['name']}: ⭐+{project['stars_period']} [{', '.join(project.get('tags', []))}]")


if __name__ == "__main__":
    main()
