import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from types import SimpleNamespace  # noqa: E402

from sources import (  # noqa: E402
    appstore_global,
    llm_api_prices,
    steam_cn,
    hk_carpark_vacancy,
    hk_weather_forecast,
    huggingface_models,
)

RUN = SimpleNamespace(date="2026-10-21", fetched_at_utc="2026-10-21T02:17:00Z")


class Resp:
    def __init__(self, d):
        self.d = d

    def raise_for_status(self):
        pass

    def json(self):
        return self.d


class Router:
    """按 URL/参数返回不同的假数据。"""

    headers = {}

    def __init__(self, fn):
        self.fn = fn
        self.calls = []

    def get(self, url, timeout=None, params=None, **kw):
        self.calls.append((url, params))
        r = self.fn(url, params or {})
        if isinstance(r, Exception):
            raise r
        return Resp(r)


APPLE_FEED = {
    "feed": {
        "title": {"label": "iTunes Store: Top Free"},
        "entry": [
            {
                "im:name": {"label": "TikTok"},
                "id": {"attributes": {"im:id": "835599320", "im:bundleId": "com.zhiliaoapp.musically"}},
                "im:artist": {"label": "TikTok Ltd."},
                "category": {"attributes": {"label": "Entertainment"}},
            }
        ],
    }
}


def test_appstore_global(monkeypatch):
    import collect

    monkeypatch.setattr(appstore_global, "PAUSE_SECONDS", 0)
    monkeypatch.setattr(collect.time, "sleep", lambda s: None)

    def fn(url, params):
        if "/jp/" in url:
            return ConnectionError("jp down")
        return APPLE_FEED

    s = Router(fn)
    rows = appstore_global.collect(s, RUN)
    n_ok = len(appstore_global.COUNTRIES) - 1
    assert len(rows) == n_ok * len(appstore_global.FEEDS)
    assert {r["country"] for r in rows} == set(appstore_global.COUNTRIES) - {"jp"}
    assert rows[0]["name"] == "TikTok" and rows[0]["chart"] == "免费榜"
    assert set(rows[0]) == set(appstore_global.FIELDS)
    assert any(r["chart"] == "游戏畅销榜" for r in rows)


def test_huggingface(monkeypatch):
    monkeypatch.setattr(huggingface_models, "PAUSE_SECONDS", 0)
    model = {
        "id": "deepseek-ai/DeepSeek-V4.1-Flash-1017",
        "likes": 1771,
        "downloads": 17924,
        "trendingScore": 1600,
        "pipeline_tag": "image-text-to-text",
        "createdAt": "2026-10-17T02:40:38.000Z",
    }
    s = Router(lambda url, p: [model, model])
    rows = huggingface_models.collect(s, RUN)
    n_jobs = len(huggingface_models.jobs())
    assert len(s.calls) == n_jobs
    assert len(rows) == 2 * n_jobs
    r = rows[0]
    assert r["kind"] == "model" and r["author"] == "deepseek-ai"
    assert r["downloads_30d"] == 17924 and r["created_at"] == "2026-10-17" and r["rank"] == 1
    assert any(p.get("author") == "Qwen" for _, p in s.calls)
    assert {r["kind"] for r in rows} == {"model", "dataset", "space"}
    assert set(rows[0]) == set(huggingface_models.FIELDS)
    assert any(u.endswith("/api/spaces") for u, _ in s.calls)


def test_hk_weather():
    data = {
        "generalSituation": "東北季候風",
        "updateTime": "2026-10-21T11:30:00+08:00",
        "weatherForecast": [
            {
                "forecastDate": "20261022",
                "week": "星期四",
                "forecastWind": "東風",
                "forecastWeather": "大致天晴",
                "forecastMaxtemp": {"value": 29, "unit": "C"},
                "forecastMintemp": {"value": 24, "unit": "C"},
                "forecastMaxrh": {"value": 85, "unit": "percent"},
                "forecastMinrh": {"value": 60, "unit": "percent"},
                "ForecastIcon": 51,
                "PSR": "低",
            }
        ],
    }
    rows = hk_weather_forecast.collect(Router(lambda u, p: data), RUN)
    assert set(rows[0]) == set(hk_weather_forecast.FIELDS)
    assert rows == [
        {
            "issued_at": "2026-10-21T11:30:00+08:00",
            "lead_day": 1,
            "forecast_date": "20261022",
            "week": "星期四",
            "max_temp_c": 29,
            "min_temp_c": 24,
            "max_rh_pct": 85,
            "min_rh_pct": 60,
            "weather": "大致天晴",
            "wind": "東風",
            "icon": 51,
            "psr": "低",
            "general_situation": "東北季候風",
        }
    ]


