<!-- 本文件由 make_catalog.py 自动生成，请勿手改 -->
# 香港停车场实时空位

- 数据集 ID：`hk_carpark_vacancy`（固定不变）
- 分类：交通出行（`transport`）
- 状态：采集中
- 来源：<https://api.data.gov.hk/v1/carpark-info-vacancy>
- 许可：🟢 香港运输署开放数据（DATA.GOV.HK 使用条款），来源：运输署。
- 覆盖：2026-10-21 至 2026-10-24，已存档 4 天，缺失 0 天
- 文件：`data/raw/transport/hk_carpark_vacancy/<YYYY-MM>/<YYYY-MM-DD>.csv`，每天一个 CSV（UTF-8，Excel 可直接打开）
- 频率：每天采集一次（当天首次成功的那次）
- 采集机器：GitHub Actions（海外）

## 说明

香港停车场实时空位（每天一个固定时点的快照）。

来源：香港运输署开放数据 API（DATA.GOV.HK），只提供实时空位，不提供历史。
每天同一时刻存一次，可得到各停车场的日度占用面板。

## 字段

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

## 读取

```python
import pandas as pd, glob
df = pd.concat(pd.read_csv(f) for f in sorted(glob.glob("data/raw/transport/hk_carpark_vacancy/*/*.csv")))
```

## 引用

> 数据来自「每日数据时光机」存档（cn-data-timemachine），数据集 `hk_carpark_vacancy`，版本 snapshot-YYYY-MM-DD，https://github.com/wenxizhang0919/cn-data-timemachine

每天文件的 SHA-256 和内容 ID 见 `ledger/<日期>.json`，可用 `python scripts/verify.py` 独立验证。
