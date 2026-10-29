<!-- 本文件由 scripts/health.py 自动生成，请勿手改 -->
# 运行状态

**✅ 一切正常** · 检查日期 2026-10-30 · 检查时间 2026-10-30 01:27（北京时间）

## 各数据集

| 数据集 | 名称 | 采集 | 今天 | 连续天数 | 已存档天数 | 开始日期 |
|---|---|---|---|---|---|---|
| `appstore_cn` | App Store 中国区排行榜 | GitHub | ✅ | 10 | 10 | 2026-10-21 |
| `appstore_global` | 全球 App Store 排行榜 | GitHub | ✅ | 10 | 10 | 2026-10-21 |
| `mi_appstore_rank` | 小米应用商店排行榜（总榜与分类榜） | 国内服务器 | ⏳ 等待采集 | 3 | 5 | 2026-10-22 |
| `steam_cn` | Steam 中国区畅销榜 | 国内服务器 | ⏳ 等待采集 | 3 | 5 | 2026-10-22 |
| `apple_podcasts_cn` | Apple 播客中国区排行榜 | GitHub | ✅ | 10 | 10 | 2026-10-21 |
| `huggingface_models` | Hugging Face 热度（模型/数据集/应用） | GitHub | ✅ | 10 | 10 | 2026-10-21 |
| `llm_api_prices` | 大模型 API 价格（OpenRouter） | GitHub | ✅ | 10 | 10 | 2026-10-21 |
| `cn_city_weather_forecast` | 全国城市 7 天天气预报存档（中央气象台） | 国内服务器 | ⏳ 等待采集 | 3 | 5 | 2026-10-22 |
| `cn_surface_water_quality` | 全国地表水水质自动监测实时数据 | 国内服务器·每小时 | ✅（今天 1 次有新数据，累计 977 行） | 4 | 6 | 2026-10-22 |
| `cn_weather_hourly_obs` | 全国城市逐小时天气实况（中央气象台） | 国内服务器 | ⏳ 等待采集 | 3 | 5 | 2026-10-22 |
| `hk_weather_forecast` | 香港天文台九天预报 | GitHub | ✅ | 10 | 10 | 2026-10-21 |
| `hk_carpark_vacancy` | 香港停车场实时空位 | GitHub | ✅ | 10 | 10 | 2026-10-21 |
| `bj_housing_daily` | 北京新房与二手房每日网签及库存 | 国内服务器 | ⏳ 等待采集 | 3 | 5 | 2026-10-22 |
| `gz_housing_daily` | 广州新建商品房每日签约与库存（分区） | 国内服务器 | ⏳ 等待采集 | 3 | 5 | 2026-10-22 |

## 怎么自查

- 这一页随每次数据入库自动更新；每晚 22:47 和 23:17 还会做一次严格检查，发现问题会自动补跑，并给仓库主人发邮件。
- 本地检查：`python scripts/health.py`；验证整条哈希链：`python scripts/verify.py`。
- 历史上的缺失和修正记录见 [CHANGELOG.md](CHANGELOG.md)。
