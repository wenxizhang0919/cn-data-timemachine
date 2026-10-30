"""当天文件行数骤降时，后续重试再采一次、只在行数更多时替换（2026-10-29 steam_cn 只采到 99 行）。"""

import csv
import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import collect  # noqa: E402


def _setup(tmp_path, monkeypatch, sizes):
    monkeypatch.setattr(collect, "DATA_DIR", tmp_path)
    monkeypatch.setattr(collect, "STATUS_DIR", tmp_path / "_status")
    (tmp_path / "_status").mkdir()
    # 前一次（往日）采到 200 行
    (tmp_path / "_status" / "2000-01-01.server.json").write_text(
        json.dumps({"sources": {"d": {"ok": True, "rows": 200}}}), encoding="utf-8"
    )
    it = iter(sizes)
    calls = []

    def fake_collect(s, r):
        calls.append(1)
        return [{"i": i} for i in range(next(it))]

    d = SimpleNamespace(NAME="d", CATEGORY="c", RUNNER="server", collect=fake_collect)
    monkeypatch.setattr(collect, "discover_sources", lambda: {"d": d})
    return calls


def _rows(tmp_path):
    p = next(tmp_path.glob("c/d/*/*.csv"))
    with p.open(encoding="utf-8-sig", newline="") as f:
        return len(list(csv.DictReader(f)))


def _status(tmp_path):
    p = next(x for x in (tmp_path / "_status").glob("*.json") if not x.name.startswith("2000"))
    return json.loads(p.read_text(encoding="utf-8"))["sources"]["d"]


def test_partial_file_is_retried_and_replaced(tmp_path, monkeypatch):
    calls = _setup(tmp_path, monkeypatch, [99, 200])
    assert collect.main(["--runner", "server"]) == 1  # 骤降，报警
    assert _rows(tmp_path) == 99 and "warning" in _status(tmp_path)
    assert collect.main(["--runner", "server"]) == 0  # 重试采全，替换
    assert _rows(tmp_path) == 200 and "warning" not in _status(tmp_path)
    assert collect.main(["--runner", "server"]) == 0  # 已正常，不再重采
    assert len(calls) == 2


def test_retry_with_fewer_rows_keeps_original(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, [99, 50])
    collect.main(["--runner", "server"])
    collect.main(["--runner", "server"])
    assert _rows(tmp_path) == 99 and _status(tmp_path)["rows"] == 99


def test_source_reported_partial_is_retried(tmp_path, monkeypatch):
    """2026-10-30 steam_cn 畅销榜第 3 页出错，只得 149 行（未到骤降阈值），由数据源自己报告不完整。"""
    calls = _setup(tmp_path, monkeypatch, [149, 200])
    d = collect.discover_sources()["d"]
    inner = d.collect

    def fake(s, r):
        rows = inner(s, r)
        d.LAST_WARNING = "部分榜单采集中途出错" if len(rows) < 200 else ""
        return rows

    d.collect = fake
    assert collect.main(["--runner", "server"]) == 1
    assert _rows(tmp_path) == 149 and "warning" in _status(tmp_path)
    assert collect.main(["--runner", "server"]) == 0
    assert _rows(tmp_path) == 200 and "warning" not in _status(tmp_path)
    assert len(calls) == 2


def test_steam_collect_reports_partial(monkeypatch):
    import collect as c
    from sources import steam_cn

    page = '<a href="x" data-ds-appid="{0}"><span class="title">G{0}</span></a>'
    n = iter(range(10_000))

    def fake_get_json(session, url, retries=3, params=None):
        if params["filter"] == "topsellers" and params["start"] == 50:
            raise RuntimeError("502")
        return {"results_html": "".join(page.format(next(n)) for _ in range(25))}

    monkeypatch.setattr(c, "get_json", fake_get_json)
    monkeypatch.setattr(steam_cn, "PAUSE_SECONDS", 0)
    rows = steam_cn.collect(None, None)
    assert len(rows) == 150 and "topsellers" in steam_cn.LAST_WARNING
