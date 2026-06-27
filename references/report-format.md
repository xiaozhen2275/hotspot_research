# 报告格式

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
        └── video-*.mp4            # 启用视频下载时生成
```

每条入选内容包含：

- platform：平台
- score：评分
- topic_category：主题分类
- title：标题
- account_name：账号名称
- published_at：发布时间
- key_info：关键信息
- reference_value：可借鉴点
- selection_reason：入选理由
- source_url：原文链接或本地视频路径

视频号内容：

- `source_url` 优先使用本地 MP4 路径。
- JSON 中保留 `object_id` 和 `object_nonce_id`，便于后续刷新链接。
- 不保存带 API Key 的 `play_url` 或 `download_url`。
