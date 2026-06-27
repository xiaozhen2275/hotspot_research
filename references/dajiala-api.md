# 大加拉 API 说明

修改请求字段、排查接口错误、解释视频播放问题时读取本文件。

## 凭证

使用环境变量：

- `DAJIALA_API_KEY`：必填。
- `DAJIALA_VERIFYCODE`：可选；账号没有设置 verifycode 时传空字符串。

不要把 API Key 写入报告、HTML、JSON、Git 提交、截图或聊天消息。

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
