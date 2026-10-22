"""一天多次采集（INTRADAY）与全国地表水水质数据源的测试。"""

import csv
import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import collect  # noqa: E402
from sources import cn_surface_water_quality as wq  # noqa: E402

# 与 2026-10-22 在服务器上实测到的官网返回格式一致
U = "<br/><span class='unit'>({})</span>"
THEAD = ["省份", "流域", "断面名称", "监测时间", "水质类别"] + [
    n + U.format(u) for n, u in [
        ("水温", "℃"), ("pH", "无量纲"), ("溶解氧", "mg/L"), ("电导率", "μS/cm"), ("浊度", "NTU"),
        ("高锰酸盐指数", "mg/L"), ("氨氮", "mg/L"), ("总磷", "mg/L"), ("总氮", "mg/L"),
        ("叶绿素α", "mg/L"), ("藻密度", "cells/L"),
    ]
]


def v(shown, orig):
    return f"<span title='原始值：{orig}'>{shown}</span>"


QC = "<span data-toggle='tooltip' data-placement='right' title='当天质控不合格'>--</span>"


def row(station, t, cls="2", ph="7.58"):
    return [
        "北京市", "海河流域", station, t, cls,
        v("17.0", "17.01"), v(ph, ph), v("8.61", "8.61"), v("367.4", "367.36"), v("9.3", "9.345"),
        QC, v("0.029", "0.029"), v("0.018", "0.018"), v("1.19", "1.19"), "--", "--",
    ]


class Resp:
    def __init__(self, d):
        self.d = d

    def raise_for_status(self):
        pass

    def json(self):
        return self.d


class FakeSession:
    def __init__(self, payloads):
        self.payloads = list(payloads)
        self.posts = []

    def post(self, url, data=None, headers=None, timeout=None):
        self.posts.append(dict(data))
        return Resp(self.payloads.pop(0))


def test_parse_matches_live_format():
    j = {"result": 1, "total": 1, "records": 1, "thead": THEAD, "tbody": [row("鼓楼外大街", "10-22 14:00", "1")]}
    r = wq.parse(j, "2026-10-22")[0]
    assert r["station"] == "鼓楼外大街" and r["province"] == "北京市"
    assert r["water_temp_c"] == "17.0" and r["water_temp_c_orig"] == "17.01"  # 显示值与原始值
    assert r["ph"] == "7.58" and r["ph_orig"] == ""  # 相同时原始值留空
    assert r["permanganate_index_mg_l"] == "" and r["notes"] == "高锰酸盐指数：当天质控不合格"
    assert r["chlorophyll_a_mg_l"] == ""  # "--" 视为空
    assert r["monitor_time"] == "2026-10-22 14:00"
    assert r["water_class"] == "Ⅰ" and r["water_class_code"] == "1"
    assert not [k for k in r if k.startswith("extra_")]


def test_station_full_name_from_title():
    assert wq.station_name("<span title='钱塘江闸口断面'>钱塘江闸</span>") == "钱塘江闸口断面"
    assert wq.station_name("鼓楼外大街") == "鼓楼外大街"


def test_year_inferred_across_new_year():
    assert wq.full_time("12-31 20:00", "2027-01-01") == "2026-12-31 20:00"
    assert wq.full_time("01-01 00:00", "2027-01-01") == "2027-01-01 00:00"
    assert wq.full_time("2026-10-22 08:00", "2026-10-22") == "2026-10-22 08:00"
    assert wq.full_time("", "2026-10-22") == ""


def test_unknown_header_kept_as_extra_column():
    j = {"result": 1, "thead": THEAD + ["新指标" + U.format("mg/L")],
         "tbody": [row("甲断面", "10-22 08:00") + [v("0.3", "0.31")]]}
    s = FakeSession([j])
    out = wq.collect(s, SimpleNamespace(date="2026-10-22"))
    assert out[0]["extra_16"] == "0.3" and out[0]["extra_16_orig"] == "0.31"
    assert set(wq.FIELDS) <= set(out[0])


def test_collect_uses_unpaged_national_request_and_dedups():
    j = {"result": 1, "total": 1, "thead": THEAD,
         "tbody": [row("甲断面", "10-22 08:00"), row("甲断面", "10-22 08:00"), row("乙断面", "10-22 08:00")]}
    s = FakeSession([j])
    out = wq.collect(s, SimpleNamespace(date="2026-10-22"))
    assert len(out) == 2
    assert s.posts[0]["action"] == "getRealDatas" and s.posts[0]["PageIndex"] == "-1"


def test_rate_limit_response_is_retried(monkeypatch):
    monkeypatch.setattr(wq.time, "sleep", lambda s: None)
    ok = {"result": 1, "total": 1, "thead": THEAD, "tbody": [row("甲断面", "10-22 08:00")]}
    s = FakeSession([-1, ok])
    assert len(wq.collect(s, SimpleNamespace(date="2026-10-22"))) == 1


def test_merge_intraday_keeps_first_seen():
    a = [{"s": "甲", "t": "08:00", "v": "1"}]
    b = [{"s": "甲", "t": "08:00", "v": "999"}, {"s": "甲", "t": "12:00", "v": "2"}]
    merged, added = collect.merge_intraday(a, b, ("s", "t"))
    assert added == 1 and [r["v"] for r in merged] == ["1", "2"]


