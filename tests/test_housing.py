"""北京、广州每日房产数据源的测试（结构与 2026-10-22 在服务器上实测到的页面一致）。"""

import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sources import bj_housing_daily as bj, gz_housing_daily as gz  # noqa: E402

RUN = SimpleNamespace(date="2026-10-22", fetched_at_utc="2026-10-22T02:47:00Z")


def kv_table(title, pairs):
    rows = "".join(f"<tr><td>{k}：</td><td>{v}</td></tr>" for k, v in pairs)
    return f"<table><tr><td colspan=2>{title}</td></tr>{rows}</table>"


BJ_HTML = (
    "<html><body>"
    "<table><tr><td>期房、现房网上签约数据统计</td></tr><tr><td>--&gt;&nbsp;&nbsp;</td></tr></table>"
    + kv_table("可售期房统计", [("可售房屋套数", "64090"), ("可售房屋面积(M<sup>2</sup>)", "5750792.0800"),
                                ("&nbsp;&nbsp;其中&nbsp;&nbsp;住宅套数", "29768"), ("面积(M 2 )", "4176314.2600")])
    + kv_table("2026 年9月预售许可", [("批准预售许可证", "19")])
    + kv_table("2026/10/21期房网上签约", [("网上签约套数", "136"), ("网上签约面积 (M 2 )", "12925.2600"),
                                         ("其中住宅套数", "120"), ("面积(M 2 )", "12683.1900")])
    + "<table><tr><td>存量房网上签约统计 </td></tr></table>"
    + kv_table("2026/10/21存量房网上签约", [("网上签约套数", "756"), ("网上签约面积(M 2 )", "68000.12")])
    + "<table><tr><td>区域</td><td>成交套数</td><td>成交面积(m 2 )</td></tr>"
      "<tr><td>朝阳</td><td>888</td><td>88499.17</td></tr><tr><td>海淀</td><td>559</td><td>37837.63</td></tr></table>"
    "</body></html>"
)


def test_bj_parse_long_format():
    rows = bj.parse(BJ_HTML)
    by = {(r["section"], r["item"]): r for r in rows}
    sign = by[("2026/10/21期房网上签约", "网上签约套数")]
    assert sign["value"] == "136" and sign["period"] == "2026-10-21" and sign["group"] == "期房、现房网上签约数据统计"
    assert by[("2026/10/21期房网上签约", "其中住宅套数·面积(m²)")]["value"] == "12683.1900"
    assert by[("2026 年9月预售许可", "批准预售许可证")]["period"] == "2026-09"
    stock = by[("可售期房统计", "可售房屋套数")]
    assert stock["period"] == "" and stock["value"] == "64090"
    resale = by[("2026/10/21存量房网上签约", "网上签约套数")]
    assert resale["group"] == "存量房网上签约统计" and resale["value"] == "756"
    assert by[("", "朝阳|成交套数")]["value"] == "888"
    assert set(bj.FIELDS) == set(rows[0])


def test_bj_collect_rejects_page_without_signing_data(monkeypatch):
    class S:
        def get(self, *a, **k):
            return SimpleNamespace(raise_for_status=lambda: None, text="<html>维护中</html>",
                                   apparent_encoding="utf-8", encoding="utf-8")

    monkeypatch.setattr("time.sleep", lambda s: None)
    try:
        bj.collect(S(), RUN)
    except RuntimeError as e:
        assert "网上签约" in str(e)
    else:
        raise AssertionError("应当报错")


GZ_ROW = {"sectionName": "越秀区", "createTime": "2026/10/21 0:00:00", "zhuZaiTaoShu": 1, "zhuZaiArea": 164.6102,
          "shangYeTaoShu": 0, "shangYeArea": 0.0, "banGongTaoShu": 0, "banGongArea": 0.0,
          "cheWeiTaoShu": 0, "cheWeiArea": 0.0}


def test_gz_collect_three_kinds(monkeypatch):
    calls = []

    class S:
        def post(self, url, headers=None, timeout=None):
            calls.append(url)
            extra = {"newField": 5} if "wsxx" in url else {}
            return SimpleNamespace(raise_for_status=lambda: None, json=lambda: {"data": [{**GZ_ROW, **extra}]})

    monkeypatch.setattr("time.sleep", lambda s: None)
    rows = gz.collect(S(), RUN)
    assert [r["kind"] for r in rows] == ["签约", "可售", "未售"]
    r = rows[0]
    assert r["district"] == "越秀区" and r["data_date"] == "2026-10-21" and r["residential_units"] == 1
    assert rows[2]["newField"] == 5  # 官网新增字段原样保留
    assert set(gz.FIELDS) <= set(r)
    assert len(calls) == 3
