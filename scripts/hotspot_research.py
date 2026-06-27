#!/usr/bin/env python3
"""Collect Dajiala WeChat article / Channels video hotspots and build reports."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


ARTICLE_URL = "https://www.dajiala.com/fbmain/monitor/v3/kw_search"
WXVIDEO_URL = "https://www.dajiala.com/fbmain/monitor/v3/wxvideo"

PROFILES = {
    "codex": {
        "topic": "Codex",
        "keywords": ["Codex", "OpenAI Codex", "Claude Code"],
        "topic_keywords": ["Codex", "OpenAI", "Claude Code", "AI编程", "Agent", "工作流"],
    },
    "ai-agent": {
        "topic": "AI Agent",
        "keywords": ["AI Agent", "智能体", "自动化工作流"],
        "topic_keywords": ["AI Agent", "智能体", "工作流", "工具调用", "MCP"],
    },
    "ai-video": {
        "topic": "AI 视频生成",
        "keywords": ["AI 视频生成", "AIGC 视频", "视频生成模型"],
        "topic_keywords": ["视频生成", "AIGC", "AI视频", "可灵", "Runway", "Sora"],
    },
    "prompt-engineering": {
        "topic": "提示词工程",
        "keywords": ["提示词工程", "Prompt", "提示词"],
        "topic_keywords": ["提示词", "Prompt", "工作流", "模板", "案例"],
    },
}

DEFAULT_EXCLUDE = [
    "广告",
    "招商",
    "课程招生",
    "训练营",
    "招聘",
    "带货",
    "成人",
    "擦边",
    "规避审核",
    "去水印",
    "股市",
    "楼市",
    "留学考试",
    "校园活动",
    "生活服务",
    "高风险",
]

SCENE_TERMS = ["实战", "实践", "落地", "案例", "复盘", "流程", "步骤", "教程", "手把手", "项目", "部署", "接入", "搭建"]
NEW_TERMS = ["2026", "2025", "最新", "发布", "升级", "API", "SDK", "MCP", "Agent", "智能体", "工作流", "自动化", "插件"]
ASSET_TERMS = ["代码", "脚本", "模板", "清单", "SOP", "Prompt", "提示词", "开源", "GitHub", "配置", "命令"]


def now_str() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def slugify(value: str) -> str:
    value = re.sub(r"[\\/:*?\"<>|]+", "-", value.strip())
    value = re.sub(r"\s+", "-", value)
    return value[:80] or "topic"


def split_csv(values: list[str] | None) -> list[str]:
    if not values:
        return []
    result: list[str] = []
    for value in values:
        for part in re.split(r"[,，]", value):
            part = part.strip()
            if part:
                result.append(part)
    return result


def request_json(url: str, payload: dict[str, Any] | None = None, *, params: dict[str, Any] | None = None, timeout: int = 30) -> dict[str, Any]:
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    data = None
    headers = {"User-Agent": "Mozilla/5.0"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", "replace"))


def download_file(url: str, path: Path, timeout: int = 180) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        path.write_bytes(response.read())


def clean_text(value: Any) -> str:
    value = "" if value is None else str(value)
    value = re.sub(r"<[^>]+>", "", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def contains_any(text: str, terms: list[str]) -> list[str]:
    lower = text.lower()
    return [term for term in terms if term.lower() in lower]


def score_item(title: str, content: str, topic_terms: list[str], read: int = 0, likes: int = 0, forwards: int = 0, comments: int = 0) -> tuple[int, dict[str, int], list[str]]:
    text = f"{title}\n{content}"
    topic_hits = contains_any(text, topic_terms)
    scene_hits = contains_any(text, SCENE_TERMS)
    new_hits = contains_any(text, NEW_TERMS)
    asset_hits = contains_any(text, ASSET_TERMS)
    topic_score = min(35, len(topic_hits) * 8 + (15 if topic_hits else 0))
    scene_score = min(25, len(scene_hits) * 5)
    new_score = min(20, len(new_hits) * 4)
    asset_score = min(10, len(asset_hits) * 3)
    heat_raw = read + likes * 5 + forwards * 5 + comments * 5
    heat_score = min(10, heat_raw // 1000 if heat_raw else 0)
    total = int(topic_score + scene_score + new_score + asset_score + heat_score)
    reasons = []
    if topic_hits:
        reasons.append("主题命中：" + "、".join(topic_hits[:6]))
    if scene_hits:
        reasons.append("落地信号：" + "、".join(scene_hits[:6]))
    if new_hits:
        reasons.append("技术信号：" + "、".join(new_hits[:6]))
    if asset_hits:
        reasons.append("资产信号：" + "、".join(asset_hits[:6]))
    if heat_score:
        reasons.append(f"热度信号：read={read}, like={likes}, forward={forwards}, comment={comments}")
    return total, {
        "topic_relevance": topic_score,
        "landing_value": scene_score,
        "trend_value": new_score,
        "reusable_assets": asset_score,
        "heat": heat_score,
    }, reasons


def is_excluded(title: str, content: str, exclude_terms: list[str]) -> tuple[bool, list[str]]:
    hits = contains_any(f"{title}\n{content}", exclude_terms)
    return bool(hits), hits


def collect_articles(api_key: str, args: argparse.Namespace, keywords: list[str], topic_terms: list[str], exclude_terms: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    raw: list[dict[str, Any]] = []
    items_by_url: dict[str, dict[str, Any]] = {}
    for keyword in keywords:
        for page in range(1, args.pages + 1):
            payload = {
                "key": api_key,
                "kw": keyword,
                "sort_type": args.sort_type,
                "mode": 3,
                "period": args.period,
                "page": page,
                "any_kw": args.any_kw or "",
                "ex_kw": args.ex_kw or "",
            }
            try:
                response = request_json(ARTICLE_URL, payload, timeout=args.timeout)
            except Exception as exc:
                response = {"_error": type(exc).__name__, "_message": str(exc)}
            raw.append({"platform": "article", "keyword": keyword, "page": page, "response": response})
            for row in response.get("data") or []:
                url = row.get("url") or row.get("short_link") or row.get("title")
                if not url or url in items_by_url:
                    continue
                title = clean_text(row.get("title"))
                content = clean_text(row.get("content") or row.get("excerpt"))
                excluded, exclude_hits = is_excluded(title, content, exclude_terms)
                score, breakdown, reasons = score_item(
                    title,
                    content,
                    topic_terms,
                    read=int(row.get("read") or 0),
                    likes=int(row.get("praise") or 0),
                    comments=int(row.get("looking") or 0),
                )
                items_by_url[url] = {
                    "platform": "公众号",
                    "score": score,
                    "score_breakdown": breakdown,
                    "topic_category": args.topic,
                    "title": title,
                    "account_name": row.get("wx_name") or "",
                    "published_at": row.get("publish_time_str") or row.get("publish_date") or "",
                    "read": row.get("read"),
                    "like": row.get("praise"),
                    "forward": "",
                    "comment": row.get("looking"),
                    "key_info": content[:220],
                    "reference_value": "可拆解标题、结构、案例、工具链和可复用步骤，用于选题与内容策划。",
                    "selection_reason": "；".join(reasons) or "关键词命中主题。",
                    "source_url": row.get("short_link") or row.get("url") or "",
                    "excluded": excluded,
                    "exclude_hits": exclude_hits,
                }
            time.sleep(args.interval)
    selected = sorted((item for item in items_by_url.values() if not item["excluded"]), key=lambda x: x["score"], reverse=True)
    return selected[: args.article_limit], raw


def video_title(row: dict[str, Any]) -> str:
    desc = row.get("object_desc") or {}
    return clean_text(desc.get("description") or "")


def video_media(row: dict[str, Any]) -> dict[str, Any]:
    media = (row.get("object_desc") or {}).get("media") or []
    return media[0] if media else {}


def collect_videos(api_key: str, args: argparse.Namespace, keywords: list[str], topic_terms: list[str], exclude_terms: list[str], run_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    raw: list[dict[str, Any]] = []
    by_id: dict[str, dict[str, Any]] = {}
    assets_dir = run_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    for keyword in keywords:
        payload = {"key": api_key, "verifycode": os.getenv("DAJIALA_VERIFYCODE", ""), "type": 4, "keywords": keyword}
        try:
            response = request_json(WXVIDEO_URL, payload, timeout=args.timeout)
        except Exception as exc:
            response = {"_error": type(exc).__name__, "_message": str(exc)}
        raw.append({"platform": "wxvideo_search", "keyword": keyword, "response": response})
        for row in response.get("video_object_list") or []:
            object_id = str(row.get("id") or row.get("object_id") or "")
            if not object_id or object_id in by_id:
                continue
            title = video_title(row)
            contact = row.get("contact") or {}
            media = video_media(row)
            content = f"{title}\n{contact.get('signature') or ''}"
            excluded, exclude_hits = is_excluded(title, content, exclude_terms)
            score, breakdown, reasons = score_item(
                title,
                content,
                topic_terms,
                likes=int(row.get("like_count") or 0),
                forwards=int(row.get("forward_count") or 0),
                comments=int(row.get("comment_count") or 0),
            )
            by_id[object_id] = {
                "platform": "视频号",
                "score": score,
                "score_breakdown": breakdown,
                "topic_category": args.topic,
                "title": title,
                "account_name": contact.get("nickname") or row.get("nickname") or "",
                "published_at": dt.datetime.fromtimestamp(int(row.get("createtime") or 0)).strftime("%Y-%m-%d %H:%M:%S") if row.get("createtime") else "",
                "read": "",
                "like": row.get("like_count"),
                "forward": row.get("forward_count"),
                "comment": row.get("comment_count"),
                "key_info": title[:220],
                "reference_value": "可拆解标题表达、系列包装、账号定位和互动数据，迁移到短视频选题与脚本。",
                "selection_reason": "；".join(reasons) or "关键词命中主题。",
                "source_url": "",
                "object_id": object_id,
                "object_nonce_id": row.get("object_nonce_id") or "",
                "cover_url": media.get("cover_url") or media.get("thumb_url") or "",
                "duration_seconds": media.get("video_play_len"),
                "excluded": excluded,
                "exclude_hits": exclude_hits,
            }
        time.sleep(args.interval)
    selected = sorted((item for item in by_id.values() if not item["excluded"]), key=lambda x: x["score"], reverse=True)[: args.video_limit]
    if args.download_video:
        for index, item in enumerate(selected, 1):
            detail_params = {
                "object_id": item["object_id"],
                "object_nonce_id": item.get("object_nonce_id") or "",
                "key": api_key,
                "verifycode": os.getenv("DAJIALA_VERIFYCODE", ""),
                "type": 3,
            }
            try:
                detail = request_json(WXVIDEO_URL, params=detail_params, timeout=args.timeout)
            except Exception as exc:
                detail = {"_error": type(exc).__name__, "_message": str(exc)}
            raw.append({"platform": "wxvideo_detail", "object_id": item["object_id"], "response": scrub_key(detail)})
            source_url = detail.get("download_url") or detail.get("play_url")
            if not source_url:
                item["video_download_error"] = detail.get("msg") or detail.get("_message") or "missing play_url/download_url"
                continue
            filename = f"video-{index}-{item['object_id']}.mp4"
            local_path = assets_dir / filename
            try:
                download_file(source_url, local_path, timeout=max(args.timeout, 180))
                head = local_path.read_bytes()[:64]
                item["local_video_file"] = f"assets/{filename}"
                item["source_url"] = f"assets/{filename}"
                item["local_video_size"] = local_path.stat().st_size
                item["local_video_has_ftyp"] = b"ftyp" in head
            except Exception as exc:
                item["video_download_error"] = f"{type(exc).__name__}: {exc}"
            time.sleep(args.interval)
    return selected, raw


def scrub_key(value: Any) -> Any:
    if isinstance(value, str):
        key = os.getenv("DAJIALA_API_KEY")
        return value.replace(key, "***") if key else value
    if isinstance(value, list):
        return [scrub_key(item) for item in value]
    if isinstance(value, dict):
        return {k: scrub_key(v) for k, v in value.items()}
    return value


def render_markdown(args: argparse.Namespace, run_dir: Path, selected: list[dict[str, Any]], meta: dict[str, Any]) -> None:
    lines = [
        f"# {args.topic} 热点报告",
        "",
        f"生成时间：{meta['generated_at']}",
        f"平台：{args.platform}",
        f"关键词：{', '.join(meta['keywords'])}",
        "",
        "## 概况",
        "",
        f"- 入选内容：{len(selected)} 条",
        f"- 公众号目标：{args.article_limit} 条",
        f"- 视频号目标：{args.video_limit} 条",
        "",
        "## 内容清单",
        "",
    ]
    for index, item in enumerate(selected, 1):
        lines.extend(
            [
                f"### {index}. {item['title']}",
                "",
                f"- 平台：{item['platform']}",
                f"- 评分：{item['score']}",
                f"- 主题分类：{item['topic_category']}",
                f"- 账号：{item['account_name']}",
                f"- 发布时间：{item['published_at']}",
                f"- 关键信息：{item['key_info']}",
                f"- 可借鉴点：{item['reference_value']}",
                f"- 入选理由：{item['selection_reason']}",
                f"- 链接：{item.get('source_url') or ''}",
                "",
            ]
        )
    (run_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")


def render_html(args: argparse.Namespace, run_dir: Path, selected: list[dict[str, Any]], meta: dict[str, Any]) -> None:
    template_path = Path(__file__).resolve().parents[1] / "assets" / "report_template.html"
    if template_path.exists():
        template = template_path.read_text(encoding="utf-8")
    else:
        template = DEFAULT_TEMPLATE
    rows = []
    for index, item in enumerate(selected, 1):
        link = item.get("source_url") or ""
        if item["platform"] == "视频号" and link.endswith(".mp4"):
            media_html = f'<video controls preload="metadata" src="{html.escape(link)}"></video><br><a href="{html.escape(link)}" target="_blank">打开本地 MP4</a>'
        elif link:
            media_html = f'<a href="{html.escape(link)}" target="_blank" rel="noopener noreferrer">打开链接</a>'
        else:
            media_html = ""
        rows.append(
            "<tr>"
            f"<td>{index}</td>"
            f"<td>{html.escape(item['platform'])}</td>"
            f"<td class='score'>{item['score']}</td>"
            f"<td>{html.escape(item['topic_category'])}</td>"
            f"<td class='title'>{html.escape(item['title'])}</td>"
            f"<td>{html.escape(str(item['account_name']))}</td>"
            f"<td>{html.escape(str(item['published_at']))}</td>"
            f"<td>{html.escape(str(item['key_info']))}</td>"
            f"<td>{html.escape(str(item['reference_value']))}</td>"
            f"<td>{html.escape(str(item['selection_reason']))}</td>"
            f"<td>{media_html}</td>"
            "</tr>"
        )
    html_text = template.replace("{{TITLE}}", html.escape(f"{args.topic} 热点报告"))
    html_text = html_text.replace("{{META}}", html.escape(f"关键词：{', '.join(meta['keywords'])} · 平台：{args.platform} · 生成时间：{meta['generated_at']}"))
    html_text = html_text.replace("{{ROWS}}", "\n".join(rows))
    html_text = html_text.replace("{{COUNT}}", str(len(selected)))
    (run_dir / "report.html").write_text(html_text, encoding="utf-8-sig")


DEFAULT_TEMPLATE = """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{{TITLE}}</title></head>
<body><h1>{{TITLE}}</h1><p>{{META}}</p><table><thead><tr><th>#</th><th>平台</th><th>评分</th><th>主题</th><th>标题</th><th>账号</th><th>时间</th><th>关键信息</th><th>可借鉴点</th><th>入选理由</th><th>链接/播放</th></tr></thead><tbody>{{ROWS}}</tbody></table></body></html>"""


