"""独立验证整条账本链：任何人下载本仓库后都可以运行。

检查三件事：
1. 每份账本里的 prev_ledger_sha256 等于前一份账本文件的实际 SHA-256（链没有断、没被改）
2. 账本中记录的每个数据文件，重算 SHA-256 与记录一致（数据没被改）
3. data/raw/ 下的每个数据文件都登记在账本里（没有未登记的"补造"文件）
4. 如有 .ots 时间戳文件，提示可用 `ots verify` 进一步核验

用法：python scripts/verify.py        退出码 0 表示全部通过
"""

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "ledger"
RAW = ROOT / "data" / "raw"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    errors, n_files, gaps = [], 0, []
    registered = set()
    ledgers = sorted(LEDGER.glob("????-??-??.json"))
    prev = None
    for lp in ledgers:
        entry = json.loads(lp.read_text(encoding="utf-8"))
        if entry.get("date") != lp.stem:
            errors.append(f"{lp.name}: date 字段与文件名不符")
        want_prev = sha256_file(prev) if prev else None
        if entry.get("prev_ledger_sha256") != want_prev:
            errors.append(f"{lp.name}: 哈希链断裂（prev_ledger_sha256 与前一份账本不符）")
        if prev and entry.get("prev_date") != prev.stem:
            errors.append(f"{lp.name}: prev_date 应为 {prev.stem}")
        if prev and entry.get("prev_date"):
            from datetime import date

            d0 = date.fromisoformat(entry["prev_date"])
            d1 = date.fromisoformat(entry["date"])
            if (d1 - d0).days > 1:
                gaps.append(f"{entry['prev_date']} → {entry['date']}")
        for f in entry.get("files", []):
            p = ROOT / f["path"]
            registered.add(p.resolve())
            n_files += 1
            if not p.exists():
                errors.append(f"{lp.name}: 缺少文件 {f['path']}")
            elif sha256_file(p) != f["sha256"]:
                errors.append(f"{lp.name}: 文件被改动 {f['path']}")
        prev = lp

    for p in RAW.glob("*/*/*.csv"):
        if p.resolve() not in registered:
            errors.append(f"未登记在账本中的数据文件: {p.relative_to(ROOT).as_posix()}")

    print(f"账本 {len(ledgers)} 份，数据文件 {n_files} 个")
    if ledgers:
        print(f"链首 {ledgers[0].stem}，链尾 {ledgers[-1].stem}，链尾哈希 {sha256_file(ledgers[-1])}")
    if gaps:
        print("断采区间（如实记录，未补造）：" + "；".join(gaps))
    ots = sorted(LEDGER.glob("*.json.ots"))
    if ots:
        print(f"有 {len(ots)} 个 OpenTimestamps 时间戳，可运行 `ots verify ledger/<日期>.json.ots` 核验")
    if errors:
        print("验证失败：")
        print("\n".join(f"  - {e}" for e in errors))
        return 1
    print("验证通过：哈希链完整，所有数据文件与账本一致。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
