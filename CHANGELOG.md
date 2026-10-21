# 修正与变更日志

原始快照只增不改。任何口径变化、数据源增减、已知问题和修正说明，都只记录在这里，不改动历史文件。

格式：`日期 · 数据集 · 说明`

## 2026-10-21

- 全部 · **账本创世日**。哈希链从 `ledger/2026-10-21.json` 开始（`prev_ledger_sha256` 为空）。
- 全部 · 当天账本启用前，曾为调试采集代码多次重采当天数据；以账本记录的最终文件为准。
- `appstore_cn` · Apple 旧版 RSS 接口每个榜单最多返回 100 条（请求 200 条无效），口径为前 100 名。
- `appstore_cn`、`apple_podcasts_cn`、`appstore_global`、`huggingface_models`、`llm_api_prices`、`steam_cn`、`hk_weather_forecast`、`hk_carpark_vacancy` · 开始收录。
