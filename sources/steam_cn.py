"""Steam 中国区畅销榜 / 热门新品榜（各前 100 名，含价格、折扣、评测数与好评率）。

来源：Steam 商店公开搜索结果（中国区定价）。商店只显示当前榜单，
畅销排名、折扣、评测数的历史没有免费公开来源。
"""

import html
import re
import time

NAME = "steam_cn"
TITLE = "Steam 中国区畅销榜"

URL = "https://store.steampowered.com/search/results/"
LISTS = {
    "topsellers": "畅销榜",
    "popularnew": "热门新品",
}
TOP_N = 100
PAGE = 50
PAUSE_SECONDS = 1.0

_ROW = re.compile(r'<a\s+href="[^"]*"\s+data-ds-appid="([^"]+)"(.*?)</a>', re.S)
_TITLE = re.compile(r'<span class="title">(.*?)</span>', re.S)
_RELEASED = re.compile(r'<div class="search_released[^"]*">\s*(.*?)\s*</div>', re.S)
_REVIEW = re.compile(
    r'class="search_review_summary[^"]*"\s+data-tooltip-html="([^"]*)"', re.S
)
_REVIEW_NUM = re.compile(r"([\d,]+)\s*篇用户评测中有\s*(\d+)%")
_PRICE_FINAL = re.compile(r'data-price-final="(\d+)"')
_DISCOUNT = re.compile(r'data-discount="(\d+)"')
_TAGIDS = re.compile(r'data-ds-tagids="\[([^\]]*)\]"')


def parse(results_html: str) -> list[dict]:
    items = []
    for appid, body in _ROW.findall(results_html):
        title = _TITLE.search(body)
        released = _RELEASED.search(body)
        review = _REVIEW.search(body)
        review_text = html.unescape(review.group(1)) if review else ""
        summary = review_text.split("<br>")[0] if review_text else ""
        nums = _REVIEW_NUM.search(review_text)
        price = _PRICE_FINAL.search(body)
        disc = _DISCOUNT.search(body)
        tags = _TAGIDS.search(body)
        items.append(
            {
                "appid": appid.split(",")[0],
                "title": html.unescape(title.group(1).strip()) if title else "",
                "released": released.group(1).strip() if released else "",
                "review_summary": summary,
                "review_count": nums.group(1).replace(",", "") if nums else "",
                "review_positive_pct": nums.group(2) if nums else "",
                "price_cny": int(price.group(1)) / 100 if price else "",
                "discount_pct": disc.group(1) if disc else "0",
                "prepurchase": "prepurchase_tag" in body,
                "tag_ids": tags.group(1) if tags else "",
            }
        )
    return items


def collect(session, run) -> list[dict]:
    from collect import get_json

    rows, errors = [], []
    for key, label in LISTS.items():
        seen, rank = set(), 0
        try:
            for start in range(0, TOP_N, PAGE):
                data = get_json(
                    session,
                    URL,
                    params={
                        "filter": key, "cc": "cn", "l": "schinese",
                        "start": start, "count": PAGE, "infinite": 1,
                    },
                )
                for it in parse(data.get("results_html", "")):
                    if it["appid"] in seen or rank >= TOP_N:
                        continue
                    seen.add(it["appid"])
                    rank += 1
                    rows.append({"list": label, "rank": rank, **it})
                time.sleep(PAUSE_SECONDS)
        except Exception as e:  # noqa: BLE001
            errors.append(f"{key}: {e!r}")
    for msg in errors:
        print(f"  [warn] {msg}")
    if not rows:
        raise RuntimeError("; ".join(errors[:3]) or "解析结果为空，页面结构可能变了")
    return rows
