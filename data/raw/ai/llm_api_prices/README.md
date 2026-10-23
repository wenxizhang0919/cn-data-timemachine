<!-- 本文件由 make_catalog.py 自动生成，请勿手改 -->
# 大模型 API 价格（OpenRouter）

- 数据集 ID：`llm_api_prices`（固定不变）
- 分类：人工智能（`ai`）
- 状态：采集中
- 来源：<https://openrouter.ai/api/v1/models>
- 许可：🟢 OpenRouter 公开 API。仅存档价格、上下文长度等事实数据。
- 覆盖：2026-10-21 至 2026-10-24，已存档 4 天，缺失 0 天
- 文件：`data/raw/ai/llm_api_prices/<YYYY-MM>/<YYYY-MM-DD>.csv`，每天一个 CSV（UTF-8，Excel 可直接打开）
- 频率：每天采集一次（当天首次成功的那次）
- 采集机器：GitHub Actions（海外）

## 说明

大模型 API 价格与上架情况（OpenRouter 全部模型）。

来源：OpenRouter 公开模型列表接口，只给当前价格。各家模型调价、限时免费、
下架都很频繁，价格历史没有公开来源。每天存一次即可得到价格变化史。
价格单位统一换算为"美元 / 百万 token"。

## 字段

| 字段 | 说明 |
|---|---|
| `model_id` | 模型 ID（厂商/模型） |
| `vendor` | 厂商 |
| `name` | 模型名称 |
| `created` | 上架日期（UTC） |
| `context_length` | 上下文长度（token） |
| `prompt_usd_per_m` | 输入价格（美元/百万 token） |
| `completion_usd_per_m` | 输出价格（美元/百万 token） |
| `cache_read_usd_per_m` | 缓存读取价格（美元/百万 token） |
| `image_usd` | 图像输入价格（美元/张，原始口径） |
| `request_usd` | 按次计费（美元/次） |
| `is_free_variant` | 是否 :free 免费版本 |
| `has_time_based_pricing` | 是否有分时段价格 |
| `date` | 采集日期（北京时间），即数据版本日期 |
| `fetched_at_utc` | 实际采集时刻（UTC） |

## 读取

```python
import pandas as pd, glob
df = pd.concat(pd.read_csv(f) for f in sorted(glob.glob("data/raw/ai/llm_api_prices/*/*.csv")))
```

## 引用

> 数据来自「每日数据时光机」存档（cn-data-timemachine），数据集 `llm_api_prices`，版本 snapshot-YYYY-MM-DD，https://github.com/wenxizhang0919/cn-data-timemachine

每天文件的 SHA-256 和内容 ID 见 `ledger/<日期>.json`，可用 `python scripts/verify.py` 独立验证。
