"""健康检查与兜底采集的测试。"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import collect  # noqa: E402
import health  # noqa: E402
import ledger  # noqa: E402
import make_catalog  # noqa: E402

D = "2026-10-22"


def mods():
    return {
        "a": SimpleNamespace(NAME="a", CATEGORY="apps", TITLE="A"),
        "w": SimpleNamespace(NAME="w", CATEGORY="weather", TITLE="W", RUNNER="server", INTRADAY=True, KEY=("k",)),
    }


def setup(tmp_path, monkeypatch, files=("a", "w"), status=None, ledger_files=None):
    raw, led = tmp_path / "data" / "raw", tmp_path / "ledger"
    (raw / "_status").mkdir(parents=True)
    led.mkdir()
    for m in (ledger, make_catalog):
        monkeypatch.setattr(m, "LEDGER", led)
    monkeypatch.setattr(ledger, "RAW", raw)
    monkeypatch.setattr(ledger, "ROOT", tmp_path)
    monkeypatch.setattr(collect, "DATA_DIR", raw)
    ms = mods()
    monkeypatch.setattr(health, "discover_sources", lambda: ms)
    monkeypatch.setattr(health, "out_path", collect.out_path)
    monkeypatch.setattr(ledger, "git_commit", lambda: "x")
    for n in files:
        p = collect.out_path(ms[n], D)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("k,v\n1,2\n", encoding="utf-8")
    st = status or {
        "a": {"ok": True, "rows": 1, "fetched_at_utc": "2026-10-22T02:00:00Z"},
    }
    (raw / "_status" / f"{D}.json").write_text(json.dumps({"runner": "github", "sources": st}), "utf-8")
    sst = {"w": {"ok": True, "rows": 1, "runs": 3, "fetched_at_utc": "2026-10-22T06:00:00Z"}}
    (raw / "_status" / f"{D}.server.json").write_text(json.dumps({"runner": "server", "sources": sst}), "utf-8")
    ledger.write(D)
    monkeypatch.setattr(health.subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=0, stdout="", stderr=""))
    return raw


def at(h, m=0):
    # 北京时间 h:m
    return datetime(2026, 10, 22, h - 8, m, tzinfo=timezone.utc) if h >= 8 else datetime(2026, 10, 21, h + 16, m, tzinfo=timezone.utc)


def test_all_good(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch)
    rep = health.check(D, at(15, 30))
    assert rep["problems"] == [], rep["problems"]
    assert "一切正常" in health.render(rep)


def test_missing_source_pending_before_deadline_then_problem(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch, files=("w",), status={})
    assert not [p for p in health.check(D, at(15))["problems"] if "`a`" in p]
    probs = health.check(D, at(22, 47))["problems"]
    assert any("`a`" in p and "没有数据" in p for p in probs)


def test_intraday_silence_flags_server_down(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch)
    probs = health.check(D, at(19))["problems"]  # 最后一次新数据是 14:00，已 5 小时
    assert any("`w`" in p and "没有新数据" in p for p in probs)


def test_failed_status_and_host_warning_reported(tmp_path, monkeypatch):
    raw = setup(tmp_path, monkeypatch, files=("w",), status={"a": {"ok": False, "error": "502"}})
    p = raw / "_status" / f"{D}.server.json"
    st = json.loads(p.read_text("utf-8"))
    st["host_warning"] = "磁盘剩余 1.0 GB"
    p.write_text(json.dumps(st), "utf-8")
    probs = health.check(D, at(15))["problems"]
    assert any("采集失败" in x for x in probs) and any("磁盘" in x for x in probs)


def test_stale_ledger_detected(tmp_path, monkeypatch):
    raw = setup(tmp_path, monkeypatch)
    p = collect.out_path(mods()["w"], D)
    p.write_text("k,v\n1,2\n3,4\n", encoding="utf-8")  # 推送了新数据，账本未重建
    probs = health.check(D, at(15))["problems"]
    assert any("账本与数据文件不一致" in x for x in probs)


def test_strict_exit_code(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch, files=("w",), status={})
    monkeypatch.setattr(health, "datetime", type("DT", (datetime,), {"now": staticmethod(lambda tz=None: at(23))}))
    assert health.main(["--date", D, "--strict"]) == 1
    assert health.main(["--date", D]) == 0


def test_fallback_collects_other_runners_missing_daily_sources(tmp_path, monkeypatch):
    monkeypatch.setattr(collect, "DATA_DIR", tmp_path)
    monkeypatch.setattr(collect, "STATUS_DIR", tmp_path / "_status")
    ran = []

    def mk(name, runner="github", intraday=False):
        ns = SimpleNamespace(NAME=name, CATEGORY="c", RUNNER=runner,
                             collect=lambda s, r: ran.append(name) or [{"x": 1}])
        if intraday:
            ns.INTRADAY, ns.KEY = True, ("x",)
        return ns

    fake = {"gh1": mk("gh1"), "gh2": mk("gh2"), "ghi": mk("ghi", intraday=True), "srv": mk("srv", "server")}
    monkeypatch.setattr(collect, "discover_sources", lambda: fake)
    assert collect.main(["gh1"]) == 0  # GitHub 已采到 gh1
    ran.clear()
    assert collect.main(["--runner", "server", "--fallback"]) == 0
    assert sorted(ran) == ["gh2", "srv"]  # 只兜底缺的、一天一次的
    st = json.loads(next((tmp_path / "_status").glob("*.server.json")).read_text("utf-8"))
    assert "gh2" in st["sources"] and "gh1" not in st["sources"]


def test_intraday_no_file_today_flags_server_down(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch, files=("a",))
    assert not [p for p in health.check(D, at(2))["problems"] if "`w`" in p]
    probs = health.check(D, at(21, 13))["problems"]  # 服务器整天没推送，22 点前也要报警
    assert any("`w`" in p and "没有任何数据" in p for p in probs)


def test_strict_after_midnight_checks_previous_day(tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(health, "check", lambda d, now: seen.append(d) or {"problems": [], "rows": [], "date": d, "checked_at": ""})
    monkeypatch.setattr(health, "render", lambda rep: "")

    class FakeDT(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 10, 22, 18, 30, tzinfo=timezone.utc)  # 北京时间 10-23 02:30

    monkeypatch.setattr(health, "datetime", FakeDT)
    health.main(["--strict"])
    health.main([])
    assert seen == ["2026-10-22", "2026-10-23"]
