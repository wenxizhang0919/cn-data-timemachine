"""全球 App Store 排行榜（约 35 个国家/地区 × 免费榜/畅销榜 × 总榜/游戏，各前 100 名）。

来源：Apple 官方公开 RSS 接口，只提供当天榜单。海外榜单的历史排名
目前只能从付费平台购买。可用于研究中国应用/游戏出海的排名变化。
"""

from sources import _apple

NAME = "appstore_global"
TITLE = "全球 App Store 排行榜"
SOURCE_URL = 'https://itunes.apple.com/{country}/rss/'
LICENSE = '🟢 Apple 官方公开 RSS 接口。仅存档排名、价格等事实数据；App 名称、商标归各自权利人。'
FIELDS = {
    'country': '国家/地区代码（Apple 商店区）',
    'country_name': '国家/地区中文名',
    'chart': '榜单（免费榜/畅销榜/游戏免费榜/游戏畅销榜）',
    'rank': '名次（1 起）',
    'app_id': 'App Store 应用 ID',
    'bundle_id': '应用包名',
    'name': '应用名称',
    'artist': '开发者',
    'category': '应用主分类',
    'price': '价格',
    'currency': '币种',
}

COUNTRIES = {
    "us": "美国", "ca": "加拿大", "mx": "墨西哥", "br": "巴西", "ar": "阿根廷",
    "cl": "智利", "co": "哥伦比亚",
    "gb": "英国", "de": "德国", "fr": "法国", "it": "意大利", "es": "西班牙",
    "nl": "荷兰", "se": "瑞典", "pl": "波兰", "tr": "土耳其", "ru": "俄罗斯",
    "jp": "日本", "kr": "韩国", "hk": "中国香港", "mo": "中国澳门", "tw": "中国台湾",
    "sg": "新加坡", "my": "马来西亚", "th": "泰国", "vn": "越南", "id": "印度尼西亚",
    "ph": "菲律宾", "in": "印度", "pk": "巴基斯坦",
    "sa": "沙特阿拉伯", "ae": "阿联酋", "eg": "埃及", "za": "南非", "ng": "尼日利亚",
    "au": "澳大利亚", "nz": "新西兰",
}
FEEDS = [
    ("topfreeapplications", "", "免费榜"),
    ("topgrossingapplications", "", "畅销榜"),
    ("topfreeapplications", "6014", "游戏免费榜"),
    ("topgrossingapplications", "6014", "游戏畅销榜"),
]
PAUSE_SECONDS = 0.4


def collect(session, run) -> list[dict]:
    rows, failed = [], []
    for cc, cname in COUNTRIES.items():
        try:
            results = _apple.fetch_feeds(
                session, [(c, g) for c, g, _ in FEEDS], country=cc, pause=PAUSE_SECONDS
            )
        except Exception as e:  # noqa: BLE001  某个国家整体失败不影响其他国家
            failed.append(f"{cc}: {e!r}")
            continue
        names = {(c, g): n for c, g, n in FEEDS}
        for chart, genre, _title, items in results:
            for it in items:
                rows.append(
                    {
                        "country": cc,
                        "country_name": cname,
                        "chart": names[(chart, genre)],
                        "rank": it["rank"],
                        "app_id": it["id"],
                        "bundle_id": it["bundle_id"],
                        "name": it["name"],
                        "artist": it["artist"],
                        "category": it["category"],
                        "price": it["price"],
                        "currency": it["currency"],
                    }
                )
    for msg in failed:
        print(f"  [warn] {msg}")
    if not rows:
        raise RuntimeError("; ".join(failed[:5]) or "no rows")
    return rows
