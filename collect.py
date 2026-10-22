"""每日数据时光机：把只提供"当前数据"的公开数据源，每天存一次快照，攒成历史数据。

用法:
    python collect.py                 # 运行全部数据源
    python collect.py appstore_cn     # 只运行指定数据源
    python collect.py --force         # 当天文件已存在也重新采集（只会覆盖"当天"的文件）

原始层 data/raw/<分类>/<数据集ID>/ 的规则：每天一个文件，只在当天写入；过了当天永不修改。
每次采集都在 data/raw/_status/<日期>.json 里记录行数、耗时和文件的 sha256。

每个数据源是 sources/ 下的一个模块，需提供：
    NAME: str            数据集固定 ID（永不改变）
    CATEGORY: str        分类目录名，见 sources/_categories.py
    RUNNER: str          （可选）由哪台机器采集：github（默认，海外）或 server（国内云服务器）
    TITLE: str           中文名
    SOURCE_URL: str      数据来源（原始服务的地址）
    LICENSE: str         许可/使用条款说明（含 🟢/🟡 等级）
    FIELDS: dict         字段名 -> 字段说明
    INTRADAY: bool       （可选）一天内多次采集：新行按 KEY 去重后追加进当天文件；默认 False（一天一次）
    KEY: tuple           （INTRADAY 时必填）判断"同一条记录"的字段，如 (站点, 监测时刻)
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


def out_path(mod, date: str) -> Path:
    """data/raw/<分类>/<数据集ID>/<年-月>/<日期>.csv"""
    return DATA_DIR / mod.CATEGORY / mod.NAME / date[:7] / f"{date}.csv"


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


RUNNERS = ("github", "server")
ANOMALY_RATIO = 0.5  # 行数低于前一次成功采集的一半，视为异常（可能是数据源改版、解析失效）


def previous_rows(name: str, before: str, key: str = "rows") -> int | None:
    """找该数据源在 before 日期之前最近一次成功采集的行数（key="fetched" 时为单次抓取行数）。"""
    for p in sorted(STATUS_DIR.glob("????-??-??*.json"), reverse=True):
        if p.name[:10] >= before:
            continue
        try:
            s = json.loads(p.read_text(encoding="utf-8")).get("sources", {}).get(name, {})
        except Exception:  # noqa: BLE001
            continue
        if s.get("ok") and s.get(key):
            return int(s[key])
    return None


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def merge_intraday(existing: list[dict], fetched: list[dict], key: tuple) -> tuple[list[dict], int]:
    """把本次抓到的行追加到当天已有的行后面；同一 KEY 的记录只保留最早采到的那条。"""
    seen = {tuple(str(r.get(k, "")) for k in key) for r in existing}
    new = []
    for r in fetched:
        k = tuple(str(r.get(f, "")) for f in key)
        if k not in seen:
            seen.add(k)
            new.append(r)
    return existing + new, len(new)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("only", nargs="*", help="只运行这些数据源")
    ap.add_argument("--force", action="store_true")
    ap.add_argument(
        "--intraday-only", action="store_true",
        help="只运行一天多次采集的数据源（INTRADAY = True），用于夜间等额外时点",
    )
    ap.add_argument(
        "--runner", default="github", choices=RUNNERS,
        help="在哪台机器上运行：github（GitHub Actions，海外）或 server（国内云服务器）",
    )
    args = ap.parse_args(argv)

    now = datetime.now(timezone.utc)
    run = Run(
        date=now.astimezone(CST).strftime("%Y-%m-%d"),
        fetched_at_utc=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    sources = discover_sources()
    # 未指定时只运行"启用的、且归这台机器采集的"数据源；ENABLED = False 的数据源可手动指定运行
    selected = args.only or sorted(
        n for n, m in sources.items()
        if getattr(m, "ENABLED", True) and getattr(m, "RUNNER", "github") == args.runner
        and (getattr(m, "INTRADAY", False) or not args.intraday_only)
    )
    session = make_session()

    # 每台机器写自己的状态文件，避免两台机器同时改同一个文件
    suffix = "" if args.runner == "github" else f".{args.runner}"
    status_path = STATUS_DIR / f"{run.date}{suffix}.json"
    status = {"date": run.date, "runner": args.runner, "sources": {}}
    if status_path.exists():  # 同一天多次运行（如只补采一个源）时保留其他源的记录
        status = json.loads(status_path.read_text(encoding="utf-8"))
    failed = 0
    for name in selected:
        mod = sources.get(name)
        if mod is None:
            print(f"[skip] 未知数据源: {name}")
            continue
        path = out_path(mod, run.date)
        intraday = getattr(mod, "INTRADAY", False)
        if path.exists() and not args.force and not intraday:
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
            fetched = len(rows)
            prev_entry = status["sources"].get(name, {})
            if intraday:
                existing = read_csv(path) if path.exists() and not args.force else []
                rows, added = merge_intraday(existing, rows, tuple(mod.KEY))
                if existing and not added:
                    # 没有新的监测时刻：不改文件、不改状态，避免无意义的提交
                    print(f"[same] {name}: 抓到 {fetched} 行，没有新记录")
                    continue
            write_csv(path, rows)
            status["sources"][name] = {
                "ok": True,
                "rows": len(rows),
                "seconds": round(time.time() - t0, 1),
                "fetched_at_utc": run.fetched_at_utc,
                "file": path.relative_to(DATA_DIR).as_posix(),
                "sha256": sha256(path),
            }
            if intraday:
                status["sources"][name].update(
                    fetched=fetched, added=added, runs=int(prev_entry.get("runs", 0)) + 1,
                )
                print(f"[ok]   {name}: 抓到 {fetched} 行，新增 {added} 行，当天累计 {len(rows)} 行 -> {path}")
            else:
                print(f"[ok]   {name}: {len(rows)} 行 -> {path}")
            # 异常检测：数据照常保存（如实存档），但让本次运行报错，GitHub 会发邮件提醒检查
            # 一天多次的数据源比较"单次抓取行数"，一天一次的比较"文件行数"
            if intraday:
                n, prev = fetched, prev_entry.get("fetched") or previous_rows(name, run.date, "fetched")
            else:
                n, prev = len(rows), previous_rows(name, run.date)
            if prev and n < int(prev) * ANOMALY_RATIO:
                warning = f"行数骤降：{n} 行，前一次为 {prev} 行，可能是数据源改版"
                status["sources"][name]["warning"] = warning
                failed += 1
                print(f"[warn] {name}: {warning}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            prev_entry = status["sources"].get(name, {})
            if getattr(mod, "INTRADAY", False) and prev_entry.get("ok"):
                # 当天早些时候已成功采到数据：保留那次的记录，只记下这次的失败
                prev_entry["last_error"] = f"{run.fetched_at_utc} {e!r}"[:500]
                print(f"[fail] {name}: {e!r}（当天已有数据，保留）")
                continue
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
