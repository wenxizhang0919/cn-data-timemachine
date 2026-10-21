"""每日数据时光机：把只提供"当前数据"的公开数据源，每天存一次快照，攒成历史数据。

用法:
    python collect.py                 # 运行全部数据源
    python collect.py appstore_cn     # 只运行指定数据源
    python collect.py --force         # 当天文件已存在也重新采集（只会覆盖"当天"的文件）

原始层 data/raw/ 的规则：每天一个文件，只在当天写入；过了当天永不修改。
每次采集都在 data/raw/_status/<日期>.json 里记录行数、耗时和文件的 sha256。

每个数据源是 sources/ 下的一个模块，需提供：
    NAME: str            数据集固定 ID，也是 data/raw/ 下的目录名
    TITLE: str           中文名
    SOURCE_URL: str      数据来源（原始服务的地址）
    LICENSE: str         许可/使用条款说明（含 🟢/🟡 等级）
    FIELDS: dict         字段名 -> 字段说明
    collect(session, run) -> list[dict]
        返回当天采集到的行；每行是扁平的 dict。
"""

from __future__ import annotations

import argparse
import csv
import hashlib
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
DATA_DIR = ROOT / "data" / "raw"
STATUS_DIR = DATA_DIR / "_status"
CST = timezone(timedelta(hours=8))  # 以北京时间划分"哪一天"

REPO_URL = "https://github.com/wenxizhang0919/cn-data-timemachine"
USER_AGENT = f"cn-data-timemachine/0.2 (daily snapshot archive for research; +{REPO_URL})"

# 每行都会自动加上的公共字段
COMMON_FIELDS = {
    "date": "采集日期（北京时间），即数据版本日期",
    "fetched_at_utc": "实际采集时刻（UTC）",
}


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


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


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
    # 未指定时只运行启用的数据源；ENABLED = False 的数据源可手动指定运行
    selected = args.only or sorted(n for n, m in sources.items() if getattr(m, "ENABLED", True))
    session = make_session()

    status_path = STATUS_DIR / f"{run.date}.json"
    status = {"date": run.date, "sources": {}}
    if status_path.exists():  # 同一天多次运行（如只补采一个源）时保留其他源的记录
        status = json.loads(status_path.read_text(encoding="utf-8"))
    failed = 0
    for name in selected:
        mod = sources.get(name)
        if mod is None:
            print(f"[skip] 未知数据源: {name}")
            continue
        path = out_path(name, run.date)
        if path.exists() and not args.force:
            print(f"[skip] {name}: 今天已采集")
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
                "fetched_at_utc": run.fetched_at_utc,
                "file": path.relative_to(DATA_DIR).as_posix(),
                "sha256": sha256(path),
            }
            print(f"[ok]   {name}: {len(rows)} 行 -> {path}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            status["sources"][name] = {
                "ok": False,
                "fetched_at_utc": run.fetched_at_utc,
                "error": repr(e)[:500],
            }
            print(f"[fail] {name}: {e!r}")
            traceback.print_exc()

    STATUS_DIR.mkdir(parents=True, exist_ok=True)
    status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
