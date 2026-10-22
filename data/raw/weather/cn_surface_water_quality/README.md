<!-- 本文件由 make_catalog.py 自动生成，请勿手改 -->
# 全国地表水水质自动监测实时数据

- 数据集 ID：`cn_surface_water_quality`（固定不变）
- 分类：天气与环境（`weather`）
- 状态：暂停（见 CHANGELOG）
- 来源：<https://szzdjc.cnemc.cn:8070/GJZ/Business/Publish/Main.html>
- 许可：🟡 中国环境监测总站公开发布的实时数据，官网未声明开放许可；本存档仅作非商业研究用途的历史保存，使用时请注明来源：中国环境监测总站。官网注明数据未经审核，仅供参考。
- 覆盖：— 至 —，已存档 0 天，缺失 0 天
- 文件：`data/raw/weather/cn_surface_water_quality/<YYYY-MM>/<YYYY-MM-DD>.csv`，每天一个 CSV（UTF-8，Excel 可直接打开）
- 频率：一天内多次采集，新出现的记录追加进当天文件（同一记录只存一次，以首次采到的为准）
- 采集机器：国内云服务器（阿里云 杭州）

## 说明

全国地表水水质自动监测站实时数据（一天内多次采集，逐个监测时刻存档）。

来源：中国环境监测总站「国家地表水水质自动监测实时数据发布系统」。
官网只滚动显示每个断面"最新一次"的监测值（约每 4 小时一次），不提供历史查询或下载。
本数据集由国内云服务器一天多次抓取，把每个断面每个监测时刻的数值都存下来，
攒成全国断面 × 4 小时的面板数据。

说明：
- 官网注明"数据未经审核，仅供参考"，本存档如实保存原始发布值，不做任何修正。
- 每天一个文件，包含当天各次采集中出现的所有（断面, 监测时刻）记录；
  同一断面同一监测时刻只记一次（以第一次采到的为准）。
- 断面停运、维护时官网显示的空值或"--"原样保存，不做插补。

## 字段

| 字段 | 说明 |
|---|---|
| `province` | 省份 |
| `basin` | 流域 |
| `station` | 断面名称 |
| `monitor_time` | 监测时刻（北京时间，YYYY-MM-DD HH:MM；官网只显示月-日，年份按采集日期推断） |
| `monitor_time_raw` | 官网显示的监测时间原文 |
| `water_class_code` | 水质类别代码（1–6） |
| `water_class` | 水质类别（Ⅰ、Ⅱ、Ⅲ、Ⅳ、Ⅴ、劣Ⅴ） |
| `water_temp_c` | 水温（℃） |
| `ph` | pH（无量纲） |
| `dissolved_oxygen_mg_l` | 溶解氧（mg/L） |
| `conductivity_us_cm` | 电导率（μS/cm） |
| `turbidity_ntu` | 浊度（NTU） |
| `permanganate_index_mg_l` | 高锰酸盐指数（mg/L） |
| `ammonia_nitrogen_mg_l` | 氨氮（mg/L） |
| `total_phosphorus_mg_l` | 总磷（mg/L） |
| `total_nitrogen_mg_l` | 总氮（mg/L） |
| `chlorophyll_a_mg_l` | 叶绿素α（mg/L） |
| `algae_density_cells_l` | 藻密度（cells/L） |
| `station_status` | 站点情况（如维护、停运等说明） |
| `date` | 采集日期（北京时间），即数据版本日期 |
| `fetched_at_utc` | 实际采集时刻（UTC） |

## 读取

```python
import pandas as pd, glob
df = pd.concat(pd.read_csv(f) for f in sorted(glob.glob("data/raw/weather/cn_surface_water_quality/*/*.csv")))
```

## 引用

> 数据来自「每日数据时光机」存档（cn-data-timemachine），数据集 `cn_surface_water_quality`，版本 snapshot-YYYY-MM-DD，https://github.com/wenxizhang0919/cn-data-timemachine

每天文件的 SHA-256 和内容 ID 见 `ledger/<日期>.json`，可用 `python scripts/verify.py` 独立验证。
