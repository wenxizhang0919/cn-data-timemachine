# 每日数据时光机 · cn-data-timemachine

很多公开数据源只提供**"现在这一刻"**的数据，不保留历史。等到写论文、打比赛需要面板数据时，才发现历史根本拿不到，只能花钱找人买。

这个仓库做一件简单的事：**每天自动给这些数据源拍一张快照，长期攒下来，免费开放。**

代码谁都能写，但历史数据补不回来——越早开始攒，数据越值钱。

## 已收录的数据

| 数据集 | 内容 | 频率 | 开始日期 | 来源 |
|---|---|---|---|---|
| `appstore_cn` | App Store 中国区：iPhone 免费/付费/畅销榜（总榜 + 全部 25 个分类）、iPad 三榜（总榜 + 游戏）、Mac 免费榜、新上架榜，各前 100 名 | 每日 | 2026-10-21 | 🟢 Apple 官方公开 RSS |
| `apple_podcasts_cn` | Apple 播客中国区排行榜（总榜 + 18 个分类，各前 100 名） | 每日 | 2026-10-21 | 🟢 Apple 官方公开 RSS |

更多数据源正在陆续加入，见 [Issues](../../issues)。

## 数据在哪

```
data/<数据集>/<年-月>/<日期>.csv     每天一个 CSV（UTF-8，Excel 可直接打开）
data/_status/<日期>.json            每天的采集日志
```

每行都带 `date`（北京时间日期）和 `fetched_at_utc`（实际采集时间）。

合并成面板数据（Python）：

```python
import pandas as pd, glob
df = pd.concat(pd.read_csv(f) for f in sorted(glob.glob("data/appstore_cn/*/*.csv")))
panel = df[df.chart == "topgrossingapplications"].pivot_table(
    index="date", columns="name", values="rank")
```

## 收录原则

每个数据源都会标注授权状态，只公开发布允许再利用的数据：

- 🟢 **可发布**：官方开放接口，或明确允许再利用的公共数据开放平台
- 🟡 **注明来源发布**：网站未作声明；权利人提出要求即删除
- 🔴 **不收录**：网站明确禁止下载使用，或 robots.txt 不允许抓取

采集遵守 robots.txt，每个数据源每天只请求一次，不给对方服务器增加负担。

如果你是某个数据的权利人，希望下架，请开 Issue，会尽快处理。

## 怎么运行

数据由 GitHub Actions 每天北京时间 10:17 左右自动采集，提交回本仓库。本地运行：

```bash
pip install -r requirements.txt
python collect.py              # 采集全部数据源
python collect.py appstore_cn  # 只采集一个
```

## 贡献新数据源

在 `sources/` 下新建一个模块，提供 `NAME`、`TITLE` 和 `collect(session, run)`，返回一个由 dict 组成的列表即可。参考 [`sources/appstore_cn.py`](sources/appstore_cn.py)。

欢迎在 Issue 里推荐"只有实时、没有历史"的数据源。
