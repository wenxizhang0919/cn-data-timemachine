"""试跑一个数据源：只抓取并打印结果，不写任何文件。用于新数据源上线前在服务器上实测。

用法：python scripts/dry_run.py <数据源ID> [--limit N]
      --limit 只对支持的数据源生效（如中央气象台的两个数据集，只抓前 N 个城市）
"""

from __future__ import annotations

import argparse
import json
import os
import resource
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import collect  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()
    if args.limit:
        os.environ["TM_LIMIT"] = str(args.limit)
    mod = collect.discover_sources()[args.name]
    now = datetime.now(timezone.utc)
    run = collect.Run(date=now.astimezone(collect.CST).strftime("%Y-%m-%d"), fetched_at_utc=now.strftime("%Y-%m-%dT%H:%M:%SZ"))
    t = time.time()
    rows = mod.collect(collect.make_session(), run)
    secs = time.time() - t
    print(f"数据源 {args.name}：{len(rows)} 行，用时 {secs:.1f} 秒，"
          f"峰值内存 {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024:.0f} MB")
    if not rows:
        return 1
    fields = list(mod.FIELDS)
    print("缺少的字段：", [f for f in fields if f not in rows[0]] or "无")
    print("多出的字段：", [f for f in rows[0] if f not in fields] or "无")
    empty = {f: sum(1 for r in rows if r.get(f) in ("", None)) for f in fields}
    print("各字段空值比例：", {f: f"{n / len(rows):.0%}" for f, n in empty.items() if n})
    print("第一行：", json.dumps(rows[0], ensure_ascii=False))
    print("最后一行：", json.dumps(rows[-1], ensure_ascii=False))
    for f in fields[:3]:
        c = Counter(str(r.get(f, "")) for r in rows)
        print(f"{f} 不同取值 {len(c)} 个：", c.most_common(14))
    return 0


if __name__ == "__main__":
    sys.exit(main())
