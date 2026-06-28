# 视频号热点抓取

基于大加拉/极致了 API 抓取微信公众号文章和微信视频号内容，并生成 Markdown、HTML、JSON 热点报告。

> 技术调用名仍为 `$video-hotspot-research`，用于 Codex 中触发本 skill。

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

### 如何获取 www.dajiala.com 的 API Key

1. 打开大加拉/极致了官网：`https://www.dajiala.com/`
2. 登录账号：`https://www.dajiala.com/main/login`
3. 进入账号后台，查找“API 接口”“开放接口”“接口服务”“开发者接口”“我的接口”“接口密钥”等相关入口。
4. 确认账号已开通需要的接口能力：
   - 微信公众号关键词搜索
   - 微信视频号关键词搜索
   - 微信视频号详情/下载
5. 创建或复制 API Key。
6. 如果后台要求 `verifycode`，同时复制该值；如果没有设置，可以不配置 `DAJIALA_VERIFYCODE`。

如果你在后台找不到 API Key 入口，通常说明账号尚未开通 API 服务。可以联系大加拉/极致了客服或商务，说明你需要公众号和视频号数据接口。

### Windows 配置示例

PowerShell 临时配置，只在当前窗口有效：

```powershell
$env:DAJIALA_API_KEY="your_key"
$env:DAJIALA_VERIFYCODE="your_verifycode"
```

PowerShell 用户级长期配置：

```powershell
[Environment]::SetEnvironmentVariable("DAJIALA_API_KEY", "your_key", "User")
[Environment]::SetEnvironmentVariable("DAJIALA_VERIFYCODE", "your_verifycode", "User")
```

## 在 Codex 中使用

安装并重启 Codex 后，直接在 Codex 对话里说你要抓什么主题、抓哪些平台、保存到哪里即可。

最简单的说法：

```text
使用 $video-hotspot-research 抓取 Codex 相关的公众号文章和视频号内容，生成热点报告，保存到 ./output
```

Codex 会自动完成：

- 检查大加拉 API Key
- 选择关键词和平台
- 抓取微信公众号文章和视频号内容
- 对内容评分、过滤广告和低相关内容
- 下载视频号本地 MP4
- 生成 `report.html`、`report.md`、`selected_items.json` 等文件
- 如果数量不足，生成 `diagnosis.md` 说明原因

默认会抓取：

- 10 条微信公众号文章
- 5 条微信视频号内容
- 视频会默认下载为本地 MP4，保证 HTML 报告可播放

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

## 使用案例

下面这些都可以直接复制到 Codex 中使用。

### 案例 1：抓取 Codex 热点

```text
使用 $video-hotspot-research 抓取 Codex、OpenAI Codex、Claude Code 相关的微信公众号文章和视频号内容，生成热点报告，保存到 ./output
```

适合观察 Codex、OpenAI Codex、Claude Code、AI 编程工具等内容趋势。

### 案例 2：抓取 AI Agent 选题

```text
使用 $video-hotspot-research 抓取 AI Agent、智能体、自动化工作流、MCP、工具调用相关的公众号文章和视频号内容。公众号抓取 20 条，视频号抓取 10 条，生成热点报告，保存到 ./output
```

适合课程学员、内容团队做智能体、自动化工作流、MCP、工具调用等方向的选题库。

### 案例 3：只抓公众号文章

```text
使用 $video-hotspot-research 只抓微信公众号文章，主题是 AI 编程，关键词包括 AI 编程、Codex、Claude Code、Cursor，抓取 20 条，生成热点报告，保存到 ./output
```

适合做公众号文章选题、竞品标题分析、长文素材库。

### 案例 4：只抓视频号并下载本地 MP4

```text
使用 $video-hotspot-research 只抓视频号内容，主题是 AI 视频生成，关键词包括 AI 视频生成、AIGC 视频、可灵、Runway、Sora，抓取 8 条，下载本地 MP4，生成 HTML 热点报告，保存到 ./output
```

适合做视频号选题监控。报告会引用本地 MP4，方便直接预览。

### 案例 5：只保留视频号元数据，不下载视频

```text
使用 $video-hotspot-research 只抓视频号元数据，主题是提示词工程，关键词包括提示词工程、Prompt、AI 工作流，抓取 10 条，不下载视频，只生成选题分析报告，保存到 ./output
```

适合只做标题、账号、互动数据和选题角度分析，不保存视频文件。

### 案例 6：保存到指定素材库

```text
使用 $video-hotspot-research 抓取 AI 产品相关的微信公众号文章和视频号内容，生成热点报告，保存到 D:\workplace\01.workplace\super_person\超级个体\02-素材库\热点报告
```

适合已经有固定素材库目录的用户。

## 开发者与自动化用法（可选）

非技术用户可以忽略本节。如果你要做定时任务或批处理，可以直接运行脚本：

```bash
python scripts/hotspot_research.py \
  --topic "Codex" \
  --platform both \
  --keywords "Codex,OpenAI Codex,Claude Code" \
  --article-limit 10 \
  --video-limit 5 \
  --output-dir ./output
```

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
