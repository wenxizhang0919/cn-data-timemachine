<!-- 本文件由 make_catalog.py 自动生成，请勿手改 -->
# App Store 中国区排行榜

- 数据集 ID：`appstore_cn`（固定不变）
- 分类：应用与游戏（`apps`）
- 状态：采集中
- 来源：<https://itunes.apple.com/cn/rss/>
- 许可：🟢 Apple 官方公开 RSS 接口。仅存档排名、价格等事实数据；App 名称、商标归各自权利人。
- 覆盖：2026-10-21 至 2026-10-23，已存档 3 天，缺失 0 天
- 文件：`data/raw/apps/appstore_cn/<YYYY-MM>/<YYYY-MM-DD>.csv`，每天一个 CSV（UTF-8，Excel 可直接打开）
- 频率：每天采集一次（当天首次成功的那次）
- 采集机器：GitHub Actions（海外）

## 说明

App Store 中国区排行榜。

- iPhone：免费榜 / 付费榜 / 畅销榜 × 总榜 + 全部 25 个分类
- iPad：免费榜 / 付费榜 / 畅销榜 × 总榜 + 游戏
- Mac：免费榜（中国区 Mac 付费榜、畅销榜为空）
- 新上架：新 App / 新免费 / 新付费

来源：Apple 官方公开 RSS 接口，只提供当前榜单，不提供历史。每个榜单最多 100 条。
每天存一次，就得到每个 App 的日度排名面板数据。

## 字段

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

## 读取

```python
import pandas as pd, glob
df = pd.concat(pd.read_csv(f) for f in sorted(glob.glob("data/raw/apps/appstore_cn/*/*.csv")))
```

## 引用

> 数据来自「每日数据时光机」存档（cn-data-timemachine），数据集 `appstore_cn`，版本 snapshot-YYYY-MM-DD，https://github.com/wenxizhang0919/cn-data-timemachine

每天文件的 SHA-256 和内容 ID 见 `ledger/<日期>.json`，可用 `python scripts/verify.py` 独立验证。
