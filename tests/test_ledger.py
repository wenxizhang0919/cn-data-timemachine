import importlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import collect  # noqa: E402
import ledger  # noqa: E402
import make_catalog  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts"))
import check_immutable  # noqa: E402
import verify  # noqa: E402


def setup_repo(tmp_path, monkeypatch):
    raw = tmp_path / "data" / "raw"
    led = tmp_path / "ledger"
    for mod in (ledger,):
        monkeypatch.setattr(mod, "ROOT", tmp_path)
        monkeypatch.setattr(mod, "RAW", raw)
        monkeypatch.setattr(mod, "LEDGER", led)
    monkeypatch.setattr(verify, "ROOT", tmp_path)
    monkeypatch.setattr(verify, "RAW", raw)
    monkeypatch.setattr(verify, "LEDGER", led)
    monkeypatch.setattr(ledger, "git_commit", lambda: "abc123")
    return raw, led


def add_day(raw, date, datasets=("a", "b")):
    for ds in datasets:
        p = raw / "cat" / ds / date[:7] / f"{date}.csv"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"﻿x,date\n1,{date}\n2,{date}\n", encoding="utf-8")
    st = raw / "_status" / f"{date}.json"
    st.parent.mkdir(parents=True, exist_ok=True)
    st.write_text(json.dumps({"date": date, "sources": {d: {"ok": True, "rows": 2} for d in datasets}}))


def test_chain_builds_and_verifies(tmp_path, monkeypatch):
    raw, led = setup_repo(tmp_path, monkeypatch)
    add_day(raw, "2026-10-21")
    p1 = ledger.write("2026-10-21")
    add_day(raw, "2026-10-22")
    p2 = ledger.write("2026-10-22")

    e1 = json.loads(p1.read_text("utf-8"))
    e2 = json.loads(p2.read_text("utf-8"))
    assert e1["prev_ledger_sha256"] is None
    assert e2["prev_date"] == "2026-10-21"
    assert e2["prev_ledger_sha256"] == ledger.sha256_file(p1)
    assert e1["files"][0]["rows"] == 2
    assert e1["files"][0]["content_id"].startswith("a@2026-10-21#")
    assert e1["files"][0]["category"] == "cat"
    assert (led / "HEAD").read_text().startswith("2026-10-22 ")
    assert verify.main() == 0


def test_tampering_with_data_is_detected(tmp_path, monkeypatch):
    raw, _ = setup_repo(tmp_path, monkeypatch)
    add_day(raw, "2026-10-21")
    ledger.write("2026-10-21")
    f = raw / "cat" / "a" / "2026-10" / "2026-10-21.csv"
    f.write_text(f.read_text("utf-8").replace("1,2026", "9,2026"), encoding="utf-8")
    assert verify.main() == 1


def test_tampering_with_old_ledger_breaks_chain(tmp_path, monkeypatch):
    raw, led = setup_repo(tmp_path, monkeypatch)
    add_day(raw, "2026-10-21")
    p1 = ledger.write("2026-10-21")
    add_day(raw, "2026-10-22")
    ledger.write("2026-10-22")
    p1.write_text(p1.read_text("utf-8").replace('"rows": 2', '"rows": 9', 1), encoding="utf-8")
    assert verify.main() == 1


def test_unregistered_backfill_is_detected(tmp_path, monkeypatch):
    raw, _ = setup_repo(tmp_path, monkeypatch)
    add_day(raw, "2026-10-21")
    ledger.write("2026-10-21")
    add_day(raw, "2026-10-20")  # 事后"补造"的一天，没有账本
    assert verify.main() == 1


def test_gap_is_reported_not_fatal(tmp_path, monkeypatch, capsys):
    raw, _ = setup_repo(tmp_path, monkeypatch)
    add_day(raw, "2026-10-21")
    ledger.write("2026-10-21")
    add_day(raw, "2026-10-24")
    ledger.write("2026-10-24")
    assert verify.main() == 0
    assert "2026-10-21 → 2026-10-24" in capsys.readouterr().out


def test_ledger_bytes_are_canonical(tmp_path, monkeypatch):
    raw, _ = setup_repo(tmp_path, monkeypatch)
    add_day(raw, "2026-10-21")
    p = ledger.write("2026-10-21")
    obj = json.loads(p.read_text("utf-8"))
    assert ledger.dump(obj) == p.read_bytes()


def test_check_immutable_rules():
    today = "2026-10-22"
    ok = (
        "A\tdata/raw/a/2026-10/2026-10-22.csv\n"
        "M\tdata/raw/_status/2026-10-22.json\n"
        "A\tledger/2026-10-22.json\n"
        "M\tledger/HEAD\n"
        "M\tledger/2026-10-21.json.ots\n"
        "M\tdata/raw/apps/appstore_cn/README.md\n"
    )
    assert check_immutable.violations(ok, today) == []
    bad = "M\tdata/raw/a/2026-10/2026-10-21.csv\nD\tledger/2026-10-20.json\n"
    assert len(check_immutable.violations(bad, today)) == 2


def test_every_source_has_citation_metadata():
    for name, mod in collect.discover_sources().items():
        assert mod.NAME == name
        assert mod.TITLE and mod.SOURCE_URL.startswith("http")
        assert mod.LICENSE[:1] in "🟢🟡"
        assert isinstance(mod.FIELDS, dict) and mod.FIELDS
        assert mod.__doc__
        from sources._categories import CATEGORIES

        assert mod.CATEGORY in CATEGORIES


def test_catalog_renders(tmp_path, monkeypatch):
    monkeypatch.setattr(make_catalog, "LEDGER", tmp_path)
    (tmp_path / "2026-10-21.json").write_text(
        json.dumps({"date": "2026-10-21", "files": [{"dataset": "appstore_cn"}]})
    )
    (tmp_path / "2026-10-23.json").write_text(
        json.dumps({"date": "2026-10-23", "files": [{"dataset": "appstore_cn"}]})
    )
    cat = make_catalog.build()
    a = next(d for d in cat if d["id"] == "appstore_cn")
    assert a["first_snapshot"] == "2026-10-21" and a["days_archived"] == 2 and a["days_missing"] == 1
    assert "date" in a["fields"] and "rank" in a["fields"]
    assert a["category"] == "apps" and a["path"].startswith("data/raw/apps/appstore_cn/")
    md = make_catalog.render_md(cat)
    assert "## 应用与游戏" in md and "data/raw/apps/appstore_cn/" in md
    page = make_catalog.render_dataset(a)
    assert "数据集 ID：`appstore_cn`" in page and "snapshot-YYYY-MM-DD" in page and "| `rank` |" in page
