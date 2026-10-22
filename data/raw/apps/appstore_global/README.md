<!-- 本文件由 make_catalog.py 自动生成，请勿手改 -->
# 全球 App Store 排行榜

- 数据集 ID：`appstore_global`（固定不变）
- 分类：应用与游戏（`apps`）
- 状态：采集中
- 来源：`https://itunes.apple.com/{country}/rss/`
- 许可：🟢 Apple 官方公开 RSS 接口。仅存档排名、价格等事实数据；App 名称、商标归各自权利人。
- 覆盖：2026-10-21 至 2026-10-23，已存档 3 天，缺失 0 天
- 文件：`data/raw/apps/appstore_global/<YYYY-MM>/<YYYY-MM-DD>.csv`，每天一个 CSV（UTF-8，Excel 可直接打开）
- 频率：每天采集一次（当天首次成功的那次）
- 采集机器：GitHub Actions（海外）

## 说明

全球 App Store 排行榜（约 35 个国家/地区 × 免费榜/畅销榜 × 总榜/游戏，各前 100 名）。

来源：Apple 官方公开 RSS 接口，只提供当天榜单。海外榜单的历史排名
目前只能从付费平台购买。可用于研究中国应用/游戏出海的排名变化。

## 字段

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

## 读取

```python
import pandas as pd, glob
df = pd.concat(pd.read_csv(f) for f in sorted(glob.glob("data/raw/apps/appstore_global/*/*.csv")))
```

## 引用

> 数据来自「每日数据时光机」存档（cn-data-timemachine），数据集 `appstore_global`，版本 snapshot-YYYY-MM-DD，https://github.com/wenxizhang0919/cn-data-timemachine

每天文件的 SHA-256 和内容 ID 见 `ledger/<日期>.json`，可用 `python scripts/verify.py` 独立验证。
