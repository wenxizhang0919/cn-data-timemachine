<!-- 本文件由 make_catalog.py 自动生成，请勿手改 -->
# Apple 播客中国区排行榜

- 数据集 ID：`apple_podcasts_cn`（固定不变）
- 分类：内容与媒体（`media`）
- 状态：采集中
- 来源：<https://itunes.apple.com/cn/rss/toppodcasts/>
- 许可：🟢 Apple 官方公开 RSS 接口。仅存档排名等事实数据；节目名称归各自权利人。
- 覆盖：2026-10-21 至 2026-10-27，已存档 7 天，缺失 0 天
- 文件：`data/raw/media/apple_podcasts_cn/<YYYY-MM>/<YYYY-MM-DD>.csv`，每天一个 CSV（UTF-8，Excel 可直接打开）
- 频率：每天采集一次（当天首次成功的那次）
- 采集机器：GitHub Actions（海外）

## 说明

Apple 播客中国区排行榜（总榜 + 各分类，各前 100 名）。

来源：Apple 官方公开 RSS 接口，只提供当前榜单，不提供历史。
可用于研究中文播客的热度变化、新节目崛起、分类竞争格局等。

## 字段

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

## 读取

```python
import pandas as pd, glob
df = pd.concat(pd.read_csv(f) for f in sorted(glob.glob("data/raw/media/apple_podcasts_cn/*/*.csv")))
```

## 引用

> 数据来自「每日数据时光机」存档（cn-data-timemachine），数据集 `apple_podcasts_cn`，版本 snapshot-YYYY-MM-DD，https://github.com/wenxizhang0919/cn-data-timemachine

每天文件的 SHA-256 和内容 ID 见 `ledger/<日期>.json`，可用 `python scripts/verify.py` 独立验证。
