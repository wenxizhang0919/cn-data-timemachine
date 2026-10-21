"""Apple 播客中国区排行榜（总榜 + 各分类，各前 100 名）。

来源：Apple 官方公开 RSS 接口，只提供当前榜单，不提供历史。
可用于研究中文播客的热度变化、新节目崛起、分类竞争格局等。
"""

from sources import _apple

NAME = "apple_podcasts_cn"
TITLE = "Apple 播客中国区排行榜"

# 顶层分类编号；名称以接口返回的榜单标题为准（chart_title 列），避免手写对照表出错
GENRE_IDS = [
    "",  # 总榜
    "1301", "1303", "1304", "1305", "1309", "1310", "1314", "1318", "1321",
    "1324", "1483", "1487", "1488", "1489", "1502", "1512", "1533", "1545",
]
PAUSE_SECONDS = 0.5


def collect(session, run) -> list[dict]:
    feeds = [("toppodcasts", g) for g in GENRE_IDS]
    rows = []
    for _chart, genre, title, items in _apple.fetch_feeds(
        session, feeds, pause=PAUSE_SECONDS
    ):
        for it in items:
            rows.append(
                {
                    "genre_id": genre or "all",
                    "chart_title": title,
                    "rank": it["rank"],
                    "podcast_id": it["id"],
                    "name": it["name"],
                    "artist": it["artist"],
                    "category_id": it["category_id"],
                    "category": it["category"],
                    "release_date": it["release_date"],
                }
            )
    return rows
