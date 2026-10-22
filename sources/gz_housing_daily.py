"""广州市每日新建商品房签约、可售、未售情况（按行政区）。

来源：广州市住房和城乡建设局网站「商品房销售统计信息」页。页面每天只显示前一天的数据，
按行政区列出住宅、商业、办公、车位的签约套数与面积、可售套数与面积、未售套数与面积；
旧数据不保留，官方只另行发布月度汇总。每天存一次，即得广州各区新房成交与库存的日度面板。

说明：
- data_date 是官网标注的数据日期（通常是采集日的前一天）。
- kind：签约 = 当天网上签约（成交）；可售 = 纳入预售、可供销售的存量；未售 = 尚未售出的全部新建商品房。
- 面积单位：平方米。官网字段若新增，会以原始字段名追加保存。
"""

NAME = "gz_housing_daily"
CATEGORY = "real_estate"
RUNNER = "server"
TITLE = "广州新建商品房每日签约与库存（分区）"
SOURCE_URL = "https://zfcj.gz.gov.cn/zfcj/tjxx/spfxstjxx/"
LICENSE = (
    "🟡 广州市住房和城乡建设局网站公开数据，官网未声明开放许可；"
    "本存档仅作非商业研究用途的历史保存，使用时请注明来源：广州市住房和城乡建设局。"
)

BASE = "https://zfcj.gz.gov.cn/ysqgk/Api/WebApi/"
ENDPOINTS = {"签约": "mrxjspfqyxx.ashx", "可售": "mrxjspfksxx.ashx", "未售": "mrxjspfwsxx.ashx"}
KEYMAP = {
    "sectionName": "district",
    "createTime": "data_date",
    "zhuZaiTaoShu": "residential_units",
    "zhuZaiArea": "residential_area_m2",
    "shangYeTaoShu": "commercial_units",
    "shangYeArea": "commercial_area_m2",
    "banGongTaoShu": "office_units",
    "banGongArea": "office_area_m2",
    "cheWeiTaoShu": "parking_units",
    "cheWeiArea": "parking_area_m2",
}
FIELDS = {
    "kind": "类别：签约 / 可售 / 未售",
    "district": "行政区",
    "data_date": "官网标注的数据日期（YYYY-MM-DD）",
    "residential_units": "住宅套数",
    "residential_area_m2": "住宅面积（平方米）",
    "commercial_units": "商业套数",
    "commercial_area_m2": "商业面积（平方米）",
    "office_units": "办公套数",
    "office_area_m2": "办公面积（平方米）",
    "parking_units": "车位个数",
    "parking_area_m2": "车位面积（平方米）",
}


def norm_date(s: str) -> str:
    """'2026/10/21 0:00:00' -> '2026-10-21'"""
    import re

    m = re.match(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})", str(s or ""))
    return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}" if m else str(s or "")


def collect(session, run) -> list[dict]:
    import time

    rows = []
    for kind, ep in ENDPOINTS.items():
        last = None
        for i in range(3):
            try:
                r = session.post(BASE + ep, headers={"X-Requested-With": "XMLHttpRequest",
                                                     "Referer": SOURCE_URL}, timeout=30)
                r.raise_for_status()
                data = r.json().get("data")
                if not data:
                    raise RuntimeError("返回为空")
                break
            except Exception as e:  # noqa: BLE001
                last = e
                time.sleep(5 * (i + 1))
        else:
            raise RuntimeError(f"{kind} 接口失败：{last!r}")
        for d in data:
            row = {"kind": kind}
            for k, v in d.items():
                row[KEYMAP.get(k, k)] = norm_date(v) if k == "createTime" else v
            rows.append(row)
        time.sleep(1)
    return rows
