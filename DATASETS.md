<!-- 本文件由 make_catalog.py 自动生成，请勿手改 -->
# 数据集目录

按分类分组。每个数据集在 `data/raw/<分类>/<数据集ID>/` 下有独立文件夹和说明页。机器可读版本见 [`datasets.json`](datasets.json)。

## 应用与游戏（`apps`）

应用商店、游戏平台的排行榜、价格与评测

| ID | 名称 | 首个快照 | 最新快照 | 已存档天数 | 缺失天数 | 状态 |
|---|---|---|---|---|---|---|
| [`appstore_cn`](data/raw/apps/appstore_cn/) | App Store 中国区排行榜 | 2026-10-21 | 2026-10-22 | 2 | 0 | 采集中 |
| [`appstore_global`](data/raw/apps/appstore_global/) | 全球 App Store 排行榜 | 2026-10-21 | 2026-10-22 | 2 | 0 | 采集中 |
| [`mi_appstore_rank`](data/raw/apps/mi_appstore_rank/) | 小米应用商店排行榜（总榜与分类榜） | 2026-10-22 | 2026-10-22 | 1 | 0 | 采集中 |
| [`steam_cn`](data/raw/apps/steam_cn/) | Steam 中国区畅销榜 | 2026-10-22 | 2026-10-22 | 1 | 0 | 采集中 |

## 内容与媒体（`media`）

播客、视频、音乐、图书等内容平台的榜单

| ID | 名称 | 首个快照 | 最新快照 | 已存档天数 | 缺失天数 | 状态 |
|---|---|---|---|---|---|---|
| [`apple_podcasts_cn`](data/raw/media/apple_podcasts_cn/) | Apple 播客中国区排行榜 | 2026-10-21 | 2026-10-22 | 2 | 0 | 采集中 |

## 人工智能（`ai`）

模型热度、下载量、API 价格等 AI 生态数据

| ID | 名称 | 首个快照 | 最新快照 | 已存档天数 | 缺失天数 | 状态 |
|---|---|---|---|---|---|---|
| [`huggingface_models`](data/raw/ai/huggingface_models/) | Hugging Face 热度（模型/数据集/应用） | 2026-10-21 | 2026-10-22 | 2 | 0 | 采集中 |
| [`llm_api_prices`](data/raw/ai/llm_api_prices/) | 大模型 API 价格（OpenRouter） | 2026-10-21 | 2026-10-22 | 2 | 0 | 采集中 |

## 天气与环境（`weather`）

天气预报、空气、水文等环境数据

| ID | 名称 | 首个快照 | 最新快照 | 已存档天数 | 缺失天数 | 状态 |
|---|---|---|---|---|---|---|
| [`cn_city_weather_forecast`](data/raw/weather/cn_city_weather_forecast/) | 全国城市 7 天天气预报存档（中央气象台） | 2026-10-22 | 2026-10-22 | 1 | 0 | 采集中 |
| [`cn_surface_water_quality`](data/raw/weather/cn_surface_water_quality/) | 全国地表水水质自动监测实时数据 | 2026-10-22 | 2026-10-22 | 1 | 0 | 采集中 |
| [`cn_weather_hourly_obs`](data/raw/weather/cn_weather_hourly_obs/) | 全国城市逐小时天气实况（中央气象台） | 2026-10-22 | 2026-10-22 | 1 | 0 | 采集中 |
| [`hk_weather_forecast`](data/raw/weather/hk_weather_forecast/) | 香港天文台九天预报 | 2026-10-21 | 2026-10-22 | 2 | 0 | 采集中 |

## 交通出行（`transport`）

停车、道路、公共交通等实时数据

| ID | 名称 | 首个快照 | 最新快照 | 已存档天数 | 缺失天数 | 状态 |
|---|---|---|---|---|---|---|
| [`hk_carpark_vacancy`](data/raw/transport/hk_carpark_vacancy/) | 香港停车场实时空位 | 2026-10-21 | 2026-10-22 | 2 | 0 | 采集中 |

## 房地产（`real_estate`）

各城市每日网签、成交等数据

| ID | 名称 | 首个快照 | 最新快照 | 已存档天数 | 缺失天数 | 状态 |
|---|---|---|---|---|---|---|
| [`bj_housing_daily`](data/raw/real_estate/bj_housing_daily/) | 北京新房与二手房每日网签及库存 | 2026-10-22 | 2026-10-22 | 1 | 0 | 采集中 |
| [`gz_housing_daily`](data/raw/real_estate/gz_housing_daily/) | 广州新建商品房每日签约与库存（分区） | 2026-10-22 | 2026-10-22 | 1 | 0 | 采集中 |
