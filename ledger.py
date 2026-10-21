"""每日账本：借鉴区块链的"账本思想"（只增不改、哈希链、公开可验证），但不上链。

每天采集完成后生成 ledger/YYYY-MM-DD.json，记录：
- 当天每个数据文件的 SHA-256、行数、字节数、内容 ID（数据集ID@日期#哈希前12位）
- 当天各数据源的采集状态（成功/失败/原因）
- 前一份账本文件的 SHA-256（prev_ledger_sha256）—— 一天扣一天，改动任何一天都会断链
- 生成这份账本时的代码版本（git commit）

账本文件本身的 SHA-256 就是"这一天的指纹"，由下一天的账本引用，
并用 OpenTimestamps 做公共时间戳（.ots 文件）。

用法：python ledger.py [YYYY-MM-DD]
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
LEDGER = ROOT / "ledger"
SCHEMA = "cn-data-timemachine/ledger/v1"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def count_rows(path: Path) -> int:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return max(sum(1 for _ in csv.reader(f)) - 1, 0)


def dump(obj) -> bytes:
    """规范化 JSON：键排序、固定缩进、UTF-8、末尾换行。任何人用同样规则都能复现同样字节。"""
    return (json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def ledger_files() -> list[Path]:
    return sorted(LEDGER.glob("????-??-??.json"))


def previous_ledger(date: str) -> Path | None:
    prev = [p for p in ledger_files() if p.stem < date]
    return prev[-1] if prev else None


def git_commit() -> str:
    sha = os.environ.get("GITHUB_SHA")
    if sha:
        return sha
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True, cwd=ROOT
        ).stdout.strip()
    except Exception:  # noqa: BLE001
        return ""


def build(date: str) -> dict:
    status_path = RAW / "_status" / f"{date}.json"
    status = json.loads(status_path.read_text(encoding="utf-8")) if status_path.exists() else {}

    files = []
    for path in sorted(RAW.glob(f"*/*/{date[:7]}/{date}.csv")):
        category, dataset = path.relative_to(RAW).parts[:2]
        digest = sha256_file(path)
        files.append(
            {
                "dataset": dataset,
                "category": category,
                "path": path.relative_to(ROOT).as_posix(),
                "sha256": digest,
                "bytes": path.stat().st_size,
                "rows": count_rows(path),
                "content_id": f"{dataset}@{date}#{digest[:12]}",
            }
        )

    sources = {}
    for name, s in sorted((status.get("sources") or {}).items()):
        sources[name] = {k: s[k] for k in ("ok", "rows", "fetched_at_utc", "error") if k in s}

    prev = previous_ledger(date)
    return {
        "schema": SCHEMA,
        "date": date,
        "prev_date": prev.stem if prev else None,
        "prev_ledger_sha256": sha256_file(prev) if prev else None,
        "files": files,
        "sources": sources,
        "code_commit": git_commit(),
        "created_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def write(date: str) -> Path:
    LEDGER.mkdir(exist_ok=True)
    entry = build(date)
    path = LEDGER / f"{date}.json"
    path.write_bytes(dump(entry))
    (LEDGER / "HEAD").write_text(f"{date} {sha256_file(path)}\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    from collect import CST

    d = sys.argv[1] if len(sys.argv) > 1 else datetime.now(CST).strftime("%Y-%m-%d")
    p = write(d)
    print(f"ledger: {p.relative_to(ROOT)} sha256={sha256_file(p)}")
