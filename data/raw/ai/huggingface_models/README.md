<!-- 本文件由 make_catalog.py 自动生成，请勿手改 -->
# Hugging Face 热度（模型/数据集/应用）

- 数据集 ID：`huggingface_models`（固定不变）
- 分类：人工智能（`ai`）
- 状态：采集中
- 来源：<https://huggingface.co/api/>
- 许可：🟢 Hugging Face 公开 API。仅存档公开仓库的统计数字（下载量、点赞数、热度）。
- 覆盖：2026-10-21 至 2026-10-28，已存档 8 天，缺失 0 天
- 文件：`data/raw/ai/huggingface_models/<YYYY-MM>/<YYYY-MM-DD>.csv`，每天一个 CSV（UTF-8，Excel 可直接打开）
- 频率：每天采集一次（当天首次成功的那次）
- 采集机器：GitHub Actions（海外）

## 说明

Hugging Face 热度快照（模型 / 数据集 / 应用）。

- 模型：全站热门榜、下载榜、点赞榜各前 100；中国主要 AI 机构的模型（按下载量各前 50）
- 数据集、Spaces 应用：热门榜各前 100

来源：Hugging Face 公开 API。downloads 是"近 30 天下载量"，trendingScore
是当前热度，接口都不提供历史值；每天存一次即可得到日度变化。

## 字段

| 字段 | 说明 |
|---|---|
| `kind` | 类型：model / dataset / space |
| `list` | 榜单：trending、top_downloads、top_likes 或 org:<机构> |
| `rank` | 名次（1 起） |
| `repo_id` | 仓库 ID（机构/名称） |
| `author` | 发布机构或账号 |
| `downloads_30d` | 近 30 天下载量（接口口径） |
| `likes` | 点赞数 |
| `trending_score` | 当前热度分 |
| `pipeline_tag` | 任务类型 |
| `library_or_sdk` | 框架（模型）或 SDK（Spaces） |
| `created_at` | 仓库创建日期 |
| `date` | 采集日期（北京时间），即数据版本日期 |
| `fetched_at_utc` | 实际采集时刻（UTC） |

## 读取

```python
import pandas as pd, glob
df = pd.concat(pd.read_csv(f) for f in sorted(glob.glob("data/raw/ai/huggingface_models/*/*.csv")))
```

## 引用

> 数据来自「每日数据时光机」存档（cn-data-timemachine），数据集 `huggingface_models`，版本 snapshot-YYYY-MM-DD，https://github.com/wenxizhang0919/cn-data-timemachine

每天文件的 SHA-256 和内容 ID 见 `ledger/<日期>.json`，可用 `python scripts/verify.py` 独立验证。
