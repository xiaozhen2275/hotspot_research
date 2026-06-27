# video-hotspot-research

基于大加拉/极致了 API 抓取微信公众号文章和微信视频号内容，并生成 Markdown、HTML、JSON 热点报告。

适合：

- 公众号/视频号运营者做选题监控
- 课程学员做热点研究
- 内容团队做竞品观察
- AI 工具、Agent、工作流等主题的素材库建设

## 安装

把本目录复制到 Codex skills 目录：

```bash
~/.codex/skills/video-hotspot-research
```

安装后重启 Codex。

## 配置 API Key

把大加拉 API Key 放到环境变量：

```bash
export DAJIALA_API_KEY="your_key"
```

如果你的账号需要 verifycode：

```bash
export DAJIALA_VERIFYCODE="your_verifycode"
```

不要把 API Key 提交到 GitHub。

## 快速开始

使用 Codex 内置主题：

```bash
python scripts/hotspot_research.py \
  --profile codex \
  --platform both \
  --output-dir ./output
```

使用自定义主题：

```bash
python scripts/hotspot_research.py \
  --topic "AI Agent" \
  --platform both \
  --keywords "AI Agent,智能体,自动化工作流" \
  --output-dir ./output
```

默认会抓取：

- 10 条微信公众号文章
- 5 条微信视频号内容
- 视频会默认下载为本地 MP4，保证 HTML 报告可播放

修改数量：

```bash
python scripts/hotspot_research.py \
  --topic "AI 编程" \
  --platform both \
  --keywords "AI 编程,Codex,Claude Code" \
  --article-limit 20 \
  --video-limit 10 \
  --output-dir ./output
```

只生成视频号元数据，不下载视频：

```bash
python scripts/hotspot_research.py \
  --topic "AI 视频生成" \
  --platform video \
  --keywords "AI 视频生成,AIGC 视频" \
  --no-download-video \
  --output-dir ./output
```

## 输出结构

每次运行会生成：

```text
output-dir/
└── YYYY-MM-DD-topic-热点/
    ├── report.html
    ├── report.md
    ├── raw_responses.json
    ├── selected_items.json
    ├── run_meta.json
    ├── diagnosis.md              # 结果不足目标数量时生成
    └── assets/
        └── video-*.mp4
```

## 视频号播放说明

关键词搜索接口返回的视频地址不一定是浏览器可直接播放的标准 MP4。

本工具会调用详情/可下载接口，把视频下载到本地，再在 `report.html` 中引用 `assets/video-*.mp4`。带 API Key 的播放地址不会写入报告。

下载的视频仅用于内部选题研究和预览。请勿在未授权的情况下转载、发布或二次分发。

## 示例案例

查看 `examples/`：

- `examples/wechat-article-codex/report.md`
- `examples/wechat-article-codex/report.html`
- `examples/wechat-channel-codex/report.md`
- `examples/wechat-channel-codex/report.html`

视频号示例不包含 MP4 文件。真实运行并启用视频下载时，会生成 `assets/video-*.mp4`。

## 内置主题

- `codex`
- `ai-agent`
- `ai-video`
- `prompt-engineering`

## 常见问题

- `DAJIALA_API_KEY is not set`：请先配置环境变量。
- 结果太少：增加关键词、扩大 `--period`，或增加 `--pages`。
- HTML 乱码：用支持 UTF-8 的浏览器打开；模板会写入 UTF-8 with BOM。
- 视频不能播放：检查 `report.html` 是否引用本地 `assets/*.mp4`，而不是 `finder.video.qq.com` 加密流。
