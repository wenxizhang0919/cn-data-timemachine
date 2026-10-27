<!-- 本文件由 make_catalog.py 自动生成，请勿手改 -->
# 全国地表水水质自动监测实时数据

- 数据集 ID：`cn_surface_water_quality`（固定不变）
- 分类：天气与环境（`weather`）
- 状态：采集中
- 来源：<https://szzdjc.cnemc.cn:8070/GJZ/Business/Publish/Main.html>
- 许可：🟡 中国环境监测总站公开发布的实时数据，官网未声明开放许可；本存档仅作非商业研究用途的历史保存，使用时请注明来源：中国环境监测总站。官网注明数据未经审核，仅供参考。
- 覆盖：2026-10-22 至 2026-10-27，已存档 3 天，缺失 3 天
- 文件：`data/raw/weather/cn_surface_water_quality/<YYYY-MM>/<YYYY-MM-DD>.csv`，每天一个 CSV（UTF-8，Excel 可直接打开）
- 频率：一天内多次采集，新出现的记录追加进当天文件（同一记录只存一次，以首次采到的为准）
- 采集机器：国内云服务器（阿里云 杭州）

## 说明

全国地表水水质自动监测站实时数据（每小时采集，逐个监测时刻存档）。

来源：中国环境监测总站「国家地表水水质自动监测实时数据发布系统」。
官网只滚动显示全国约 1500 个断面"最新一次"的监测值（多数断面每小时更新），
不提供历史查询或下载。本数据集由国内云服务器每小时抓取一次，
把每个断面每个监测时刻的数值都存下来，攒成全国断面 × 小时的面板数据。

说明：
- 官网注明"数据未经审核，仅供参考"，本存档如实保存发布值，不做任何修正或插补。
- 每个指标存两列：官网显示值（按发布规则修约）和 `_orig` 原始值（官网提示框里的
  "原始值"；与显示值相同时留空）。
- 官网显示"--"时，若提示框给出原因（如"当天质控不合格"），记录在 `notes` 列。
- 文件按采集日期（北京时间）划分；同一断面同一监测时刻只记一次，以第一次采到的为准。
  每天 0:27–22:27 每小时采集，23 点前后的监测值会在次日凌晨的采集中存入次日文件。

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
| `water_temp_c_orig` | 水温（℃）的原始值（未修约；与显示值相同时留空） |
| `ph_orig` | pH（无量纲）的原始值（未修约；与显示值相同时留空） |
| `dissolved_oxygen_mg_l_orig` | 溶解氧（mg/L）的原始值（未修约；与显示值相同时留空） |
| `conductivity_us_cm_orig` | 电导率（μS/cm）的原始值（未修约；与显示值相同时留空） |
| `turbidity_ntu_orig` | 浊度（NTU）的原始值（未修约；与显示值相同时留空） |
| `permanganate_index_mg_l_orig` | 高锰酸盐指数（mg/L）的原始值（未修约；与显示值相同时留空） |
| `ammonia_nitrogen_mg_l_orig` | 氨氮（mg/L）的原始值（未修约；与显示值相同时留空） |
| `total_phosphorus_mg_l_orig` | 总磷（mg/L）的原始值（未修约；与显示值相同时留空） |
| `total_nitrogen_mg_l_orig` | 总氮（mg/L）的原始值（未修约；与显示值相同时留空） |
| `chlorophyll_a_mg_l_orig` | 叶绿素α（mg/L）的原始值（未修约；与显示值相同时留空） |
| `algae_density_cells_l_orig` | 藻密度（cells/L）的原始值（未修约；与显示值相同时留空） |
| `notes` | 官网提示框里的说明（如某指标"当天质控不合格"），多条用分号分隔 |
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
