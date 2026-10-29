<!-- 本文件由 make_catalog.py 自动生成，请勿手改 -->
# 小米应用商店排行榜（总榜与分类榜）

- 数据集 ID：`mi_appstore_rank`（固定不变）
- 分类：应用与游戏（`apps`）
- 状态：采集中
- 来源：<https://app.mi.com/topList>
- 许可：🟡 小米应用商店网页公开显示的排行榜，未声明开放许可；本存档仅作非商业研究用途的历史保存，使用时请注明来源：小米应用商店。
- 覆盖：2026-10-22 至 2026-10-29，已存档 5 天，缺失 3 天
- 文件：`data/raw/apps/mi_appstore_rank/<YYYY-MM>/<YYYY-MM-DD>.csv`，每天一个 CSV（UTF-8，Excel 可直接打开）
- 频率：每天采集一次（当天首次成功的那次）
- 采集机器：国内云服务器（阿里云 杭州）

## 说明

小米应用商店排行榜（总榜 + 各分类榜），每天一次。

来源：小米应用商店网页版「应用排行榜」。国内安卓市场远大于 App Store，但各安卓商店的榜单
只显示当前排名，历史排名主要由七麦、蝉大师等商业公司付费提供。每天存一次，
可与 appstore_cn 对照研究国内 iOS / 安卓两个市场的应用排名变化。

说明：
- chart = "0" 是全部应用总榜，其余为分类榜（chart_name 为分类名）。
- rank 是在该榜单中的名次（按页面顺序，从 1 开始）。榜单翻页直到没有新应用为止；实测网页版每个榜单约显示前 108 名。
- package 是安卓包名（跨日、跨商店对齐用的稳定 ID）；app_id 是页面统计代码里的应用编号。

## 字段

| 字段 | 说明 |
|---|---|
| `chart` | 榜单 ID（0 = 总榜，其余为分类 ID） |
| `chart_name` | 榜单名称 |
| `rank` | 名次 |
| `app_name` | 应用名称 |
| `package` | 安卓包名 |
| `app_id` | 小米商店页面统计代码里的应用编号（pos_name） |
| `category_id` | 应用所属分类 ID |
| `category_name` | 应用所属分类 |
| `page` | 所在页码 |
| `date` | 采集日期（北京时间），即数据版本日期 |
| `fetched_at_utc` | 实际采集时刻（UTC） |

## 读取

```python
import pandas as pd, glob
df = pd.concat(pd.read_csv(f) for f in sorted(glob.glob("data/raw/apps/mi_appstore_rank/*/*.csv")))
```

## 引用

> 数据来自「每日数据时光机」存档（cn-data-timemachine），数据集 `mi_appstore_rank`，版本 snapshot-YYYY-MM-DD，https://github.com/wenxizhang0919/cn-data-timemachine

每天文件的 SHA-256 和内容 ID 见 `ledger/<日期>.json`，可用 `python scripts/verify.py` 独立验证。
