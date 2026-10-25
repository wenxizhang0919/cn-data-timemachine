"""健康检查：今天的数据齐不齐、服务器还活着没、账本和时间戳连不连续。

用法：
    python scripts/health.py                    打印报告（总是退出码 0）
    python scripts/health.py --write STATUS.md  同时生成状态页
    python scripts/health.py --strict           有问题时退出码 1（给每晚的健康检查用，GitHub 会发邮件）
    python scripts/health.py --date 2026-10-22  检查指定日期

检查项：
1. 每个启用的数据源今天都有数据文件，并已登记进当天账本
2. 当天账本已生成、且与磁盘上的文件一致（没有"推送了但没登记"）
3. 采集状态里没有失败或"行数骤降"警告
4. 一天多次采集的数据源：最近 3 小时内有新数据（否则多半是服务器停了）
5. 国内服务器没有报告磁盘不足
6. 昨天的账本和时间戳都在（哈希链没有断）
7. 整条哈希链可验证
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import ledger  # noqa: E402
from collect import CST, discover_sources, out_path  # noqa: E402
from make_catalog import coverage  # noqa: E402
from sources._categories import CATEGORIES  # noqa: E402

DEADLINE_HOUR = 22  # 北京时间 22 点后仍缺数据才算"缺失"；之前算"等待采集"
INTRADAY_MAX_GAP_H = 3  # 一天多次的数据源超过 3 小时没有新数据视为异常
INTRADAY_ACTIVE_FROM_H = 3  # 凌晨数据少，3 点前不检查这一项
STRICT_LATE_UNTIL_H = 6  # --strict 在北京时间 6 点前运行时（定时被推迟），检查前一天
RUNNER_NAME = {"github": "GitHub", "server": "国内服务器"}


def parse_utc(s: str) -> datetime | None:
    try:
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except Exception:  # noqa: BLE001
        return None


def load_status(date: str) -> tuple[dict, dict]:
    """合并当天各机器的状态文件。返回 (数据源状态, 机器级警告)。"""
    merged, host = {}, {}
    for sp in sorted((ledger.RAW / "_status").glob(f"{date}*.json")):
        st = json.loads(sp.read_text(encoding="utf-8"))
        runner = st.get("runner") or "github"
        for name, s in (st.get("sources") or {}).items():
            prev = merged.get(name)
            if prev and prev.get("ok") and not s.get("ok"):
                continue  # 一台机器成功、另一台失败时，以成功的为准
            merged[name] = {**s, "runner": runner}
        if st.get("host_warning"):
            host[runner] = st["host_warning"]
    return merged, host


def streak(dates: list[str], until: str) -> int:
    """截至 until（含）连续有数据的天数。"""
    have, n = set(dates), 0
    d = datetime.strptime(until, "%Y-%m-%d").date()
    while d.isoformat() in have:
        n += 1
        d -= timedelta(days=1)
    return n


def check(date: str, now: datetime) -> dict:
    now_cst = now.astimezone(CST)
    is_today = now_cst.strftime("%Y-%m-%d") == date
    past_deadline = (not is_today) or now_cst.hour >= DEADLINE_HOUR
    problems: list[str] = []

    lp = ledger.LEDGER / f"{date}.json"
    led = json.loads(lp.read_text(encoding="utf-8")) if lp.exists() else None
    in_ledger = {f["dataset"] for f in (led or {}).get("files", [])}
    if led is None:
        if past_deadline:
            problems.append(f"{date} 的账本还没有生成")
    elif ledger.is_stale(date):
        problems.append(f"{date} 的账本与数据文件不一致（有数据推送后还没重新登记）")

    status, host = load_status(date)
    for runner, w in host.items():
        problems.append(f"{RUNNER_NAME.get(runner, runner)}：{w}")

    cov = coverage()
    rows = []
    for name, mod in sorted(discover_sources().items()):
        if not getattr(mod, "ENABLED", True):
            continue
        runner = getattr(mod, "RUNNER", "github")
        intraday = getattr(mod, "INTRADAY", False)
        st = status.get(name, {})
        has_file = out_path(mod, date).exists()
        issues = []
        if not has_file:
            if st and not st.get("ok"):
                issues.append(f"采集失败：{st.get('error', '')[:120]}")
            elif past_deadline:
                issues.append("今天没有数据")
        elif led is not None and name not in in_ledger:
            issues.append("有数据但未登记进账本")
        if st.get("warning"):
            issues.append(st["warning"])
        if intraday and not has_file and not issues and is_today and now_cst.hour >= INTRADAY_ACTIVE_FROM_H:
            issues.append(f"已到 {now_cst.hour} 点，今天还没有任何数据（服务器可能停了，或数据源停更）")
        if intraday and has_file and is_today and now_cst.hour >= INTRADAY_ACTIVE_FROM_H:
            last = parse_utc(st.get("fetched_at_utc", ""))
            if last is None or now - last > timedelta(hours=INTRADAY_MAX_GAP_H):
                ago = f"{(now - last).total_seconds() / 3600:.1f} 小时" if last else "未知时长"
                issues.append(f"已 {ago} 没有新数据（服务器可能停了，或数据源停更）")
        problems += [f"`{name}`：{i}" for i in issues]

        if has_file and not issues:
            state = "✅"
        elif not has_file and not issues:
            state = "⏳ 等待采集"
        else:
            state = "❌ " + "；".join(issues)
        dates = cov.get(name, [])
        extra = ""
        if intraday and st.get("runs"):
            extra = f"（今天 {st['runs']} 次有新数据，累计 {st.get('rows', 0)} 行）"
        rows.append(
            {
                "id": name,
                "title": mod.TITLE,
                "category": mod.CATEGORY,
                "runner": RUNNER_NAME.get(runner, runner) + ("·每小时" if intraday else ""),
                "state": state + extra,
                "streak": streak(dates, date) if has_file else streak(dates, prev_day(date)),
                "days": len(set(dates)),
                "first": dates[0] if dates else "—",
            }
        )

    # 连续性：昨天的账本和时间戳都要在
    yday = prev_day(date)
    first_ledger = ledger.ledger_files()[0].stem if ledger.ledger_files() else None
    if first_ledger and yday >= first_ledger:
        if not (ledger.LEDGER / f"{yday}.json").exists():
            problems.append(f"{yday} 的账本缺失，哈希链在这一天断开")
        elif not (ledger.LEDGER / f"{yday}.json.ots").exists():
            problems.append(f"{yday} 的账本没有 OpenTimestamps 时间戳")

    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "verify.py")], capture_output=True, text=True)
    if r.returncode != 0:
        tail = (r.stdout + r.stderr).strip().splitlines()[-3:]
        problems.append("哈希链验证失败：" + " / ".join(tail))

    return {"date": date, "checked_at": now_cst.strftime("%Y-%m-%d %H:%M"), "problems": problems, "rows": rows}


def prev_day(date: str) -> str:
    return (datetime.strptime(date, "%Y-%m-%d").date() - timedelta(days=1)).isoformat()


def render(rep: dict) -> str:
    ok = not rep["problems"]
    lines = [
        "<!-- 本文件由 scripts/health.py 自动生成，请勿手改 -->",
        "# 运行状态",
        "",
        f"**{'✅ 一切正常' if ok else '⚠️ 有 ' + str(len(rep['problems'])) + ' 个问题'}**"
        f" · 检查日期 {rep['date']} · 检查时间 {rep['checked_at']}（北京时间）",
        "",
    ]
    if not ok:
        lines += ["## 问题", "", *[f"- {p}" for p in rep["problems"]], ""]
    lines += [
        "## 各数据集",
        "",
        "| 数据集 | 名称 | 采集 | 今天 | 连续天数 | 已存档天数 | 开始日期 |",
        "|---|---|---|---|---|---|---|",
    ]
    order = list(CATEGORIES)
    for r in sorted(rep["rows"], key=lambda r: (order.index(r["category"]), r["id"])):
        lines.append(
            f"| `{r['id']}` | {r['title']} | {r['runner']} | {r['state']} | {r['streak']} | {r['days']} | {r['first']} |"
        )
    lines += [
        "",
        "## 怎么自查",
        "",
        "- 这一页随每次数据入库自动更新；每晚 22:47 和 23:17 还会做一次严格检查，发现问题会自动补跑，并给仓库主人发邮件。",
        "- 本地检查：`python scripts/health.py`；验证整条哈希链：`python scripts/verify.py`。",
        "- 历史上的缺失和修正记录见 [CHANGELOG.md](CHANGELOG.md)。",
    ]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date")
    ap.add_argument("--write")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args(argv)
    now = datetime.now(timezone.utc)
    date = args.date or now.astimezone(CST).strftime("%Y-%m-%d")
    if not args.date and args.strict and now.astimezone(CST).hour < STRICT_LATE_UNTIL_H:
        # GitHub 定时任务常被推迟到次日凌晨，此时应检查刚结束的那一天，而不是刚开始的新一天
        date = prev_day(date)
    rep = check(date, now)
    text = render(rep)
    if args.write:
        (ROOT / args.write).write_text(text, encoding="utf-8")
    print(text)
    return 1 if (args.strict and rep["problems"]) else 0


if __name__ == "__main__":
    sys.exit(main())
