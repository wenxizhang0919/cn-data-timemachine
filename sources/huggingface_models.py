"""Hugging Face 模型热度快照。

- 全站热门榜（trending）、下载榜、点赞榜，各前 100
- 中国主要 AI 机构的模型（按下载量，各前 50）

来源：Hugging Face 公开 API。downloads 字段是"近 30 天下载量"，
接口不提供历史值；每天存一次，就能得到模型热度的日度变化。
"""

import time

NAME = "huggingface_models"
TITLE = "Hugging Face 模型热度"

API = "https://huggingface.co/api/models"

GLOBAL_LISTS = {
    "trending": "trendingScore",
    "top_downloads": "downloads",
    "top_likes": "likes",
}
# 中国主要 AI 机构在 Hugging Face 上的账号
CN_ORGS = [
    "deepseek-ai", "Qwen", "zai-org", "THUDM", "moonshotai", "MiniMaxAI",
    "baidu", "tencent", "internlm", "openbmb", "BAAI", "stepfun-ai",
    "XiaomiMiMo", "ByteDance-Seed", "inclusionAI", "meituan-longcat",
    "OpenGVLab", "Kwai-Kolors", "unsloth",  # unsloth 主要发布热门开源模型的量化版，作参照
]
PAUSE_SECONDS = 0.5


def _row(list_name, rank, m):
    return {
        "list": list_name,
        "rank": rank,
        "model_id": m.get("id") or m.get("modelId", ""),
        "author": (m.get("id") or "").split("/")[0],
        "downloads_30d": m.get("downloads", ""),
        "likes": m.get("likes", ""),
        "trending_score": m.get("trendingScore", ""),
        "pipeline_tag": m.get("pipeline_tag", ""),
        "library_name": m.get("library_name", ""),
        "created_at": (m.get("createdAt") or "")[:10],
    }


def collect(session, run) -> list[dict]:
    from collect import get_json

    jobs = [(name, {"sort": key, "limit": 100}) for name, key in GLOBAL_LISTS.items()]
    jobs += [
        (f"org:{org}", {"author": org, "sort": "downloads", "limit": 50})
        for org in CN_ORGS
    ]
    rows, errors = [], []
    for list_name, params in jobs:
        try:
            data = get_json(session, API, params=params)
            for i, m in enumerate(data, start=1):
                rows.append(_row(list_name, i, m))
        except Exception as e:  # noqa: BLE001
            errors.append(f"{list_name}: {e!r}")
        time.sleep(PAUSE_SECONDS)
    for msg in errors:
        print(f"  [warn] {msg}")
    if not rows:
        raise RuntimeError("; ".join(errors[:5]))
    return rows
