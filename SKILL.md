---
name: video-hotspot-research
description: 使用大加拉/极致了 API 抓取指定主题的微信公众号文章和微信视频号内容，进行热点评分、过滤、视频本地 MP4 下载，并生成 Markdown/HTML/JSON 热点报告。适用于公众号/视频号运营者、课程学员、内容团队做选题监控、素材库建设、竞品观察、AI 工具/Agent/工作流等主题研究，或用户要求基于 www.dajiala.com 数据生成热点报告时。
---

# 视频热点研究

把一个主题变成一份可复用的公众号/视频号热点报告。

## 前置配置

运行前检查环境变量：

- `DAJIALA_API_KEY`：必填。
- `DAJIALA_VERIFYCODE`：可选；账号没有设置时传空字符串。

严禁把 API Key 写入报告、HTML、JSON、Git 提交、截图或聊天回复。

## 主脚本

基础命令：

```bash
python scripts/hotspot_research.py \
  --topic "Codex" \
  --platform both \
  --keywords "Codex,OpenAI Codex,Claude Code" \
  --output-dir ./output
```

默认值：

- 公众号文章：`--article-limit 10`
- 视频号内容：`--video-limit 5`
- 视频默认下载为本地 MP4，确保 HTML 可以播放。
- 只有用户明确要“只看元数据”时，才使用 `--no-download-video`。

内置主题：

```bash
python scripts/hotspot_research.py --profile codex --platform both --output-dir ./output
python scripts/hotspot_research.py --profile ai-agent --platform both --output-dir ./output
python scripts/hotspot_research.py --profile ai-video --platform both --output-dir ./output
python scripts/hotspot_research.py --profile prompt-engineering --platform both --output-dir ./output
```

## 工作流

1. 只有当主题、平台、输出目录或数量缺失时才追问。
2. 修改接口参数或排查接口错误前，读取 `references/dajiala-api.md`。
3. 修改过滤或评分前，读取 `references/scoring-and-filtering.md`。
4. 运行 `scripts/hotspot_research.py`。
5. 检查 `run_meta.json`、`selected_items.json`、`report.md` 和 `report.html`。
6. 如果数量不足，检查 `diagnosis.md` 并向用户说明原因。

## 视频号强规则

视频号关键词搜索接口会返回媒体字段，但这些字段不能直接当作浏览器播放链接。

必须遵守：

- 不要把关键词搜索结果里的 `media.url` 直接写成播放链接。
- 不要因为 `media.url + url_token` 返回 `200 video/mp4` 就认为可播放；它可能是加密流，文件头没有标准 MP4 的 `ftyp`。
- 应调用详情/可下载接口获取 `play_url` 或 `download_url`。
- 这些 URL 可能包含 API Key，严禁持久化到报告或 JSON。
- 默认下载到 `assets/video-*.mp4`，HTML 只引用本地 MP4。
- 在 JSON 中保留 `object_id` 和 `object_nonce_id`，便于之后刷新链接。

## 输出结构

每次运行生成：

```text
output-dir/
└── YYYY-MM-DD-topic-热点/
    ├── report.html
    ├── report.md
    ├── raw_responses.json
    ├── selected_items.json
    ├── run_meta.json
    ├── diagnosis.md              # 数量不足时生成
    └── assets/
        └── video-*.mp4
```

报告用于选题研究、内容策划和内部复盘，不复制全文，不声称拥有第三方视频版权。

## 常见问题

- 缺少 key：让用户设置 `DAJIALA_API_KEY`。
- 结果太少：增加同义词，扩大 `--period`，增加 `--pages`，或放宽过滤。
- 视频不能播放：确认 HTML 引用的是本地 `assets/*.mp4`，不是大加拉 `play_url` 或微信 `stodownload` 加密流。
- 中文乱码：HTML 使用 UTF-8 with BOM（`utf-8-sig`），并包含 `<meta charset="utf-8">`。
