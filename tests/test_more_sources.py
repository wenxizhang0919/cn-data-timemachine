import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from types import SimpleNamespace  # noqa: E402

from sources import (  # noqa: E402
    appstore_global,
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
    n_jobs = len(huggingface_models.GLOBAL_LISTS) + len(huggingface_models.CN_ORGS)
    assert len(s.calls) == n_jobs
    assert len(rows) == 2 * n_jobs
    r = rows[0]
    assert r["author"] == "deepseek-ai" and r["downloads_30d"] == 17924
    assert r["created_at"] == "2026-10-17" and r["rank"] == 1
    assert any(p.get("author") == "Qwen" for _, p in s.calls)


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
