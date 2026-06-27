# 大加拉 API 说明

修改请求字段、排查接口错误、解释视频播放问题时读取本文件。

## 凭证

使用环境变量：

- `DAJIALA_API_KEY`：必填。
- `DAJIALA_VERIFYCODE`：可选；账号没有设置 verifycode 时传空字符串。

不要把 API Key 写入报告、HTML、JSON、Git 提交、截图或聊天消息。

## API Key 获取指南

大加拉/极致了的 API Key 通常需要在官网账号后台获取。公开入口：

- 官网：`https://www.dajiala.com/`
- 登录入口：`https://www.dajiala.com/main/login`

建议流程：

1. 打开官网并登录账号。
2. 在后台查找和 API 相关的入口，常见名称可能是“API 接口”“开放接口”“接口服务”“开发者接口”“我的接口”“接口密钥”。
3. 如果后台展示了接口套餐或余额，确认账号已开通需要的接口能力，例如公众号关键词搜索、视频号关键词搜索、视频号详情/下载等。
4. 创建或复制 API Key。
5. 如果后台要求设置 `verifycode`，同时记录该值；如果没有设置，脚本会默认传空字符串。
6. 将 Key 配置到本地环境变量，不要写进代码或仓库：

```bash
export DAJIALA_API_KEY="你的大加拉 API Key"
export DAJIALA_VERIFYCODE="你的 verifycode，可选"
```

Windows PowerShell 临时配置：

```powershell
$env:DAJIALA_API_KEY="你的大加拉 API Key"
$env:DAJIALA_VERIFYCODE="你的 verifycode，可选"
```

Windows 用户级长期配置：

```powershell
[Environment]::SetEnvironmentVariable("DAJIALA_API_KEY", "你的大加拉 API Key", "User")
[Environment]::SetEnvironmentVariable("DAJIALA_VERIFYCODE", "你的 verifycode，可选", "User")
```

如果后台找不到 API Key：

- 检查账号是否购买或开通 API 服务。
- 联系大加拉/极致了客服或商务，说明需要公众号文章搜索、视频号搜索、视频号详情/下载接口。
- 先用小范围参数测试，避免一次性消耗过多余额。

## 微信公众号文章

接口：

`POST https://www.dajiala.com/fbmain/monitor/v3/kw_search`

典型请求体：

```json
{
  "key": "从 DAJIALA_API_KEY 读取",
  "kw": "Codex",
  "sort_type": 2,
  "mode": 3,
  "period": 30,
  "page": 1,
  "any_kw": "",
  "ex_kw": ""
}
```

说明：

- `sort_type=1` 按阅读数排序；`sort_type=2` 按时间排序。
- `mode=3` 搜标题和正文。
- 每页通常最多返回约 20 条，可能按返回数量扣费。

## 微信视频号

关键词搜索接口：

`POST https://www.dajiala.com/fbmain/monitor/v3/wxvideo`

请求体：

```json
{
  "key": "从 DAJIALA_API_KEY 读取",
  "verifycode": "",
  "type": 4,
  "keywords": "Codex"
}
```

详情/下载接口：

`POST https://www.dajiala.com/fbmain/monitor/v3/wxvideo?object_id=...&object_nonce_id=...&key=...&verifycode=&type=3`

重要经验：

- 关键词搜索会返回标题/描述、账号、互动数据、`object_id`、`object_nonce_id`、媒体字段等。
- 不要把关键词搜索结果里的 `media.url` 当作浏览器播放链接。
- `media.url + url_token` 即使返回 `200 video/mp4`，也可能是加密流，没有标准 MP4 的 `ftyp` 文件头。
- 应调用详情/下载接口获取 `play_url` 或 `download_url`。
- 详情接口 URL 会包含 API Key，不能写进报告。
- 正确做法是下载到本地 `assets/video-*.mp4`，再在 HTML 中引用本地文件。
