"""根据各数据源的元数据和账本，生成数据集目录：DATASETS.md（给人看）和 datasets.json（给程序用）。

目录里每个数据集都有：固定 ID、中文名、来源 URL、许可说明、字段说明、
首个快照日期、最新快照日期、已存档天数、缺失天数。
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from collect import COMMON_FIELDS, REPO_URL, discover_sources

ROOT = Path(__file__).resolve().parent
LEDGER = ROOT / "ledger"


def coverage() -> dict:
    """从账本统计每个数据集有快照的日期。"""
    days: dict[str, list[str]] = {}
    for lp in sorted(LEDGER.glob("????-??-??.json")):
        entry = json.loads(lp.read_text(encoding="utf-8"))
        for f in entry.get("files", []):
            days.setdefault(f["dataset"], []).append(entry["date"])
    return days


def build() -> list[dict]:
    cov = coverage()
    out = []
    for name, mod in sorted(discover_sources().items()):
        ds = cov.get(name, [])
        span = (date.fromisoformat(ds[-1]) - date.fromisoformat(ds[0])).days + 1 if ds else 0
        out.append(
            {
                "id": name,
                "title": mod.TITLE,
                "enabled": getattr(mod, "ENABLED", True),
                "description": (mod.__doc__ or "").strip(),
                "source_url": mod.SOURCE_URL,
                "license": mod.LICENSE,
                "fields": {**mod.FIELDS, **COMMON_FIELDS},
                "path": f"data/raw/{name}/<YYYY-MM>/<YYYY-MM-DD>.csv",
                "first_snapshot": ds[0] if ds else None,
                "latest_snapshot": ds[-1] if ds else None,
                "days_archived": len(ds),
                "days_missing": span - len(ds),
            }
        )
    return out


def render_md(cat: list[dict]) -> str:
    lines = [
        "# 数据集目录",
        "",
        "> 本文件由 `make_catalog.py` 自动生成，请勿手改。机器可读版本见 [`datasets.json`](datasets.json)。",
        "",
        "| ID | 名称 | 首个快照 | 最新快照 | 已存档天数 | 缺失天数 |",
        "|---|---|---|---|---|---|",
    ]
    for d in cat:
        lines.append(
            f"| [`{d['id']}`](#{d['id']}) | {d['title']}{'' if d['enabled'] else '（暂停）'} | {d['first_snapshot'] or '—'} | "
            f"{d['latest_snapshot'] or '—'} | {d['days_archived']} | {d['days_missing']} |"
        )
    for d in cat:
        lines += [
            "",
            f"## {d['id']}",
            "",
            f"**{d['title']}**",
            "",
            d["description"],
            "",
            f"- 来源：<{d['source_url']}>" if "{" not in d["source_url"] else f"- 来源：`{d['source_url']}`",
            f"- 许可：{d['license']}",
            *([] if d["enabled"] else ["- 状态：**暂停采集**（原因见 CHANGELOG.md）"]),
            f"- 文件：`{d['path']}`",
            "",
            "| 字段 | 说明 |",
            "|---|---|",
        ]
        lines += [f"| `{k}` | {v} |" for k, v in d["fields"].items()]
        lines += [
            "",
            "引用示例：",
            "",
            f"> 数据来自「每日数据时光机」存档（cn-data-timemachine），数据集 `{d['id']}`，"
            f"版本 YYYY-MM-DD，{REPO_URL}",
        ]
    return "\n".join(lines) + "\n"


def main() -> None:
    cat = build()
    (ROOT / "datasets.json").write_text(
        json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (ROOT / "DATASETS.md").write_text(render_md(cat), encoding="utf-8")
    print(f"catalog: {len(cat)} 个数据集")


if __name__ == "__main__":
    main()
