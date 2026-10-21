"""App Store 中国区排行榜。

- iPhone：免费榜 / 付费榜 / 畅销榜 × 总榜 + 全部 25 个分类
- iPad：免费榜 / 付费榜 / 畅销榜 × 总榜 + 游戏
- Mac：免费榜（中国区 Mac 付费榜、畅销榜为空）
- 新上架：新 App / 新免费 / 新付费

来源：Apple 官方公开 RSS 接口，只提供当前榜单，不提供历史。每个榜单最多 100 条。
每天存一次，就得到每个 App 的日度排名面板数据。
"""

from sources import _apple

NAME = "appstore_cn"
TITLE = "App Store 中国区排行榜"
SOURCE_URL = 'https://itunes.apple.com/cn/rss/'
LICENSE = '🟢 Apple 官方公开 RSS 接口。仅存档排名、价格等事实数据；App 名称、商标归各自权利人。'
FIELDS = {
    'chart': '榜单接口名',
    'chart_name': '榜单中文名（iPhone 免费榜等）',
    'genre_id': '分类 ID，all 为总榜',
    'genre_name': '分类中文名',
    'rank': '名次（1 起）',
    'app_id': 'App Store 应用 ID',
    'bundle_id': '应用包名',
    'name': '应用名称',
    'artist': '开发者',
    'category_id': '应用主分类 ID',
    'category': '应用主分类',
    'price': '价格',
    'currency': '币种',
    'release_date': '首次上架日期',
}

CHARTS = {
    "topfreeapplications": "iPhone 免费榜",
    "toppaidapplications": "iPhone 付费榜",
    "topgrossingapplications": "iPhone 畅销榜",
    "topfreeipadapplications": "iPad 免费榜",
    "toppaidipadapplications": "iPad 付费榜",
    "topgrossingipadapplications": "iPad 畅销榜",
    "topfreemacapps": "Mac 免费榜",
    "newapplications": "新上架",
    "newfreeapplications": "新上架免费",
    "newpaidapplications": "新上架付费",
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
IPHONE_CHARTS = ["topfreeapplications", "toppaidapplications", "topgrossingapplications"]
IPAD_CHARTS = ["topfreeipadapplications", "toppaidipadapplications", "topgrossingipadapplications"]
OTHER_CHARTS = ["topfreemacapps", "newapplications", "newfreeapplications", "newpaidapplications"]

PAUSE_SECONDS = 0.5  # 请求之间稍作停顿，对接口友好


def feeds():
    out = [(c, g) for c in IPHONE_CHARTS for g in GENRES]
    out += [(c, g) for c in IPAD_CHARTS for g in ("", "6014")]
    out += [(c, "") for c in OTHER_CHARTS]
    return out


def to_rows(chart, genre, items):
    return [
        {
            "chart": chart,
            "chart_name": CHARTS.get(chart, chart),
            "genre_id": genre or "all",
            "genre_name": GENRES.get(genre, genre),
            "rank": it["rank"],
            "app_id": it["id"],
            "bundle_id": it["bundle_id"],
            "name": it["name"],
            "artist": it["artist"],
            "category_id": it["category_id"],
            "category": it["category"],
            "price": it["price"],
            "currency": it["currency"],
            "release_date": it["release_date"],
        }
        for it in items
    ]


def parse(feed_json, chart, genre):
    """兼容旧测试：解析单个榜单为输出行。"""
    _, items = _apple.parse(feed_json)
    return to_rows(chart, genre, items)


def collect(session, run) -> list[dict]:
    rows = []
    for chart, genre, _title, items in _apple.fetch_feeds(
        session, feeds(), pause=PAUSE_SECONDS
    ):
        rows.extend(to_rows(chart, genre, items))
    return rows
