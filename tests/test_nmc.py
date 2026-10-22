"""中央气象台两个数据集的测试（假数据结构与 2026-10-22 实测一致）。"""

import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pytest  # noqa: E402

from sources import _nmc, cn_city_weather_forecast as fc, cn_weather_hourly_obs as obs  # noqa: E402

RUN = SimpleNamespace(date="2026-10-22", fetched_at_utc="2026-10-22T02:47:00Z")

NO_WARN = {k: "9999" for k in ("alert", "pic", "province", "city", "url", "issuecontent", "fmeans", "signaltype", "signallevel", "pic2")}
NO_WARN["issuetime"] = ""


def weather(temp=21.6, warn=None):
    return {
        "code": 0,
        "msg": "success",
        "data": {
            "real": {"publish_time": "2026-10-22 14:35", "warn": warn or NO_WARN},
            "predict": {
                "publish_time": "2026-10-22 12:00",
                "detail": [
                    {"date": f"2026-10-2{2 + i}", "pt": "2026-10-22 12:00",
                     "day": {"weather": {"info": "晴", "img": "0", "temperature": "16"}, "wind": {"direct": "南风", "power": "微风"}},
                     "night": {"weather": {"info": "多云", "img": "1", "temperature": "9999" if i == 0 else "5"}, "wind": {"direct": "南风", "power": "微风"}},
                     "precipitation": 0}
                    for i in range(7)
                ],
            },
            "air": {"forecasttime": "2026-10-22 14:00", "aqi": 65, "aq": 2, "text": "良"},
            "passedchart": [
                {"rain1h": 0, "rain24h": 9999, "rain12h": 9999, "rain6h": 9999, "temperature": temp, "tempDiff": "",
                 "humidity": 50, "pressure": 1018, "windDirection": 104, "windSpeed": 6.4, "time": f"2026-10-22 {h:02d}:00"}
                for h in range(14, -1, -1)
            ] + [
                {"rain1h": 9999, "rain24h": 9999, "rain12h": 9999, "rain6h": 9999, "temperature": 9999, "tempDiff": "",
                 "humidity": 66, "pressure": 1019, "windDirection": 3, "windSpeed": 6.8, "time": f"2026-10-21 {h:02d}:00"}
                for h in range(23, 14, -1)
            ],
        },
    }


class Resp:
    def __init__(self, d):
        self.d = d

    def raise_for_status(self):
        pass

    def json(self):
        return self.d


class FakeSession:
    def __init__(self, fail=()):
        self.fail = set(fail)
        self.calls = 0

    def get(self, url, headers=None, timeout=None):
        self.calls += 1
        path = url.replace(_nmc.BASE, "")
        if path == "/rest/province/all":
            return Resp([{"code": "AZJ", "name": "浙江省"}, {"code": "ABJ", "name": "北京市"}])
        if path == "/rest/province/AZJ":
            return Resp([{"code": "HIieJ", "province": "浙江省", "city": "杭州"}, {"code": "Wqsps", "province": "浙江省", "city": "宁波"}])
        if path == "/rest/province/ABJ":
            return Resp([{"code": "AAAAA", "province": "北京市", "city": "北京"}])
        code = path.split("=")[-1]
        if code in self.fail:
            raise RuntimeError("timeout")
        warn = None
        if code == "AAAAA":
            warn = {**NO_WARN, "signaltype": "大风", "signallevel": "蓝色", "issuetime": "2026-10-22 10:00", "issuecontent": "北京市气象台发布大风蓝色预警"}
        return Resp(weather(warn=warn))


@pytest.fixture(autouse=True)
def fast(monkeypatch):
    monkeypatch.setattr(_nmc, "SLEEP", 0)
    monkeypatch.setattr(_nmc.time, "sleep", lambda s: None)
    _nmc._cache.clear()


def test_hourly_obs_rows_and_missing_values():
    rows = obs.collect(FakeSession(), RUN)
    assert len(rows) == 3 * 24
    hz = [r for r in rows if r["city"] == "杭州"]
    assert hz[0]["obs_time"] == "2026-10-21 15:00" and hz[-1]["obs_time"] == "2026-10-22 14:00"  # 按时间排序
    old = hz[0]
    assert old["temperature_c"] == "" and old["rain_1h_mm"] == "" and old["humidity_pct"] == 66  # 9999 -> 空
    assert set(obs.FIELDS) == set(rows[0])


def test_forecast_rows_lead_days_aqi_and_warning():
    rows = fc.collect(FakeSession(), RUN)
    assert len(rows) == 3 * 7
    hz = [r for r in rows if r["city"] == "杭州"]
    assert [r["lead_days"] for r in hz] == [str(i) for i in range(7)]
    assert hz[0]["night_temp_c"] == "" and hz[1]["night_temp_c"] == "5"
    assert hz[0]["aqi"] == 65 and hz[0]["aqi_text"] == "良"
    assert hz[0]["warning_signal"] == "" and hz[0]["warning_content"] == ""
    bj = [r for r in rows if r["city"] == "北京"][0]
    assert bj["warning_signal"] == "大风" and bj["warning_level"] == "蓝色"
    assert set(fc.FIELDS) == set(rows[0])


def test_two_datasets_share_one_round_of_requests():
    s = FakeSession()
    obs.collect(s, RUN)
    n = s.calls
    fc.collect(s, RUN)
    assert s.calls == n  # 第二个数据集不再重复请求


def test_mass_failure_aborts_so_a_later_slot_retries():
    with pytest.raises(RuntimeError, match="抓取失败"):
        obs.collect(FakeSession(fail={"Wqsps"}), RUN)  # 1/3 失败，超过 20%


def test_partial_failure_tolerated(monkeypatch):
    monkeypatch.setattr(_nmc, "MAX_FAIL_RATIO", 0.5)
    rows = obs.collect(FakeSession(fail={"Wqsps"}), RUN)
    assert {r["city"] for r in rows} == {"杭州", "北京"}
