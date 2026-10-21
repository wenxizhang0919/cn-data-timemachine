# 数据集目录

> 本文件由 `make_catalog.py` 自动生成，请勿手改。机器可读版本见 [`datasets.json`](datasets.json)。

| ID | 名称 | 首个快照 | 最新快照 | 已存档天数 | 缺失天数 |
|---|---|---|---|---|---|
| [`apple_podcasts_cn`](#apple_podcasts_cn) | Apple 播客中国区排行榜 | 2026-10-21 | 2026-10-21 | 1 | 0 |
| [`appstore_cn`](#appstore_cn) | App Store 中国区排行榜 | 2026-10-21 | 2026-10-21 | 1 | 0 |
| [`appstore_global`](#appstore_global) | 全球 App Store 排行榜 | 2026-10-21 | 2026-10-21 | 1 | 0 |
| [`hk_carpark_vacancy`](#hk_carpark_vacancy) | 香港停车场实时空位 | 2026-10-21 | 2026-10-21 | 1 | 0 |
| [`hk_weather_forecast`](#hk_weather_forecast) | 香港天文台九天预报 | 2026-10-21 | 2026-10-21 | 1 | 0 |
| [`huggingface_models`](#huggingface_models) | Hugging Face 热度（模型/数据集/应用） | 2026-10-21 | 2026-10-21 | 1 | 0 |
| [`llm_api_prices`](#llm_api_prices) | 大模型 API 价格（OpenRouter） | 2026-10-21 | 2026-10-21 | 1 | 0 |
| [`steam_cn`](#steam_cn) | Steam 中国区畅销榜 | — | — | 0 | 0 |

## apple_podcasts_cn

**Apple 播客中国区排行榜**

Apple 播客中国区排行榜（总榜 + 各分类，各前 100 名）。

来源：Apple 官方公开 RSS 接口，只提供当前榜单，不提供历史。
可用于研究中文播客的热度变化、新节目崛起、分类竞争格局等。

- 来源：<https://itunes.apple.com/cn/rss/toppodcasts/>
- 许可：🟢 Apple 官方公开 RSS 接口。仅存档排名等事实数据；节目名称归各自权利人。
- 文件：`data/raw/apple_podcasts_cn/<YYYY-MM>/<YYYY-MM-DD>.csv`

| 字段 | 说明 |
|---|---|
| `genre_id` | 请求的分类 ID，all 为总榜 |
| `chart_title` | 接口返回的榜单标题 |
| `rank` | 名次（1 起） |
| `podcast_id` | Apple 播客 ID |
| `name` | 节目名称 |
| `artist` | 制作方 |
| `category_id` | 节目所属细分类 ID |
| `category` | 节目所属细分类 |
| `release_date` | 最近更新日期 |
| `date` | 采集日期（北京时间），即数据版本日期 |
| `fetched_at_utc` | 实际采集时刻（UTC） |

引用示例：

> 数据来自「每日数据时光机」存档（cn-data-timemachine），数据集 `apple_podcasts_cn`，版本 YYYY-MM-DD，https://github.com/wenxizhang0919/cn-data-timemachine

## appstore_cn

**App Store 中国区排行榜**

App Store 中国区排行榜。

- iPhone：免费榜 / 付费榜 / 畅销榜 × 总榜 + 全部 25 个分类
- iPad：免费榜 / 付费榜 / 畅销榜 × 总榜 + 游戏
- Mac：免费榜（中国区 Mac 付费榜、畅销榜为空）
- 新上架：新 App / 新免费 / 新付费

来源：Apple 官方公开 RSS 接口，只提供当前榜单，不提供历史。每个榜单最多 100 条。
每天存一次，就得到每个 App 的日度排名面板数据。

- 来源：<https://itunes.apple.com/cn/rss/>
- 许可：🟢 Apple 官方公开 RSS 接口。仅存档排名、价格等事实数据；App 名称、商标归各自权利人。
- 文件：`data/raw/appstore_cn/<YYYY-MM>/<YYYY-MM-DD>.csv`

| 字段 | 说明 |
|---|---|
| `chart` | 榜单接口名 |
| `chart_name` | 榜单中文名（iPhone 免费榜等） |
| `genre_id` | 分类 ID，all 为总榜 |
| `genre_name` | 分类中文名 |
| `rank` | 名次（1 起） |
| `app_id` | App Store 应用 ID |
| `bundle_id` | 应用包名 |
| `name` | 应用名称 |
| `artist` | 开发者 |
| `category_id` | 应用主分类 ID |
| `category` | 应用主分类 |
| `price` | 价格 |
| `currency` | 币种 |
| `release_date` | 首次上架日期 |
| `date` | 采集日期（北京时间），即数据版本日期 |
| `fetched_at_utc` | 实际采集时刻（UTC） |

引用示例：

> 数据来自「每日数据时光机」存档（cn-data-timemachine），数据集 `appstore_cn`，版本 YYYY-MM-DD，https://github.com/wenxizhang0919/cn-data-timemachine

## appstore_global

**全球 App Store 排行榜**

全球 App Store 排行榜（约 35 个国家/地区 × 免费榜/畅销榜 × 总榜/游戏，各前 100 名）。

来源：Apple 官方公开 RSS 接口，只提供当天榜单。海外榜单的历史排名
目前只能从付费平台购买。可用于研究中国应用/游戏出海的排名变化。

- 来源：`https://itunes.apple.com/{country}/rss/`
- 许可：🟢 Apple 官方公开 RSS 接口。仅存档排名、价格等事实数据；App 名称、商标归各自权利人。
- 文件：`data/raw/appstore_global/<YYYY-MM>/<YYYY-MM-DD>.csv`

| 字段 | 说明 |
|---|---|
| `country` | 国家/地区代码（Apple 商店区） |
| `country_name` | 国家/地区中文名 |
| `chart` | 榜单（免费榜/畅销榜/游戏免费榜/游戏畅销榜） |
| `rank` | 名次（1 起） |
| `app_id` | App Store 应用 ID |
| `bundle_id` | 应用包名 |
| `name` | 应用名称 |
| `artist` | 开发者 |
| `category` | 应用主分类 |
| `price` | 价格 |
| `currency` | 币种 |
| `date` | 采集日期（北京时间），即数据版本日期 |
| `fetched_at_utc` | 实际采集时刻（UTC） |

引用示例：

> 数据来自「每日数据时光机」存档（cn-data-timemachine），数据集 `appstore_global`，版本 YYYY-MM-DD，https://github.com/wenxizhang0919/cn-data-timemachine

## hk_carpark_vacancy

**香港停车场实时空位**

香港停车场实时空位（每天一个固定时点的快照）。

来源：香港运输署开放数据 API（DATA.GOV.HK），只提供实时空位，不提供历史。
每天同一时刻存一次，可得到各停车场的日度占用面板。

- 来源：<https://api.data.gov.hk/v1/carpark-info-vacancy>
- 许可：🟢 香港运输署开放数据（DATA.GOV.HK 使用条款），来源：运输署。
- 文件：`data/raw/hk_carpark_vacancy/<YYYY-MM>/<YYYY-MM-DD>.csv`

| 字段 | 说明 |
|---|---|
| `park_id` | 停车场 ID |
| `name` | 停车场名称 |
| `district` | 所在区 |
| `vehicle_type` | 车辆类型（privateCar、LGV 等） |
| `vacancy_type` | 空位类型代码 |
| `vacancy` | 空位数 |
| `vacancy_ev` | 电动车空位数 |
| `vacancy_dis` | 残疾人士空位数 |
| `category` | 细分类别 |
| `last_update` | 该停车场数据的更新时间 |
| `date` | 采集日期（北京时间），即数据版本日期 |
| `fetched_at_utc` | 实际采集时刻（UTC） |

引用示例：

> 数据来自「每日数据时光机」存档（cn-data-timemachine），数据集 `hk_carpark_vacancy`，版本 YYYY-MM-DD，https://github.com/wenxizhang0919/cn-data-timemachine

## hk_weather_forecast

**香港天文台九天预报**

香港天文台九天天气预报。

来源：香港天文台开放数据 API（DATA.GOV.HK）。接口只提供"最新一版"预报，
过去发布过的预报不存档。每天存一次，就能研究预报准确率、预报修正等。

- 来源：<https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=fnd>
- 许可：🟢 香港天文台开放数据（DATA.GOV.HK 使用条款），来源：香港天文台。
- 文件：`data/raw/hk_weather_forecast/<YYYY-MM>/<YYYY-MM-DD>.csv`

| 字段 | 说明 |
|---|---|
| `issued_at` | 预报发布时间 |
| `lead_day` | 提前天数（1=明天） |
| `forecast_date` | 被预报的日期 |
| `week` | 星期 |
| `max_temp_c` | 预报最高气温（℃） |
| `min_temp_c` | 预报最低气温（℃） |
| `max_rh_pct` | 预报最高相对湿度（%） |
| `min_rh_pct` | 预报最低相对湿度（%） |
| `weather` | 天气描述 |
| `wind` | 风力风向描述 |
| `icon` | 天气图标代码 |
| `psr` | 显著降雨概率等级 |
| `general_situation` | 天气概况 |
| `date` | 采集日期（北京时间），即数据版本日期 |
| `fetched_at_utc` | 实际采集时刻（UTC） |

引用示例：

> 数据来自「每日数据时光机」存档（cn-data-timemachine），数据集 `hk_weather_forecast`，版本 YYYY-MM-DD，https://github.com/wenxizhang0919/cn-data-timemachine

## huggingface_models

**Hugging Face 热度（模型/数据集/应用）**

Hugging Face 热度快照（模型 / 数据集 / 应用）。

- 模型：全站热门榜、下载榜、点赞榜各前 100；中国主要 AI 机构的模型（按下载量各前 50）
- 数据集、Spaces 应用：热门榜各前 100

来源：Hugging Face 公开 API。downloads 是"近 30 天下载量"，trendingScore
是当前热度，接口都不提供历史值；每天存一次即可得到日度变化。

- 来源：<https://huggingface.co/api/>
- 许可：🟢 Hugging Face 公开 API。仅存档公开仓库的统计数字（下载量、点赞数、热度）。
- 文件：`data/raw/huggingface_models/<YYYY-MM>/<YYYY-MM-DD>.csv`

| 字段 | 说明 |
|---|---|
| `kind` | 类型：model / dataset / space |
| `list` | 榜单：trending、top_downloads、top_likes 或 org:<机构> |
| `rank` | 名次（1 起） |
| `repo_id` | 仓库 ID（机构/名称） |
| `author` | 发布机构或账号 |
| `downloads_30d` | 近 30 天下载量（接口口径） |
| `likes` | 点赞数 |
| `trending_score` | 当前热度分 |
| `pipeline_tag` | 任务类型 |
| `library_or_sdk` | 框架（模型）或 SDK（Spaces） |
| `created_at` | 仓库创建日期 |
| `date` | 采集日期（北京时间），即数据版本日期 |
| `fetched_at_utc` | 实际采集时刻（UTC） |

引用示例：

> 数据来自「每日数据时光机」存档（cn-data-timemachine），数据集 `huggingface_models`，版本 YYYY-MM-DD，https://github.com/wenxizhang0919/cn-data-timemachine

## llm_api_prices

**大模型 API 价格（OpenRouter）**

大模型 API 价格与上架情况（OpenRouter 全部模型）。

来源：OpenRouter 公开模型列表接口，只给当前价格。各家模型调价、限时免费、
下架都很频繁，价格历史没有公开来源。每天存一次即可得到价格变化史。
价格单位统一换算为"美元 / 百万 token"。

- 来源：<https://openrouter.ai/api/v1/models>
- 许可：🟢 OpenRouter 公开 API。仅存档价格、上下文长度等事实数据。
- 文件：`data/raw/llm_api_prices/<YYYY-MM>/<YYYY-MM-DD>.csv`

| 字段 | 说明 |
|---|---|
| `model_id` | 模型 ID（厂商/模型） |
| `vendor` | 厂商 |
| `name` | 模型名称 |
| `created` | 上架日期（UTC） |
| `context_length` | 上下文长度（token） |
| `prompt_usd_per_m` | 输入价格（美元/百万 token） |
| `completion_usd_per_m` | 输出价格（美元/百万 token） |
| `cache_read_usd_per_m` | 缓存读取价格（美元/百万 token） |
| `image_usd` | 图像输入价格（美元/张，原始口径） |
| `request_usd` | 按次计费（美元/次） |
| `is_free_variant` | 是否 :free 免费版本 |
| `has_time_based_pricing` | 是否有分时段价格 |
| `date` | 采集日期（北京时间），即数据版本日期 |
| `fetched_at_utc` | 实际采集时刻（UTC） |

引用示例：

> 数据来自「每日数据时光机」存档（cn-data-timemachine），数据集 `llm_api_prices`，版本 YYYY-MM-DD，https://github.com/wenxizhang0919/cn-data-timemachine

## steam_cn

**Steam 中国区畅销榜**

Steam 中国区畅销榜 / 热门新品榜（各前 100 名，含价格、折扣、评测数与好评率）。

来源：Steam 商店公开搜索结果（中国区定价）。商店只显示当前榜单，
畅销排名、折扣、评测数的历史没有免费公开来源。

- 来源：<https://store.steampowered.com/search/?filter=topsellers&cc=cn>
- 许可：🟡 Steam 商店公开页面（遵守 robots.txt，每日 4 次请求）。仅存档排名、价格、评测数等事实数据；游戏名称归各自权利人。
- 文件：`data/raw/steam_cn/<YYYY-MM>/<YYYY-MM-DD>.csv`

| 字段 | 说明 |
|---|---|
| `list` | 榜单（畅销榜/热门新品） |
| `rank` | 名次（1 起） |
| `appid` | Steam 应用 ID |
| `title` | 游戏名称 |
| `released` | 发售日期（原文） |
| `review_summary` | 评测总结（如特别好评） |
| `review_count` | 评测数（简中口径） |
| `review_positive_pct` | 好评率（%） |
| `price_cny` | 当前人民币价格（元） |
| `discount_pct` | 折扣（%） |
| `prepurchase` | 是否预购 |
| `tag_ids` | Steam 标签 ID 列表 |
| `date` | 采集日期（北京时间），即数据版本日期 |
| `fetched_at_utc` | 实际采集时刻（UTC） |

引用示例：

> 数据来自「每日数据时光机」存档（cn-data-timemachine），数据集 `steam_cn`，版本 YYYY-MM-DD，https://github.com/wenxizhang0919/cn-data-timemachine