def write_diagnosis(args: argparse.Namespace, run_dir: Path, selected: list[dict[str, Any]], raw: list[dict[str, Any]], keywords: list[str], exclude_terms: list[str]) -> None:
    target = (args.article_limit if args.platform in ("article", "both") else 0) + (args.video_limit if args.platform in ("video", "both") else 0)
    if len(selected) >= target:
        return
    errors = []
    for entry in raw:
        response = entry.get("response") or {}
        if response.get("_error") or response.get("code") not in (None, 0):
            errors.append(f"{entry.get('platform')} {entry.get('keyword') or entry.get('object_id')}: {response.get('_error') or response.get('code')} {response.get('_message') or response.get('msg')}")
    lines = [
        f"# {args.topic} 抓取诊断",
        "",
        f"- 实际有效条数：{len(selected)}",
        f"- 目标条数：{target}",
        f"- 平台：{args.platform}",
        f"- 使用关键词：{', '.join(keywords)}",
        f"- 时间范围：最近 {args.period} 天（公众号）",
        f"- 剔除内容类型：{', '.join(exclude_terms)}",
        f"- 接口错误：{'; '.join(errors) if errors else '无明确接口错误'}",
        "",
        "## 没抓满的可能原因",
        "",
        "- 关键词过窄或平台内相关内容不足。",
        "- 过滤词较严格。",
        "- 视频号详情或下载接口返回失败。",
        "- 账号余额不足或 key/verifycode 配置错误。",
        "",
        "## 下次建议",
        "",
        "- 增加同义词、竞品词和中文场景词。",
        "- 放宽过滤词或增大关键词数量。",
        "- 扩大公众号 period 或增加 pages。",
        "- 检查 DAJIALA_API_KEY 和 DAJIALA_VERIFYCODE。",
    ]
    (run_dir / "diagnosis.md").write_text("\n".join(lines), encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dajiala hotspot research for WeChat articles and Channels videos.")
    parser.add_argument("--profile", choices=sorted(PROFILES), help="Use a built-in topic profile.")
    parser.add_argument("--topic", help="Human-readable topic name.")
    parser.add_argument("--keywords", action="append", help="Comma-separated keywords. Repeatable.")
    parser.add_argument("--topic-keywords", action="append", help="Comma-separated scoring keywords. Repeatable.")
    parser.add_argument("--platform", choices=["article", "video", "both"], default="both")
    parser.add_argument("--article-limit", type=int, default=10)
    parser.add_argument("--video-limit", type=int, default=5)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--period", type=int, default=30)
    parser.add_argument("--pages", type=int, default=1)
    parser.add_argument("--sort-type", type=int, choices=[1, 2], default=2, help="1=read count, 2=time")
    parser.add_argument("--any-kw", default="")
    parser.add_argument("--ex-kw", default="")
    parser.add_argument("--exclude-keywords", action="append")
    parser.add_argument("--download-video", dest="download_video", action="store_true", default=True)
    parser.add_argument("--no-download-video", dest="download_video", action="store_false")
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument("--timeout", type=int, default=30)
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    profile = PROFILES.get(args.profile or "", {})
    args.topic = args.topic or profile.get("topic")
    keywords = split_csv(args.keywords) or profile.get("keywords", [])
    topic_terms = split_csv(args.topic_keywords) or profile.get("topic_keywords", []) or keywords
    exclude_terms = DEFAULT_EXCLUDE + split_csv(args.exclude_keywords)
    if not args.topic or not keywords:
        print("Error: provide --topic and --keywords, or use --profile.", file=sys.stderr)
        return 2
    api_key = os.getenv("DAJIALA_API_KEY")
    if not api_key:
        print("Error: DAJIALA_API_KEY is not set.", file=sys.stderr)
        return 2
    run_dir = Path(args.output_dir) / f"{dt.datetime.now().strftime('%Y-%m-%d')}-{slugify(args.topic)}-热点"
    run_dir.mkdir(parents=True, exist_ok=True)
    raw: list[dict[str, Any]] = []
    selected: list[dict[str, Any]] = []
    if args.platform in ("article", "both"):
        article_items, article_raw = collect_articles(api_key, args, keywords, topic_terms, exclude_terms)
        selected.extend(article_items)
        raw.extend(article_raw)
    if args.platform in ("video", "both"):
        video_items, video_raw = collect_videos(api_key, args, keywords, topic_terms, exclude_terms, run_dir)
        selected.extend(video_items)
        raw.extend(video_raw)
    selected = sorted(selected, key=lambda x: x["score"], reverse=True)
    meta = {
        "generated_at": now_str(),
        "topic": args.topic,
        "platform": args.platform,
        "keywords": keywords,
        "topic_keywords": topic_terms,
        "exclude_keywords": exclude_terms,
        "article_limit": args.article_limit,
        "video_limit": args.video_limit,
        "download_video": args.download_video,
    }
    (run_dir / "run_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    (run_dir / "raw_responses.json").write_text(json.dumps(scrub_key(raw), ensure_ascii=False, indent=2), encoding="utf-8")
    (run_dir / "selected_items.json").write_text(json.dumps(selected, ensure_ascii=False, indent=2), encoding="utf-8")
    render_markdown(args, run_dir, selected, meta)
    render_html(args, run_dir, selected, meta)
    write_diagnosis(args, run_dir, selected, raw, keywords, exclude_terms)
    print(json.dumps({"run_dir": str(run_dir), "selected": len(selected), "report_html": str(run_dir / "report.html")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
