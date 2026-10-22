"""小米应用商店排行榜（总榜 + 各分类榜），每天一次。

来源：小米应用商店网页版「应用排行榜」。国内安卓市场远大于 App Store，但各安卓商店的榜单
只显示当前排名，历史排名主要由七麦、蝉大师等商业公司付费提供。每天存一次，
可与 appstore_cn 对照研究国内 iOS / 安卓两个市场的应用排名变化。

说明：
- chart = "0" 是全部应用总榜，其余为分类榜（chart_name 为分类名）。
- rank 是在该榜单中的名次（按页面顺序，从 1 开始）。榜单翻页直到没有新应用为止（总榜最多 MAX_PAGES 页）。
- package 是安卓包名（跨日、跨商店对齐用的稳定 ID）；app_id 是页面统计代码里的应用编号。
"""

import re
import time

NAME = "mi_appstore_rank"
CATEGORY = "apps"
RUNNER = "server"
ENABLED = False  # 待在服务器上实测解析无误后启用
TITLE = "小米应用商店排行榜（总榜与分类榜）"
SOURCE_URL = "https://app.mi.com/topList"
LICENSE = (
    "🟡 小米应用商店网页公开显示的排行榜，未声明开放许可；"
    "本存档仅作非商业研究用途的历史保存，使用时请注明来源：小米应用商店。"
)
FIELDS = {
    "chart": "榜单 ID（0 = 总榜，其余为分类 ID）",
    "chart_name": "榜单名称",
    "rank": "名次",
    "app_name": "应用名称",
    "package": "安卓包名",
    "app_id": "小米商店页面统计代码里的应用编号（pos_name）",
    "category_id": "应用所属分类 ID",
    "category_name": "应用所属分类",
    "page": "所在页码",
}

BASE = "https://app.mi.com"
MAX_PAGES = 60  # 总榜最多翻页数
MAX_PAGES_CAT = 5  # 每个分类榜最多翻页数
SLEEP = 1.0

_LI = re.compile(r"<li>\s*<a href=\"/details\?id=([^\"]+)\"(.*?)</li>", re.S)
_NAME = re.compile(r"<h5>\s*<a[^>]*>(.*?)</a>", re.S)
_CAT = re.compile(r"<a href=\"/category/(\d+)\">(.*?)</a>", re.S)
_ID = re.compile(r"dtlClick\(\{[^}]*?(\d{3,})")


def parse_page(html: str) -> list[dict]:
    m = re.search(r'<ul class="applist">(.*?)</ul>', html, re.S)
    if not m:
        return []
    items = []
    for pkg, body in _LI.findall(m.group(1)):
        name = _NAME.search(body)
        cat = _CAT.search(body)
        app_id = _ID.search(body)
        items.append(
            {
                "app_name": re.sub(r"<[^>]+>", "", name.group(1)).strip() if name else "",
                "package": pkg.strip(),
                "app_id": app_id.group(1) if app_id else "",
                "category_id": cat.group(1) if cat else "",
                "category_name": cat.group(2).strip() if cat else "",
            }
        )
    return items


def categories(html: str) -> dict:
    """页面上出现的分类链接 -> {分类ID: 分类名}"""
    return {cid: name.strip() for cid, name in _CAT.findall(html) if name.strip()}


def fetch(session, path: str) -> str:
    last = None
    for i in range(3):
        try:
            r = session.get(BASE + path, timeout=30)
            r.raise_for_status()
            r.encoding = "utf-8"
            return r.text
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(5 * (i + 1))
    raise last  # type: ignore[misc]


def chart(session, chart_id: str, chart_name: str, max_pages: int, first_html: str | None = None) -> list[dict]:
    rows, seen = [], set()
    for page in range(1, max_pages + 1):
        html = first_html if (page == 1 and first_html) else fetch(session, f"/catTopList/{chart_id}?page={page}")
        items = [it for it in parse_page(html) if it["package"] not in seen]
        if not items:
            break
        for it in items:
            seen.add(it["package"])
            rows.append({"chart": chart_id, "chart_name": chart_name, "rank": len(rows) + 1, **it, "page": page})
        time.sleep(SLEEP)
    return rows


def collect(session, run) -> list[dict]:
    first = fetch(session, "/catTopList/0?page=1")
    rows = chart(session, "0", "总榜", MAX_PAGES, first_html=first)
    if len(rows) < 20:
        raise RuntimeError(f"总榜只解析到 {len(rows)} 个应用，页面可能改版")
    cats = categories(first)
    for r in rows:  # 补全分类名单
        if r["category_id"] and r["category_name"]:
            cats.setdefault(r["category_id"], r["category_name"])
    for cid, cname in sorted(cats.items(), key=lambda kv: int(kv[0])):
        try:
            rows += chart(session, cid, cname, MAX_PAGES_CAT)
        except Exception:  # noqa: BLE001  个别分类失败不影响总榜
            continue
    return rows
