"""Apple 旧版 RSS 接口 (itunes.apple.com/{country}/rss/...) 的公共解析。

接口只提供当前榜单，不提供历史；每个榜单最多返回约 100 条。
"""

import time

BASE = "https://itunes.apple.com/{country}/rss/{chart}/limit={limit}{genre}/json"


def label(d, *path, default=""):
    for p in path:
        if not isinstance(d, dict):
            return default
        d = d.get(p)
    return d if d is not None else default


def parse(feed_json: dict) -> tuple[str, list[dict]]:
    """返回 (榜单标题, 条目列表)。每个条目已拍平成常用字段。"""
    feed = feed_json.get("feed", {}) if isinstance(feed_json, dict) else {}
    title = label(feed, "title", "label")
    entries = feed.get("entry", [])
    if isinstance(entries, dict):  # 只有一条时 Apple 返回对象而不是数组
        entries = [entries]
    items = []
    for rank, e in enumerate(entries, start=1):
        items.append(
            {
                "rank": rank,
                "id": label(e, "id", "attributes", "im:id"),
                "bundle_id": label(e, "id", "attributes", "im:bundleId"),
                "name": label(e, "im:name", "label"),
                "artist": label(e, "im:artist", "label"),
                "category_id": label(e, "category", "attributes", "im:id"),
                "category": label(e, "category", "attributes", "label"),
                "price": label(e, "im:price", "attributes", "amount"),
                "currency": label(e, "im:price", "attributes", "currency"),
                "release_date": label(e, "im:releaseDate", "label")[:10],
            }
        )
    return title, items


def fetch_feeds(session, feeds, country="cn", limit=100, pause=0.5):
    """feeds: [(chart, genre_id 或 ""), ...]。

    逐个请求；单个榜单失败只记警告，全部失败才抛错。
    返回 [(chart, genre_id, 榜单标题, items), ...]。
    """
    from collect import get_json

    results, errors = [], []
    for chart, genre in feeds:
        url = BASE.format(
            country=country,
            chart=chart,
            limit=limit,
            genre=f"/genre={genre}" if genre else "",
        )
        try:
            title, items = parse(get_json(session, url))
            results.append((chart, genre, title, items))
        except Exception as e:  # noqa: BLE001
            errors.append(f"{chart}/{genre or 'all'}: {e!r}")
        if pause:
            time.sleep(pause)
    if errors and not results:
        raise RuntimeError("; ".join(errors[:5]))
    for msg in errors:
        print(f"  [warn] {msg}")
    return results
