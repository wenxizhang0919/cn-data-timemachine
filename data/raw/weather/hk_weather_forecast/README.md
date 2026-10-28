<!-- 本文件由 make_catalog.py 自动生成，请勿手改 -->
# 香港天文台九天预报

- 数据集 ID：`hk_weather_forecast`（固定不变）
- 分类：天气与环境（`weather`）
- 状态：采集中
- 来源：<https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=fnd>
- 许可：🟢 香港天文台开放数据（DATA.GOV.HK 使用条款），来源：香港天文台。
- 覆盖：2026-10-21 至 2026-10-29，已存档 9 天，缺失 0 天
- 文件：`data/raw/weather/hk_weather_forecast/<YYYY-MM>/<YYYY-MM-DD>.csv`，每天一个 CSV（UTF-8，Excel 可直接打开）
- 频率：每天采集一次（当天首次成功的那次）
- 采集机器：GitHub Actions（海外）

## 说明

香港天文台九天天气预报。

来源：香港天文台开放数据 API（DATA.GOV.HK）。接口只提供"最新一版"预报，
过去发布过的预报不存档。每天存一次，就能研究预报准确率、预报修正等。

## 字段

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

## 读取

```python
import pandas as pd, glob
df = pd.concat(pd.read_csv(f) for f in sorted(glob.glob("data/raw/weather/hk_weather_forecast/*/*.csv")))
```

## 引用

> 数据来自「每日数据时光机」存档（cn-data-timemachine），数据集 `hk_weather_forecast`，版本 snapshot-YYYY-MM-DD，https://github.com/wenxizhang0919/cn-data-timemachine

每天文件的 SHA-256 和内容 ID 见 `ledger/<日期>.json`，可用 `python scripts/verify.py` 独立验证。
