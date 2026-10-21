"""提交前检查"只增不改"：原始层 data/raw/ 和账本 ledger/ 只允许写"今天"的文件。

允许：
- 文件名含今天日期的文件（当天的数据、状态、账本）
- ledger/HEAD（指向最新账本）
- *.ots 时间戳文件（OpenTimestamps 升级证明时会更新，不影响数据）

用法（在 git add 之后运行）：python scripts/check_immutable.py [YYYY-MM-DD]
发现改动了历史文件就以非零状态退出，阻止提交。
"""

import subprocess
import sys
from datetime import datetime, timedelta, timezone


def violations(name_status: str, today: str) -> list[str]:
    bad = []
    for line in name_status.splitlines():
        status, *paths = line.split("\t")
        for p in paths:
            base = p.rsplit("/", 1)[-1]
            if p == "ledger/HEAD" or base.endswith(".ots") or today in base:
                continue
            bad.append(f"{status}\t{p}")
    return bad


def main() -> int:
    today = sys.argv[1] if len(sys.argv) > 1 else datetime.now(
        timezone(timedelta(hours=8))
    ).strftime("%Y-%m-%d")
    out = subprocess.run(
        ["git", "diff", "--cached", "--name-status", "--", "data/raw", "ledger"],
        capture_output=True, text=True, check=True,
    ).stdout
    bad = violations(out, today)
    if bad:
        print("拒绝提交：以下历史快照或账本被改动（只增不改，只允许写当天文件）：")
        print("\n".join(bad))
        return 1
    print(f"ok: 只改动了 {today} 的文件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
