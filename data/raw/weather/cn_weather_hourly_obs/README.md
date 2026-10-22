<!-- 本文件由 make_catalog.py 自动生成，请勿手改 -->
# 全国城市逐小时天气实况（中央气象台）

- 数据集 ID：`cn_weather_hourly_obs`（固定不变）
- 分类：天气与环境（`weather`）
- 状态：采集中
- 来源：<https://www.nmc.cn/publish/forecast.html>
- 许可：🟡 中央气象台官网公开显示的实况数据，官网未声明开放许可；本存档仅作非商业研究用途的历史保存，使用时请注明来源：中央气象台。
- 覆盖：2026-10-22 至 2026-10-22，已存档 1 天，缺失 0 天
- 文件：`data/raw/weather/cn_weather_hourly_obs/<YYYY-MM>/<YYYY-MM-DD>.csv`，每天一个 CSV（UTF-8，Excel 可直接打开）
- 频率：每天采集一次（当天首次成功的那次）
- 采集机器：国内云服务器（阿里云 杭州）

## 说明

全国约 2500 个城市的逐小时天气实况（每天存一次过去 24 小时）。

来源：中央气象台官网（nmc.cn）各城市天气页。官网每个城市只显示"过去 24 小时"的逐小时实况，
更早的不再显示；成体系的历史逐小时站点数据需向气象部门申请或付费获取。
本数据集每天抓一次全部城市，把过去 24 小时的逐小时记录存下来，攒成"全国城市 × 小时"的面板。

说明：
- 每天由国内服务器在第一个成功的时点（通常 10:47）采集，文件里是采集时刻往前 24 小时的记录
  （例如 10:47 采集得到前一天 11:00 至当天 10:00）。相邻两天的文件可能有少量重叠小时
  （某天在较晚的时点才采集成功时），按 (city_code, obs_time) 去重即可。
- 官网用 9999 表示缺测，本存档存为空值。
- city_code 是官网的城市代码；官网若更换代码体系，可用 province + city 对齐。

## 字段

| 字段 | 说明 |
|---|---|
| `city_code` | 官网城市代码 |
| `province` | 省份 |
| `city` | 城市 |
| `obs_time` | 观测时刻（北京时间，YYYY-MM-DD HH:MM） |
| `temperature_c` | 气温（℃） |
| `rain_1h_mm` | 过去 1 小时降水量（mm） |
| `humidity_pct` | 相对湿度（%） |
| `pressure_hpa` | 气压（hPa） |
| `wind_direction_deg` | 风向（度，0 为北风，顺时针） |
| `wind_speed_ms` | 风速（m/s） |
| `date` | 采集日期（北京时间），即数据版本日期 |
| `fetched_at_utc` | 实际采集时刻（UTC） |

## 读取

```python
import pandas as pd, glob
df = pd.concat(pd.read_csv(f) for f in sorted(glob.glob("data/raw/weather/cn_weather_hourly_obs/*/*.csv")))
```

## 引用

> 数据来自「每日数据时光机」存档（cn-data-timemachine），数据集 `cn_weather_hourly_obs`，版本 snapshot-YYYY-MM-DD，https://github.com/wenxizhang0919/cn-data-timemachine

每天文件的 SHA-256 和内容 ID 见 `ledger/<日期>.json`，可用 `python scripts/verify.py` 独立验证。
