"""北京市每日新建商品房（期房、现房）与存量房（二手房）网上认购、签约，及可售/未签约库存。

来源：北京市住房和城乡建设委员会「房地产数据主题服务」页。页面每天只显示最近一天的
期房/现房网上认购与签约、存量房网上签约，以及当月预售许可、可售期房、未签约现房等库存数，
次日即被覆盖。每天存一次，即得北京新房、二手房成交与库存的日度时间序列。

存储格式（长表，适应官网改版）：
- 每个数字一行：section（表格标题，如"2026/10/21期房网上签约"）、period（从标题解析出的
  日期或月份；库存类表格无日期，为采集时点的存量）、item（指标名，如"网上签约套数"、
  "其中住宅套数·面积(m²)"）、value（数值原文）。
- group 是上一级栏目（如"期房、现房网上签约数据统计""存量房网上签约统计"）。
- 官网"面积"行紧跟在对应套数行后面，这里把它记为"上一指标·面积(m²)"，避免同名歧义。
- 多列表格（如"存量房网上签约月统计"按区域、按价格段的成交）记为 item = "行名|列名"；
  这类表格官网没有单独标题，section 为空，靠 group 识别，period 为空表示"官网当时展示的最近一期"。
"""

import re

NAME = "bj_housing_daily"
CATEGORY = "real_estate"
RUNNER = "server"
TITLE = "北京新房与二手房每日网签及库存"
SOURCE_URL = "http://bjjs.zjw.beijing.gov.cn/eportal/ui?pageId=307749"
LICENSE = (
    "🟡 北京市住房和城乡建设委员会网站公开数据，官网未声明开放许可；"
    "本存档仅作非商业研究用途的历史保存，使用时请注明来源：北京市住房和城乡建设委员会。"
)
FIELDS = {
    "group": "上一级栏目",
    "section": "表格标题（原文）",
    "period": "数据所属日期（YYYY-MM-DD）或月份（YYYY-MM）；库存类为空，表示采集时点的存量",
    "item": "指标名",
    "value": "数值（原文）",
    "table_index": "该表在页面中的序号（便于核对）",
}

_TAG = re.compile(r"<[^>]+>")


def cell_text(s: str) -> str:
    s = _TAG.sub("", s).replace("&nbsp;", " ")
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"\(\s*[Mm]\s*2\s*\)", "(m²)", s)  # 面积(M 2 ) / 面积(M<sup>2</sup>) -> 面积(m²)
    s = re.sub(r"\s+\(", "(", s)
    return s.rstrip("：:").strip()


def parse_period(title: str) -> str:
    m = re.search(r"(\d{4})\s*[/-]\s*(\d{1,2})\s*[/-]\s*(\d{1,2})", title)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    m = re.search(r"(\d{4})\s*年\s*(\d{1,2})\s*月", title)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}"
    return ""


def is_number(s: str) -> bool:
    return bool(re.fullmatch(r"-?[\d,]+(\.\d+)?%?", s.strip()))


def parse(html: str) -> list[dict]:
    rows, group = [], ""
    tables = re.findall(r"<table.*?</table>", html, re.S | re.I)
    for ti, table in enumerate(tables):
        trs = [
            [cell_text(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S | re.I)]
            for tr in re.findall(r"<tr.*?</tr>", table, re.S | re.I)
        ]
        trs = [[c for c in tr] for tr in trs if any(tr)]
        if not trs:
            continue
        # 只有标题、没有数据的表：是上一级栏目名
        if all(len([c for c in tr if c]) <= 1 for tr in trs) and not any(is_number(c) for tr in trs for c in tr):
            title = next((c for tr in trs for c in tr if c and not c.startswith("-->")), "")
            if title:
                group = title
            continue
        section = trs[0][0] if len([c for c in trs[0] if c]) == 1 else ""
        body = trs[1:] if section else trs
        period = parse_period(section)
        prev_item = ""
        header = None
        for tr in body:
            cells = [c for c in tr]
            nonempty = [c for c in cells if c]
            if len(nonempty) == 2 and not is_number(nonempty[0]) and is_number(nonempty[1]):
                label, value = nonempty
                item = f"{prev_item}·{label}" if label.startswith("面积") and prev_item else label
                if not label.startswith("面积"):
                    prev_item = label
                rows.append({"group": group, "section": section, "period": period, "item": item,
                             "value": value.replace(",", ""), "table_index": ti})
            elif len(nonempty) >= 3 and not any(is_number(c) for c in nonempty[1:]):
                header = cells  # 多列表的表头
            elif header and len(cells) >= 2 and any(is_number(c) for c in cells[1:]):
                rowlabel = cells[0]
                for h, v in zip(header[1:], cells[1:]):
                    if is_number(v):
                        rows.append({"group": group, "section": section, "period": period,
                                     "item": f"{rowlabel}|{h}", "value": v.replace(",", ""), "table_index": ti})
            elif len(cells) >= 2 and not header and any(is_number(c) for c in cells[1:]):
                # 无表头的横向数据行：按"行名|列序号"保存
                for k, v in enumerate(cells[1:], 1):
                    if is_number(v):
                        rows.append({"group": group, "section": section, "period": period,
                                     "item": f"{cells[0]}|{k}", "value": v.replace(",", ""), "table_index": ti})
    return rows


def collect(session, run) -> list[dict]:
    import time

    last = None
    for i in range(4):
        try:
            r = session.get(SOURCE_URL, timeout=40)
            r.raise_for_status()
            r.encoding = r.apparent_encoding or "utf-8"
            rows = parse(r.text)
            if not any("网上签约" in x["section"] for x in rows):
                raise RuntimeError("页面里没有找到网上签约数据（可能改版）")
            return rows
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(10 * (i + 1))
    raise last  # type: ignore[misc]
