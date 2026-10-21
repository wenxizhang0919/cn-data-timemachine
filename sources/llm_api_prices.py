"""大模型 API 价格与上架情况（OpenRouter 全部模型）。

来源：OpenRouter 公开模型列表接口，只给当前价格。各家模型调价、限时免费、
下架都很频繁，价格历史没有公开来源。每天存一次即可得到价格变化史。
价格单位统一换算为"美元 / 百万 token"。
"""

from datetime import datetime, timezone

NAME = "llm_api_prices"
CATEGORY = "ai"
TITLE = "大模型 API 价格（OpenRouter）"
SOURCE_URL = 'https://openrouter.ai/api/v1/models'
LICENSE = '🟢 OpenRouter 公开 API。仅存档价格、上下文长度等事实数据。'
FIELDS = {
    'model_id': '模型 ID（厂商/模型）',
    'vendor': '厂商',
    'name': '模型名称',
    'created': '上架日期（UTC）',
    'context_length': '上下文长度（token）',
    'prompt_usd_per_m': '输入价格（美元/百万 token）',
    'completion_usd_per_m': '输出价格（美元/百万 token）',
    'cache_read_usd_per_m': '缓存读取价格（美元/百万 token）',
    'image_usd': '图像输入价格（美元/张，原始口径）',
    'request_usd': '按次计费（美元/次）',
    'is_free_variant': '是否 :free 免费版本',
    'has_time_based_pricing': '是否有分时段价格',
}

URL = "https://openrouter.ai/api/v1/models"


def _per_million(v):
    try:
        return round(float(v) * 1_000_000, 6)
    except (TypeError, ValueError):
        return ""


def collect(session, run) -> list[dict]:
    from collect import get_json

    data = get_json(session, URL).get("data", [])
    rows = []
    for m in data:
        p = m.get("pricing") or {}
        mid = m.get("id", "")
        created = m.get("created")
        rows.append(
            {
                "model_id": mid,
                "vendor": mid.split("/")[0] if "/" in mid else "",
                "name": m.get("name", ""),
                "created": datetime.fromtimestamp(created, timezone.utc).strftime("%Y-%m-%d")
                if isinstance(created, (int, float))
                else "",
                "context_length": m.get("context_length", ""),
                "prompt_usd_per_m": _per_million(p.get("prompt")),
                "completion_usd_per_m": _per_million(p.get("completion")),
                "cache_read_usd_per_m": _per_million(p.get("input_cache_read")),
                "image_usd": p.get("image", ""),
                "request_usd": p.get("request", ""),
                "is_free_variant": mid.endswith(":free"),
                "has_time_based_pricing": bool(p.get("overrides")),
            }
        )
    return rows
