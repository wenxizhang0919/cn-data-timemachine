"""Hugging Face 热度快照（模型 / 数据集 / 应用）。

- 模型：全站热门榜、下载榜、点赞榜各前 100；中国主要 AI 机构的模型（按下载量各前 50）
- 数据集、Spaces 应用：热门榜各前 100

来源：Hugging Face 公开 API。downloads 是"近 30 天下载量"，trendingScore
是当前热度，接口都不提供历史值；每天存一次即可得到日度变化。
"""

import time

NAME = "huggingface_models"
TITLE = "Hugging Face 热度（模型/数据集/应用）"
SOURCE_URL = 'https://huggingface.co/api/'
LICENSE = '🟢 Hugging Face 公开 API。仅存档公开仓库的统计数字（下载量、点赞数、热度）。'
FIELDS = {
    'kind': '类型：model / dataset / space',
    'list': '榜单：trending、top_downloads、top_likes 或 org:<机构>',
    'rank': '名次（1 起）',
    'repo_id': '仓库 ID（机构/名称）',
    'author': '发布机构或账号',
    'downloads_30d': '近 30 天下载量（接口口径）',
    'likes': '点赞数',
    'trending_score': '当前热度分',
    'pipeline_tag': '任务类型',
    'library_or_sdk': '框架（模型）或 SDK（Spaces）',
    'created_at': '仓库创建日期',
}

API = "https://huggingface.co/api/{kind}"

GLOBAL_MODEL_LISTS = {
    "trending": "trendingScore",
    "top_downloads": "downloads",
    "top_likes": "likes",
}
# 中国主要 AI 机构在 Hugging Face 上的账号
CN_ORGS = [
    "deepseek-ai", "Qwen", "zai-org", "THUDM", "moonshotai", "MiniMaxAI",
    "baidu", "tencent", "internlm", "openbmb", "BAAI", "stepfun-ai",
    "XiaomiMiMo", "ByteDance-Seed", "inclusionAI", "meituan-longcat",
    "OpenGVLab", "Kwai-Kolors",
]
PAUSE_SECONDS = 0.5


def jobs():
    out = [("models", name, {"sort": key, "limit": 100}) for name, key in GLOBAL_MODEL_LISTS.items()]
    out += [
        ("models", f"org:{org}", {"author": org, "sort": "downloads", "limit": 50})
        for org in CN_ORGS
    ]
    out += [
        ("datasets", "trending", {"sort": "trendingScore", "limit": 100}),
        ("spaces", "trending", {"sort": "trendingScore", "limit": 100}),
    ]
    return out


def _row(kind, list_name, rank, m):
    rid = m.get("id") or m.get("modelId", "")
    return {
        "kind": kind[:-1],  # model / dataset / space
        "list": list_name,
        "rank": rank,
        "repo_id": rid,
        "author": rid.split("/")[0] if "/" in rid else m.get("author", ""),
        "downloads_30d": m.get("downloads", ""),
        "likes": m.get("likes", ""),
        "trending_score": m.get("trendingScore", ""),
        "pipeline_tag": m.get("pipeline_tag", ""),
        "library_or_sdk": m.get("library_name") or m.get("sdk", ""),
        "created_at": (m.get("createdAt") or "")[:10],
    }


def collect(session, run) -> list[dict]:
    from collect import get_json

    rows, errors = [], []
    for kind, list_name, params in jobs():
        try:
            data = get_json(session, API.format(kind=kind), params=params)
            for i, m in enumerate(data, start=1):
                rows.append(_row(kind, list_name, i, m))
        except Exception as e:  # noqa: BLE001
            errors.append(f"{kind}/{list_name}: {e!r}")
        time.sleep(PAUSE_SECONDS)
    for msg in errors:
        print(f"  [warn] {msg}")
    if not rows:
        raise RuntimeError("; ".join(errors[:5]))
    return rows
