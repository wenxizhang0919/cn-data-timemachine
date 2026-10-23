<!-- 本文件由 make_catalog.py 自动生成，请勿手改 -->
# 全国城市 7 天天气预报存档（中央气象台）

- 数据集 ID：`cn_city_weather_forecast`（固定不变）
- 分类：天气与环境（`weather`）
- 状态：采集中
- 来源：<https://www.nmc.cn/publish/forecast.html>
- 许可：🟡 中央气象台官网公开显示的预报数据，官网未声明开放许可；本存档仅作非商业研究用途的历史保存，使用时请注明来源：中央气象台。
- 覆盖：2026-10-22 至 2026-10-23，已存档 2 天，缺失 0 天
- 文件：`data/raw/weather/cn_city_weather_forecast/<YYYY-MM>/<YYYY-MM-DD>.csv`，每天一个 CSV（UTF-8，Excel 可直接打开）
- 频率：每天采集一次（当天首次成功的那次）
- 采集机器：国内云服务器（阿里云 杭州）

## 说明

全国约 2500 个城市的 7 天天气预报（每天存一次当天发布的版本），附空气质量与预警。

来源：中央气象台官网（nmc.cn）各城市天气页。官网只显示最新一次发布的预报，旧预报被覆盖后不再可查。
每天存下当天的预报，就能研究"预报准不准、提前几天准、哪里最不准"，
并与 cn_weather_hourly_obs（实况）对照。

说明：
- 每个城市每天 7 行（预报日期 = 今天起 7 天）。publish_time 是官网标注的预报发布时间。
- aqi / aqi_text / aqi_time 是官网同时显示的城市空气质量（AQI）及其时间，每个城市当天各行相同。
- warning_* 是采集时该城市生效的气象预警（如有），每个城市当天各行相同；没有预警时为空。
- 官网用 9999 表示缺测/无，本存档存为空值。

## 字段

| 字段 | 说明 |
|---|---|
| `city_code` | 官网城市代码 |
| `province` | 省份 |
| `city` | 城市 |
| `publish_time` | 预报发布时间（北京时间） |
| `forecast_date` | 预报日期 |
| `lead_days` | 提前天数（0 = 当天） |
| `day_weather` | 白天天气现象 |
| `day_temp_c` | 白天气温（最高，℃） |
| `day_wind_direction` | 白天风向 |
| `day_wind_power` | 白天风力 |
| `night_weather` | 夜间天气现象 |
| `night_temp_c` | 夜间气温（最低，℃） |
| `night_wind_direction` | 夜间风向 |
| `night_wind_power` | 夜间风力 |
| `precipitation_mm` | 预报降水量（mm） |
| `aqi` | 城市空气质量指数 AQI |
| `aqi_text` | 空气质量等级 |
| `aqi_time` | AQI 对应时间 |
| `warning_signal` | 生效中的气象预警类型（如暴雨、大风） |
| `warning_level` | 预警等级（蓝/黄/橙/红） |
| `warning_issue_time` | 预警发布时间 |
| `warning_content` | 预警内容 |
| `date` | 采集日期（北京时间），即数据版本日期 |
| `fetched_at_utc` | 实际采集时刻（UTC） |

## 读取

```python
import pandas as pd, glob
df = pd.concat(pd.read_csv(f) for f in sorted(glob.glob("data/raw/weather/cn_city_weather_forecast/*/*.csv")))
```

## 引用

> 数据来自「每日数据时光机」存档（cn-data-timemachine），数据集 `cn_city_weather_forecast`，版本 snapshot-YYYY-MM-DD，https://github.com/wenxizhang0919/cn-data-timemachine

每天文件的 SHA-256 和内容 ID 见 `ledger/<日期>.json`，可用 `python scripts/verify.py` 独立验证。
