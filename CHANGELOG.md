# 修正与变更日志

原始快照只增不改。任何口径变化、数据源增减、已知问题和修正说明，都只记录在这里，不改动历史文件。

格式：`日期 · 数据集 · 说明`

## 2026-10-21

- `steam_cn` · **暂停采集**。Steam 商店对 GitHub Actions 服务器持续返回 502（重试 5 次、减小分页后仍失败），2026-10-21 无数据。计划迁移到国内服务器后恢复，恢复前的日期在账本中如实缺失。
- 全部 · **账本创世日**。哈希链从 `ledger/2026-10-21.json` 开始（`prev_ledger_sha256` 为空）。
- 全部 · 当天账本启用前，曾为调试采集代码多次重采当天数据；以账本记录的最终文件为准。
- `appstore_cn` · Apple 旧版 RSS 接口每个榜单最多返回 100 条（请求 200 条无效），口径为前 100 名。
- `appstore_cn`、`apple_podcasts_cn`、`appstore_global`、`huggingface_models`、`llm_api_prices`、`steam_cn`、`hk_weather_forecast`、`hk_carpark_vacancy` · 开始收录。
