"""App Store 中国区排行榜（免费榜 / 付费榜 / 畅销榜，总榜 + 游戏榜）。

来源：Apple 官方公开 RSS 接口，只提供当前榜单，不提供历史。
每天存一次，就得到每个 App 的日度排名面板数据。
"""

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
    "6014": "游戏",
}
LIMIT = 200


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
    for chart in CHARTS:
        for genre in GENRES:
            url = BASE.format(
                chart=chart, limit=LIMIT, genre=f"/genre={genre}" if genre else ""
            )
            rows.extend(parse(get_json(session, url), chart, genre))
    return rows