def _setup(tmp_path, monkeypatch, batches):
    monkeypatch.setattr(collect, "DATA_DIR", tmp_path)
    monkeypatch.setattr(collect, "STATUS_DIR", tmp_path / "_status")
    it = iter(batches)
    daily_calls = []
    intr = SimpleNamespace(
        NAME="intr", CATEGORY="c", RUNNER="server", INTRADAY=True, KEY=("s", "t"),
        collect=lambda s, r: [dict(x) for x in next(it)],
    )
    daily = SimpleNamespace(
        NAME="daily", CATEGORY="c", RUNNER="server",
        collect=lambda s, r: daily_calls.append(1) or [{"x": 1}],
    )
    monkeypatch.setattr(collect, "discover_sources", lambda: {"intr": intr, "daily": daily})
    return daily_calls


def _read(tmp_path):
    p = next(tmp_path.glob("c/intr/*/*.csv"))
    with p.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f)), p


def test_intraday_runs_append_and_skip_when_nothing_new(tmp_path, monkeypatch):
    b1 = [{"s": "甲", "t": "08:00"}, {"s": "乙", "t": "08:00"}]
    b2 = [{"s": "甲", "t": "08:00"}, {"s": "乙", "t": "08:00"}, {"s": "甲", "t": "12:00"}]
    daily_calls = _setup(tmp_path, monkeypatch, [b1, b2, b2])

    assert collect.main(["--runner", "server"]) == 0
    rows, path = _read(tmp_path)
    assert len(rows) == 2 and len(daily_calls) == 1

    # 第二次：每日数据源跳过；一天多次的数据源追加 1 行
    assert collect.main(["--runner", "server"]) == 0
    rows, _ = _read(tmp_path)
    assert [(r["s"], r["t"]) for r in rows] == [("甲", "08:00"), ("乙", "08:00"), ("甲", "12:00")]
    assert len(daily_calls) == 1
    st = json.loads(next((tmp_path / "_status").glob("*.server.json")).read_text("utf-8"))
    e = st["sources"]["intr"]
    assert e["rows"] == 3 and e["fetched"] == 3 and e["added"] == 1 and e["runs"] == 2

    # 第三次：没有新记录，文件和状态都不变（不会产生提交）
    before = (path.read_bytes(), next((tmp_path / "_status").glob("*.server.json")).read_bytes())
    assert collect.main(["--runner", "server", "--intraday-only"]) == 0
    after = (path.read_bytes(), next((tmp_path / "_status").glob("*.server.json")).read_bytes())
    assert before == after and len(daily_calls) == 1


def test_intraday_failure_keeps_earlier_success(tmp_path, monkeypatch):
    batches = [[{"s": "甲", "t": "08:00"}]]
    _setup(tmp_path, monkeypatch, batches)
    assert collect.main(["--runner", "server", "--intraday-only"]) == 0
    srcs = collect.discover_sources()
    srcs["intr"].collect = lambda s, r: (_ for _ in ()).throw(RuntimeError("网络错误"))
    assert collect.main(["--runner", "server", "--intraday-only"]) == 1
    st = json.loads(next((tmp_path / "_status").glob("*.server.json")).read_text("utf-8"))
    e = st["sources"]["intr"]
    assert e["ok"] is True and e["rows"] == 1 and "网络错误" in e["last_error"]
    assert "daily" not in st["sources"]  # --intraday-only 不运行每日数据源


def test_intraday_anomaly_compares_single_fetch(tmp_path, monkeypatch):
    big = [{"s": str(i), "t": "08:00"} for i in range(10)]
    small = [{"s": "x", "t": "12:00"}]
    _setup(tmp_path, monkeypatch, [big, small])
    assert collect.main(["--runner", "server", "--intraday-only"]) == 0
    assert collect.main(["--runner", "server", "--intraday-only"]) == 1  # 单次只抓到 1 行，骤降
    st = json.loads(next((tmp_path / "_status").glob("*.server.json")).read_text("utf-8"))
    assert "warning" in st["sources"]["intr"]


def test_water_quality_is_server_intraday():
    m = collect.discover_sources()["cn_surface_water_quality"]
    assert m.RUNNER == "server" and m.INTRADAY and set(m.KEY) <= set(m.FIELDS)


def test_append_is_byte_identical_to_full_rewrite(tmp_path):
    a = [{"s": "甲", "t": "08:00", "v": "1,5"}, {"s": "乙", "t": "08:00", "v": '有"引号"'}]
    b = [{"s": "甲", "t": "08:00", "v": "x"}, {"s": "甲", "t": "12:00", "v": "2"}]
    p1, p2 = tmp_path / "a.csv", tmp_path / "b.csv"
    collect.write_csv(p1, a)
    total, added = collect.append_intraday(p1, b, ("s", "t"))
    merged, _ = collect.merge_intraday(a, b, ("s", "t"))
    collect.write_csv(p2, merged)
    assert (total, added) == (3, 1)
    assert p1.read_bytes() == p2.read_bytes()
    assert not (tmp_path / "a.csv.tmp").exists()


def test_append_falls_back_to_rewrite_when_new_column_appears(tmp_path):
    p = tmp_path / "a.csv"
    collect.write_csv(p, [{"s": "甲", "t": "08:00"}])
    total, added = collect.append_intraday(p, [{"s": "甲", "t": "12:00", "new": "9"}], ("s", "t"))
    assert (total, added) == (2, 1)
    rows = collect.read_csv(p)
    assert rows[0]["new"] == "" and rows[1]["new"] == "9"
