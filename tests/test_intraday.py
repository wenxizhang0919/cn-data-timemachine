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

THEAD = [
    "省份", "流域", "断面名称", "监测时间", "水质类别", "水温(℃)", "pH(无量纲)",
    "溶解氧(mg/L)", "电导率(μS/cm)", "浊度(NTU)", "高锰酸盐指数(mg/L)", "氨氮(mg/L)",
    "总磷(mg/L)", "总氮(mg/L)", "叶绿素α(mg/L)", "藻密度(cells/L)", "站点情况",
]


def row(station, t, cls="2", ph="7.62"):
    return [
        "浙江省", "长江流域",
        f"<span data-toggle='tooltip' title='{station}'>{station[:4]}</span>",
        t, cls, "18.2", f"<span title='原始值：{ph}'>{ph}</span>", "8.1", "--", "5.3",
        "2.1", "0.05", "0.061", "1.2", "--", "--", "正常",
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


def test_parse_cleans_html_and_builds_full_time():
    j = {"result": 1, "total": 1, "thead": THEAD, "tbody": [row("钱塘江闸口断面", "10-22 12:00")]}
    rows = wq.parse(j, "2026-10-22")
    r = rows[0]
    assert r["station"] == "钱塘江闸口断面"  # 完整名称取自 title
    assert r["ph"] == "7.62"  # 去掉提示框标签
    assert r["conductivity_us_cm"] == ""  # "--" 视为空
    assert r["monitor_time"] == "2026-10-22 12:00"
    assert r["water_class"] == "Ⅱ" and r["water_class_code"] == "2"


def test_year_inferred_across_new_year():
    assert wq.full_time("12-31 20:00", "2027-01-01") == "2026-12-31 20:00"
    assert wq.full_time("01-01 00:00", "2027-01-01") == "2027-01-01 00:00"
    assert wq.full_time("2026-10-22 08:00", "2026-10-22") == "2026-10-22 08:00"
    assert wq.full_time("", "2026-10-22") == ""


def test_unknown_header_kept_as_extra_column():
    j = {"result": 1, "thead": THEAD + ["新指标(mg/L)"], "tbody": [row("甲断面", "10-22 08:00") + ["0.3"]]}
    s = FakeSession([j])
    out = wq.collect(s, SimpleNamespace(date="2026-10-22"))
    assert out[0]["extra_17"] == "0.3"
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
