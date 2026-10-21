"""每日数据时光机：把只提供"当前数据"的公开数据源，每天存一次快照，攒成历史数据。

用法:
    python collect.py                 # 运行全部数据源
    python collect.py appstore_cn     # 只运行指定数据源
    python collect.py --force         # 当天文件已存在也重新采集

每个数据源是 sources/ 下的一个模块，需提供：
    NAME: str            数据源标识，也是 data/ 下的目录名
    TITLE: str           中文名
    collect(session, run) -> list[dict]
        返回当天采集到的行；每行是扁平的 dict。
"""

from __future__ import annotations

import argparse
import csv
import importlib
import json
import pkgutil
import sys
import time
import traceback
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
STATUS_DIR = DATA_DIR / "_status"
CST = timezone(timedelta(hours=8))  # 以北京时间划分"哪一天"

USER_AGENT = (
    "cn-data-timemachine/0.1 (daily public-data snapshot for research; "
    "+https://github.com/)"
)


@dataclass
class Run:
    date: str  # 北京时间日期 YYYY-MM-DD
    fetched_at_utc: str


def make_session() -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = USER_AGENT
    return s


def get_json(session: requests.Session, url: str, retries: int = 3, **kw):
    """带重试的 GET JSON，供各数据源复用。"""
    last = None
    for i in range(retries):
        try:
            r = session.get(url, timeout=30, **kw)
            r.raise_for_status()
            return r.json()
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2 * (i + 1))
    raise last  # type: ignore[misc]


def discover_sources() -> dict:
    import sources

    mods = {}
    for info in pkgutil.iter_modules(sources.__path__):
        if info.name.startswith("_"):
            continue
        mod = importlib.import_module(f"sources.{info.name}")
        mods[mod.NAME] = mod
    return mods


def out_path(name: str, date: str) -> Path:
    return DATA_DIR / name / date[:7] / f"{date}.csv"


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for row in rows:
        for k in row:
            if k not in fields:
                fields.append(k)
    tmp = path.with_suffix(".csv.tmp")
    with tmp.open("w", newline="", encoding="utf-8-sig") as f:  # utf-8-sig: Excel 直接打开不乱码
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    tmp.replace(path)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("only", nargs="*", help="只运行这些数据源")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args(argv)

    now = datetime.now(timezone.utc)
    run = Run(
        date=now.astimezone(CST).strftime("%Y-%m-%d"),
        fetched_at_utc=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    sources = discover_sources()
    selected = args.only or sorted(sources)
    session = make_session()

    status = {"date": run.date, "fetched_at_utc": run.fetched_at_utc, "sources": {}}
    failed = 0
    for name in selected:
        mod = sources.get(name)
        if mod is None:
            print(f"[skip] 未知数据源: {name}")
            continue
        path = out_path(name, run.date)
        if path.exists() and not args.force:
            print(f"[skip] {name}: 今天已采集")
            status["sources"][name] = {"ok": True, "skipped": True}
            continue
        t0 = time.time()
        try:
            rows = mod.collect(session, run)
            if not rows:
                raise RuntimeError("没有采到任何数据")
            for r in rows:
                r.setdefault("date", run.date)
                r.setdefault("fetched_at_utc", run.fetched_at_utc)
            write_csv(path, rows)
            status["sources"][name] = {
                "ok": True,
                "rows": len(rows),
                "seconds": round(time.time() - t0, 1),
            }
            print(f"[ok]   {name}: {len(rows)} 行 -> {path}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            status["sources"][name] = {"ok": False, "error": repr(e)[:500]}
            print(f"[fail] {name}: {e!r}")
            traceback.print_exc()

    STATUS_DIR.mkdir(parents=True, exist_ok=True)
    (STATUS_DIR / f"{run.date}.json").write_text(
        json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
