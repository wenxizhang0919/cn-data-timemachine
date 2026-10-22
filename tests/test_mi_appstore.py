"""小米应用商店排行榜的测试（结构与 2026-10-22 在服务器上实测到的页面一致）。"""

import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sources import mi_appstore_rank as mi  # noqa: E402


def li(pkg, name, aid, cid, cname):
    return (f'<li>\n    <a href="/details?id={pkg}"><img data-src="https://x/a.png" alt="{name}" width="72" height="72"\n'
            f'      onclick="dtlClick({{pos_name: {aid}, category_id: {cid}}})"></a>\n'
            f'    <h5>\n      <a href="/details?id={pkg}" >{name}</a>\n    </h5>\n'
            f'    <p class="app-desc">\n      <a href="/category/{cid}">{cname}</a>\n    </p>\n  </li>')


def page(items, sidebar=True):
    side = '<ul class="side"><li class="cf"><a class="hd" href="/details?id=com.side">侧栏</a></li></ul>' if sidebar else ""
    nav = '<a href="/category/5">实用工具</a><a href="/category/19">网游RPG</a>'
    return f'<html>{nav}<ul class="applist">{"".join(items)}</ul>{side}</html>'


P1 = [li(f"com.a{i}", f"应用{i}", 1000 + i, 19 if i % 2 else 5, "网游RPG" if i % 2 else "实用工具") for i in range(30)]
P2 = [li(f"com.b{i}", f"应用B{i}", 2000 + i, 5, "实用工具") for i in range(5)]


def test_parse_page_ignores_sidebar():
    items = mi.parse_page(page(P1[:3]))
    assert [i["package"] for i in items] == ["com.a0", "com.a1", "com.a2"]
    assert items[1] == {"app_name": "应用1", "package": "com.a1", "app_id": "1001", "category_id": "19", "category_name": "网游RPG"}


def test_collect_paginates_until_repeat_and_adds_category_charts(monkeypatch):
    monkeypatch.setattr(mi, "SLEEP", 0)
    pages = {"/catTopList/0?page=1": page(P1), "/catTopList/0?page=2": page(P2), "/catTopList/0?page=3": page(P2)}
    calls = []

    def fake_fetch(session, path):
        calls.append(path)
        if path.startswith("/catTopList/0"):
            return pages[path]
        return page(P1[:2]) if path.endswith("page=1") else page(P1[:2])  # 分类榜第 2 页重复 -> 停

    monkeypatch.setattr(mi, "fetch", fake_fetch)
    rows = mi.collect(None, SimpleNamespace(date="2026-10-22"))
    total = [r for r in rows if r["chart"] == "0"]
    assert len(total) == 35 and total[-1]["rank"] == 35 and total[-1]["page"] == 2
    assert {r["chart"] for r in rows} == {"0", "5", "19"}
    cat5 = [r for r in rows if r["chart"] == "5"]
    assert [r["rank"] for r in cat5] == [1, 2] and cat5[0]["chart_name"] == "实用工具"
    assert set(mi.FIELDS) == set(rows[0])


def test_collect_fails_loudly_if_layout_changes(monkeypatch):
    monkeypatch.setattr(mi, "fetch", lambda s, p: "<html>改版了</html>")
    try:
        mi.collect(None, SimpleNamespace(date="2026-10-22"))
    except RuntimeError as e:
        assert "改版" in str(e)
    else:
        raise AssertionError
