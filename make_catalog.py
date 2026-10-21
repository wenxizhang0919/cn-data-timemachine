"""生成数据集目录（全部自动生成，请勿手改）：

- DATASETS.md            总目录，按分类分组（给人看）
- datasets.json          总目录（给程序用）
- data/raw/<分类>/README.md            该分类下的数据集一览
- data/raw/<分类>/<数据集ID>/README.md  单个数据集的说明：来源、许可、字段、覆盖天数、引用方式

每个数据集都有：固定 ID、中文名、分类、来源 URL、许可说明、字段说明、
首个快照日期、最新快照日期、已存档天数、缺失天数。
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from collect import COMMON_FIELDS, REPO_URL, discover_sources
from sources._categories import CATEGORIES

ROOT = Path(__file__).resolve().parent
LEDGER = ROOT / "ledger"
RAW = ROOT / "data" / "raw"
HEADER = "<!-- 本文件由 make_catalog.py 自动生成，请勿手改 -->"


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
        cat = mod.CATEGORY
        out.append(
            {
                "id": name,
                "title": mod.TITLE,
                "category": cat,
                "category_name": CATEGORIES[cat][0],
                "enabled": getattr(mod, "ENABLED", True),
                "description": (mod.__doc__ or "").strip(),
                "source_url": mod.SOURCE_URL,
                "license": mod.LICENSE,
                "fields": {**mod.FIELDS, **COMMON_FIELDS},
                "path": f"data/raw/{cat}/{name}/<YYYY-MM>/<YYYY-MM-DD>.csv",
                "first_snapshot": ds[0] if ds else None,
                "latest_snapshot": ds[-1] if ds else None,
                "days_archived": len(ds),
                "days_missing": span - len(ds),
            }
        )
    order = list(CATEGORIES)
    out.sort(key=lambda d: (order.index(d["category"]), d["id"]))
    return out


def _status(d) -> str:
    return "采集中" if d["enabled"] else "暂停（见 CHANGELOG）"


def _row(d, link) -> str:
    return (
        f"| [`{d['id']}`]({link}) | {d['title']} | {d['first_snapshot'] or '—'} | "
        f"{d['latest_snapshot'] or '—'} | {d['days_archived']} | {d['days_missing']} | {_status(d)} |"
    )


TABLE_HEAD = [
    "| ID | 名称 | 首个快照 | 最新快照 | 已存档天数 | 缺失天数 | 状态 |",
    "|---|---|---|---|---|---|---|",
]


def render_dataset(d) -> str:
    src = f"<{d['source_url']}>" if "{" not in d["source_url"] else f"`{d['source_url']}`"
    lines = [
        HEADER,
        f"# {d['title']}",
        "",
        f"- 数据集 ID：`{d['id']}`（固定不变）",
        f"- 分类：{d['category_name']}（`{d['category']}`）",
        f"- 状态：{_status(d)}",
        f"- 来源：{src}",
        f"- 许可：{d['license']}",
        f"- 覆盖：{d['first_snapshot'] or '—'} 至 {d['latest_snapshot'] or '—'}，"
        f"已存档 {d['days_archived']} 天，缺失 {d['days_missing']} 天",
        f"- 文件：`{d['path']}`，每天一个 CSV（UTF-8，Excel 可直接打开）",
        "",
        "## 说明",
        "",
        d["description"],
        "",
        "## 字段",
        "",
        "| 字段 | 说明 |",
        "|---|---|",
        *[f"| `{k}` | {v} |" for k, v in d["fields"].items()],
        "",
        "## 读取",
        "",
        "```python",
        "import pandas as pd, glob",
        f'df = pd.concat(pd.read_csv(f) for f in sorted(glob.glob("data/raw/{d["category"]}/{d["id"]}/*/*.csv")))',
        "```",
        "",
        "## 引用",
        "",
        f"> 数据来自「每日数据时光机」存档（cn-data-timemachine），数据集 `{d['id']}`，"
        f"版本 snapshot-YYYY-MM-DD，{REPO_URL}",
        "",
        "每天文件的 SHA-256 和内容 ID 见 `ledger/<日期>.json`，可用 `python scripts/verify.py` 独立验证。",
    ]
    return "\n".join(lines) + "\n"


def render_category(cat, items) -> str:
    name, desc = CATEGORIES[cat]
    lines = [HEADER, f"# {name}", "", desc, "", *TABLE_HEAD]
    lines += [_row(d, f"{d['id']}/") for d in items]
    return "\n".join(lines) + "\n"


def render_md(cat: list[dict]) -> str:
    lines = [
        HEADER,
        "# 数据集目录",
        "",
        "按分类分组。每个数据集在 `data/raw/<分类>/<数据集ID>/` 下有独立文件夹和说明页。"
        "机器可读版本见 [`datasets.json`](datasets.json)。",
    ]
    for c, (cname, cdesc) in CATEGORIES.items():
        items = [d for d in cat if d["category"] == c]
        if not items:
            continue
        lines += ["", f"## {cname}（`{c}`）", "", cdesc, "", *TABLE_HEAD]
        lines += [_row(d, f"data/raw/{c}/{d['id']}/") for d in items]
    return "\n".join(lines) + "\n"


def main() -> None:
    cat = build()
    (ROOT / "datasets.json").write_text(
        json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (ROOT / "DATASETS.md").write_text(render_md(cat), encoding="utf-8")
    for c in CATEGORIES:
        items = [d for d in cat if d["category"] == c]
        if not items:
            continue
        (RAW / c).mkdir(parents=True, exist_ok=True)
        (RAW / c / "README.md").write_text(render_category(c, items), encoding="utf-8")
        for d in items:
            (RAW / c / d["id"]).mkdir(parents=True, exist_ok=True)
            (RAW / c / d["id"] / "README.md").write_text(render_dataset(d), encoding="utf-8")
    print(f"catalog: {len(cat)} 个数据集，{len({d['category'] for d in cat})} 个分类")


if __name__ == "__main__":
    main()
