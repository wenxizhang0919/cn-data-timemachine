<!-- 本文件由 make_catalog.py 自动生成，请勿手改 -->
# Steam 中国区畅销榜

- 数据集 ID：`steam_cn`（固定不变）
- 分类：应用与游戏（`apps`）
- 状态：采集中
- 来源：<https://store.steampowered.com/search/?filter=topsellers&cc=cn>
- 许可：🟡 Steam 商店公开页面（遵守 robots.txt，每日 4 次请求）。仅存档排名、价格、评测数等事实数据；游戏名称归各自权利人。
- 覆盖：2026-10-22 至 2026-10-29，已存档 5 天，缺失 3 天
- 文件：`data/raw/apps/steam_cn/<YYYY-MM>/<YYYY-MM-DD>.csv`，每天一个 CSV（UTF-8，Excel 可直接打开）
- 频率：每天采集一次（当天首次成功的那次）
- 采集机器：国内云服务器（阿里云 杭州）

## 说明

Steam 中国区畅销榜 / 热门新品榜（各前 100 名，含价格、折扣、评测数与好评率）。

来源：Steam 商店公开搜索结果（中国区定价）。商店只显示当前榜单，
畅销排名、折扣、评测数的历史没有免费公开来源。

## 字段

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

## 读取

```python
import pandas as pd, glob
df = pd.concat(pd.read_csv(f) for f in sorted(glob.glob("data/raw/apps/steam_cn/*/*.csv")))
```

## 引用

> 数据来自「每日数据时光机」存档（cn-data-timemachine），数据集 `steam_cn`，版本 snapshot-YYYY-MM-DD，https://github.com/wenxizhang0919/cn-data-timemachine

每天文件的 SHA-256 和内容 ID 见 `ledger/<日期>.json`，可用 `python scripts/verify.py` 独立验证。