def test_hk_carpark():
    vac = {
        "results": [
            {
                "park_Id": "10",
                "privateCar": [{"vacancy_type": "A", "vacancy": 37, "lastupdate": "2026-10-21 21:58:00"}],
                "LGV": [{"vacancy_type": "A", "vacancy": 2, "lastupdate": "2026-10-21 21:58:00"}],
            },
            {"park_Id": "tdc2p8"},
        ]
    }
    info = {"results": [{"park_Id": "10", "name": "大會堂停車場", "district": "中西區"}]}
    s = Router(lambda u, p: info if p.get("data") == "info" else vac)
    rows = hk_carpark_vacancy.collect(s, RUN)
    assert len(rows) == 2
    assert rows[0]["name"] == "大會堂停車場" and rows[0]["vacancy"] == 37
    assert set(rows[0]) == set(hk_carpark_vacancy.FIELDS)
    assert {r["vehicle_type"] for r in rows} == {"privateCar", "LGV"}

    # 名称接口失败也照常返回空位
    def fn(u, p):
        return ConnectionError("x") if p.get("data") == "info" else vac

    import collect

    orig = collect.time.sleep
    collect.time.sleep = lambda s: None
    try:
        rows = hk_carpark_vacancy.collect(Router(fn), RUN)
    finally:
        collect.time.sleep = orig
    assert len(rows) == 2 and rows[0]["name"] == ""


# 取自 2026-10-21 Steam 中国区畅销榜真实返回（节选两条）
STEAM_HTML = """
<a href="https://store.steampowered.com/app/4435490/x/?snr=1"
\t\t\t data-ds-appid="4435490" data-ds-itemkey="App_4435490" data-ds-tagids="[1774,19,1663]" class="search_result_row ds_collapse_flag ">
  <div class="search_name ellipsis"><span class="title">使命召唤®：现代战争® 4</span></div>
  <div class="search_released responsive_secondrow">
      2026 年 10 月 22 日                </div>
  <span class="search_review_summary positive" data-tooltip-html="特别好评&lt;br&gt;此游戏的 742 篇用户评测中有 82% 为好评。&lt;br&gt;&lt;br&gt;说明"></span>
  <div class="search_price_discount_combined responsive_secondrow" data-price-final="29800">
    <div class="prepurchase_tag">预购</div><div class="discount_block search_discount_block no_discount" data-price-final="29800" data-bundlediscount="0" data-discount="0"></div>
  </div>
</a>
<a href="https://store.steampowered.com/app/578080/PUBG/?snr=1"
\t\t\t data-ds-appid="578080" data-ds-itemkey="App_578080" data-ds-tagids="[1662,1774]" class="search_result_row ds_collapse_flag ">
  <span class="title">PUBG: BATTLEGROUNDS</span>
  <div class="search_released responsive_secondrow">2017 年 12 月 21 日</div>
  <span class="search_review_summary mixed" data-tooltip-html="褒贬不一&lt;br&gt;此游戏的 1,401,763 篇用户评测中有 50% 为好评。"></span>
  <div class="search_price_discount_combined responsive_secondrow" data-price-final="0"></div>
</a>
"""


def test_steam_parse():
    items = steam_cn.parse(STEAM_HTML)
    assert [i["appid"] for i in items] == ["4435490", "578080"]
    a, b = items
    assert a["title"] == "使命召唤®：现代战争® 4"
    assert a["released"] == "2026 年 10 月 22 日"
    assert a["review_summary"] == "特别好评" and a["review_count"] == "742" and a["review_positive_pct"] == "82"
    assert a["price_cny"] == 298.0 and a["prepurchase"] is True and a["discount_pct"] == "0"
    assert b["review_count"] == "1401763" and b["price_cny"] == 0 and b["prepurchase"] is False


def test_steam_collect_dedup_and_rank(monkeypatch):
    monkeypatch.setattr(steam_cn, "PAUSE_SECONDS", 0)
    s = Router(lambda u, p: {"success": 1, "results_html": STEAM_HTML})
    rows = steam_cn.collect(s, RUN)
    # 每个榜单翻两页，但同样的 2 个游戏去重后只保留 2 条
    assert len(rows) == 2 * len(steam_cn.LISTS)
    assert [r["rank"] for r in rows[:2]] == [1, 2]
    assert set(rows[0]) == set(steam_cn.FIELDS)
    assert all(p["cc"] == "cn" for _, p in s.calls)


def test_steam_empty_html_raises(monkeypatch):
    import pytest

    monkeypatch.setattr(steam_cn, "PAUSE_SECONDS", 0)
    with pytest.raises(RuntimeError):
        steam_cn.collect(Router(lambda u, p: {"results_html": "<div>改版了</div>"}), RUN)


def test_llm_prices():
    data = {
        "data": [
            {
                "id": "deepseek/deepseek-v4.1-flash-1017",
                "name": "DeepSeek: DeepSeek V4.1 Flash 1017",
                "created": 1792225624,
                "context_length": 1048576,
                "pricing": {"prompt": "0.0000003", "completion": "0.0000012", "input_cache_read": "0.000000006",
                            "overrides": [{"utc_days": [0]}]},
            },
            {"id": "minimax/minimax-m3.1-flash:free", "pricing": {"prompt": "0", "completion": "0"}},
        ]
    }
    rows = llm_api_prices.collect(Router(lambda u, p: data), RUN)
    a, b = rows
    assert set(a) == set(llm_api_prices.FIELDS)
    assert a["vendor"] == "deepseek" and a["prompt_usd_per_m"] == 0.3 and a["completion_usd_per_m"] == 1.2
    assert a["cache_read_usd_per_m"] == 0.006 and a["has_time_based_pricing"] is True
    assert a["created"].startswith("2026-")
    assert b["is_free_variant"] is True and b["prompt_usd_per_m"] == 0.0 and b["created"] == ""
