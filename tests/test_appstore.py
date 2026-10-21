import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import collect  # noqa: E402
from sources import appstore_cn  # noqa: E402

# 结构取自 2026-10-21 实际返回的 itunes.apple.com/cn/rss/topgrossingapplications/json
SAMPLE = {
    "feed": {
        "entry": [
            {
                "im:name": {"label": "抖音"},
                "im:price": {"label": "获取", "attributes": {"amount": "0.00", "currency": "CNY"}},
                "id": {
                    "label": "https://apps.apple.com/cn/app/id1142110895",
                    "attributes": {"im:id": "1142110895", "im:bundleId": "com.ss.iphone.ugc.Aweme"},
                },
                "im:artist": {"label": "Beijing Douyin Technology Co., Ltd."},
                "category": {"attributes": {"im:id": "6016", "term": "Entertainment", "label": "娱乐"}},
                "im:releaseDate": {"label": "2016-09-25T20:28:56-07:00"},
            },
            {
                "im:name": {"label": "王者荣耀"},
                "id": {"attributes": {"im:id": "989673964", "im:bundleId": "com.tencent.smoba"}},
                "category": {"attributes": {"im:id": "6014", "label": "游戏"}},
            },
        ]
    }
}


def test_parse_ranks_and_fields():
    rows = appstore_cn.parse(SAMPLE, "topgrossingapplications", "")
    assert [r["rank"] for r in rows] == [1, 2]
    assert rows[0]["name"] == "抖音"
    assert rows[0]["bundle_id"] == "com.ss.iphone.ugc.Aweme"
    assert rows[0]["category"] == "娱乐"
    assert rows[0]["release_date"] == "2016-09-25"
    assert rows[1]["price"] == ""  # 缺字段不报错
    assert rows[1]["genre_name"] == "总榜"


def test_single_entry_object():
    one = {"feed": {"entry": SAMPLE["feed"]["entry"][0]}}
    assert len(appstore_cn.parse(one, "topfreeapplications", "6014")) == 1


class FakeResp:
    def __init__(self, data):
        self._d = data

    def raise_for_status(self):
        pass

    def json(self):
        return self._d


class FakeSession:
    headers = {}

    def __init__(self):
        self.urls = []

    def get(self, url, timeout=None, **kw):
        self.urls.append(url)
        return FakeResp(SAMPLE)


def test_end_to_end(tmp_path, monkeypatch):
    monkeypatch.setattr(collect, "DATA_DIR", tmp_path)
    monkeypatch.setattr(collect, "STATUS_DIR", tmp_path / "_status")
    fake = FakeSession()
    monkeypatch.setattr(collect, "make_session", lambda: fake)
    monkeypatch.setattr(appstore_cn, "PAUSE_SECONDS", 0)

    n_feeds = len(appstore_cn.feeds())
    assert collect.main(["appstore_cn"]) == 0
    assert len(fake.urls) == n_feeds
    assert any("genre=6014" in u for u in fake.urls)
    assert all("limit=100" in u for u in fake.urls)
    files = list(tmp_path.glob("appstore_cn/*/*.csv"))
    assert len(files) == 1
    with files[0].open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 2 * n_feeds
    assert rows[0]["date"] and rows[0]["fetched_at_utc"].endswith("Z")
    status = json.loads(next((tmp_path / "_status").glob("*.json")).read_text("utf-8"))
    assert status["sources"]["appstore_cn"]["rows"] == 2 * n_feeds

    # 同一天再跑一次应跳过，不重复请求
    fake.urls.clear()
    assert collect.main(["appstore_cn"]) == 0
    assert fake.urls == []


def test_partial_failure_keeps_other_charts(tmp_path, monkeypatch):
    monkeypatch.setattr(collect, "DATA_DIR", tmp_path)
    monkeypatch.setattr(collect, "STATUS_DIR", tmp_path / "_status")
    monkeypatch.setattr(collect.time, "sleep", lambda s: None)
    monkeypatch.setattr(appstore_cn, "PAUSE_SECONDS", 0)

    class Flaky(FakeSession):
        def get(self, url, timeout=None, **kw):
            if "genre=6000" in url:
                raise ConnectionError("one feed down")
            return FakeResp(SAMPLE)

    monkeypatch.setattr(collect, "make_session", lambda: Flaky())
    assert collect.main(["appstore_cn"]) == 0
    assert list(tmp_path.glob("appstore_cn/*/*.csv"))


def test_failure_returns_nonzero(tmp_path, monkeypatch):
    monkeypatch.setattr(collect, "DATA_DIR", tmp_path)
    monkeypatch.setattr(collect, "STATUS_DIR", tmp_path / "_status")
    monkeypatch.setattr(collect.time, "sleep", lambda s: None)
    monkeypatch.setattr(appstore_cn, "PAUSE_SECONDS", 0)

    class Boom(FakeSession):
        def get(self, url, timeout=None, **kw):
            raise ConnectionError("blocked")

    monkeypatch.setattr(collect, "make_session", lambda: Boom())
    assert collect.main(["appstore_cn"]) == 1
    assert not list(tmp_path.glob("appstore_cn/*/*.csv"))


def test_podcasts_end_to_end(tmp_path, monkeypatch):
    from sources import apple_podcasts_cn

    monkeypatch.setattr(collect, "DATA_DIR", tmp_path)
    monkeypatch.setattr(collect, "STATUS_DIR", tmp_path / "_status")
    monkeypatch.setattr(apple_podcasts_cn, "PAUSE_SECONDS", 0)
    sample = {"feed": {"title": {"label": "iTunes Store：热门播客"}, "entry": SAMPLE["feed"]["entry"]}}

    class S(FakeSession):
        def get(self, url, timeout=None, **kw):
            self.urls.append(url)
            return FakeResp(sample)

    fake = S()
    monkeypatch.setattr(collect, "make_session", lambda: fake)
    assert collect.main(["apple_podcasts_cn"]) == 0
    assert all("/toppodcasts/" in u for u in fake.urls)
    assert len(fake.urls) == len(apple_podcasts_cn.GENRE_IDS)
    f = next(tmp_path.glob("apple_podcasts_cn/*/*.csv"))
    with f.open(encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    assert rows[0]["chart_title"] == "iTunes Store：热门播客"
    assert rows[0]["podcast_id"] == "1142110895"


def test_private_modules_not_sources():
    assert "_apple" not in collect.discover_sources()
    assert {"appstore_cn", "apple_podcasts_cn"} <= set(collect.discover_sources())
