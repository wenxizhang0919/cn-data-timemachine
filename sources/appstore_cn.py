"""App Store 中国区排行榜（免费榜 / 付费榜 / 畅销榜 × 总榜 + 全部分类，各前 100 名）。

来源：Apple 官方公开 RSS 接口，只提供当前榜单，不提供历史。
每天存一次，就得到每个 App 的日度排名面板数据。
注：该接口每个榜单最多返回 100 条。
"""

import time

NAME = "appstore_cn"
TITLE = "App Store 中国区排行榜"

BASE = "https://itunes.apple.com/cn/rss/{chart}/limit={limit}{genre}/json"

CHARTS = {
    "topfreeapplications": "免费榜",
    "toppaidapplications": "付费榜",
    "topgrossingapplications": "畅销榜",
}
GENRES = {
    "": "总榜",
    "6000": "商务",
    "6001": "天气",
    "6002": "工具",
    "6003": "旅游",
    "6004": "体育",
    "6005": "社交",
    "6006": "参考",
    "6007": "效率",
    "6008": "摄影与录像",
    "6009": "新闻",
    "6010": "导航",
    "6011": "音乐",
    "6012": "生活",
    "6013": "健康健美",
    "6014": "游戏",
    "6015": "财务",
    "6016": "娱乐",
    "6017": "教育",
    "6018": "图书",
    "6020": "医疗",
    "6021": "报刊杂志",
    "6023": "美食佳饮",
    "6024": "购物",
    "6026": "开发者工具",
    "6027": "图形和设计",
}
LIMIT = 100
PAUSE_SECONDS = 0.5  # 请求之间稍作停顿，对接口友好


def _label(d, *path, default=""):
    for p in path:
        if not isinstance(d, dict):
            return default
        d = d.get(p)
    return d if d is not None else default


def parse(feed_json: dict, chart: str, genre: str) -> list[dict]:
    entries = _label(feed_json, "feed", "entry", default=[])
    if isinstance(entries, dict):  # 只有一条时 Apple 返回对象而不是数组
        entries = [entries]
    rows = []
    for rank, e in enumerate(entries, start=1):
        rows.append(
            {
                "chart": chart,
                "chart_name": CHARTS.get(chart, chart),
                "genre_id": genre or "all",
                "genre_name": GENRES.get(genre, genre),
                "rank": rank,
                "app_id": _label(e, "id", "attributes", "im:id"),
                "bundle_id": _label(e, "id", "attributes", "im:bundleId"),
                "name": _label(e, "im:name", "label"),
                "artist": _label(e, "im:artist", "label"),
                "category_id": _label(e, "category", "attributes", "im:id"),
                "category": _label(e, "category", "attributes", "label"),
                "price": _label(e, "im:price", "attributes", "amount"),
                "currency": _label(e, "im:price", "attributes", "currency"),
                "release_date": _label(e, "im:releaseDate", "label")[:10],
            }
        )
    return rows


def collect(session, run) -> list[dict]:
    from collect import get_json

    rows = []
    errors = []
    for chart in CHARTS:
        for genre in GENRES:
            url = BASE.format(
                chart=chart, limit=LIMIT, genre=f"/genre={genre}" if genre else ""
            )
            try:
                rows.extend(parse(get_json(session, url), chart, genre))
            except Exception as e:  # noqa: BLE001  单个榜单失败不影响其他榜单
                errors.append(f"{chart}/{genre or 'all'}: {e!r}")
            time.sleep(PAUSE_SECONDS)
    if errors and not rows:
        raise RuntimeError("; ".join(errors[:5]))
    for msg in errors:
        print(f"  [warn] {msg}")
    return rows
