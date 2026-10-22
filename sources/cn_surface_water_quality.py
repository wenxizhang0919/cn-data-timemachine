"""全国地表水水质自动监测站实时数据（一天内多次采集，逐个监测时刻存档）。

来源：中国环境监测总站「国家地表水水质自动监测实时数据发布系统」。
官网只滚动显示每个断面"最新一次"的监测值（约每 4 小时一次），不提供历史查询或下载。
本数据集由国内云服务器一天多次抓取，把每个断面每个监测时刻的数值都存下来，
攒成全国断面 × 4 小时的面板数据。

说明：
- 官网注明"数据未经审核，仅供参考"，本存档如实保存原始发布值，不做任何修正。
- 每天一个文件，包含当天各次采集中出现的所有（断面, 监测时刻）记录；
  同一断面同一监测时刻只记一次（以第一次采到的为准）。
- 断面停运、维护时官网显示的空值或"--"原样保存，不做插补。
"""

import html
import re
import time

NAME = "cn_surface_water_quality"
CATEGORY = "weather"
RUNNER = "server"
# 接口格式已按官网脚本实现，待在服务器上实测通过后再启用，避免把解析错误的数据写进不可修改的历史
ENABLED = False
INTRADAY = True  # 一天内多次采集，按 KEY 去重后追加到当天文件
KEY = ("province", "basin", "station", "monitor_time")
TITLE = "全国地表水水质自动监测实时数据"
SOURCE_URL = "https://szzdjc.cnemc.cn:8070/GJZ/Business/Publish/Main.html"
LICENSE = (
    "🟡 中国环境监测总站公开发布的实时数据，官网未声明开放许可；"
    "本存档仅作非商业研究用途的历史保存，使用时请注明来源：中国环境监测总站。"
    "官网注明数据未经审核，仅供参考。"
)

API = "https://szzdjc.cnemc.cn:8070/GJZ/Ajax/Publish.ashx"

# 官网表头 -> 固定字段名。表头文字若改版变化，未识别的列会以 extra_<序号> 保存并在说明中提示。
HEADER_MAP = {
    "省份": "province",
    "流域": "basin",
    "断面名称": "station",
    "监测时间": "monitor_time_raw",
    "水质类别": "water_class_code",
    "水温": "water_temp_c",
    "pH": "ph",
    "溶解氧": "dissolved_oxygen_mg_l",
    "电导率": "conductivity_us_cm",
    "浊度": "turbidity_ntu",
    "高锰酸盐指数": "permanganate_index_mg_l",
    "氨氮": "ammonia_nitrogen_mg_l",
    "总磷": "total_phosphorus_mg_l",
    "总氮": "total_nitrogen_mg_l",
    "叶绿素": "chlorophyll_a_mg_l",
    "藻密度": "algae_density_cells_l",
    "站点情况": "station_status",
}

CLASS_NAMES = {"1": "Ⅰ", "2": "Ⅱ", "3": "Ⅲ", "4": "Ⅳ", "5": "Ⅴ", "6": "劣Ⅴ"}

FIELDS = {
    "province": "省份",
    "basin": "流域",
    "station": "断面名称",
    "monitor_time": "监测时刻（北京时间，YYYY-MM-DD HH:MM；官网只显示月-日，年份按采集日期推断）",
    "monitor_time_raw": "官网显示的监测时间原文",
    "water_class_code": "水质类别代码（1–6）",
    "water_class": "水质类别（Ⅰ、Ⅱ、Ⅲ、Ⅳ、Ⅴ、劣Ⅴ）",
    "water_temp_c": "水温（℃）",
    "ph": "pH（无量纲）",
    "dissolved_oxygen_mg_l": "溶解氧（mg/L）",
    "conductivity_us_cm": "电导率（μS/cm）",
    "turbidity_ntu": "浊度（NTU）",
    "permanganate_index_mg_l": "高锰酸盐指数（mg/L）",
    "ammonia_nitrogen_mg_l": "氨氮（mg/L）",
    "total_phosphorus_mg_l": "总磷（mg/L）",
    "total_nitrogen_mg_l": "总氮（mg/L）",
    "chlorophyll_a_mg_l": "叶绿素α（mg/L）",
    "algae_density_cells_l": "藻密度（cells/L）",
    "station_status": "站点情况（如维护、停运等说明）",
}

_TAG = re.compile(r"<[^>]+>")
_TITLE = re.compile(r"""title\s*=\s*['"]([^'"]*)['"]""")


def clean(v) -> str:
    """去掉官网单元格里的 HTML 标签（提示框等），只留显示文字。"""
    if v is None:
        return ""
    s = html.unescape(_TAG.sub("", str(v))).strip()
    return "" if s in ("--", "&nbsp;") else s


def station_name(v) -> str:
    """断面名称单元格可能是缩略显示，完整名称在 title 里。"""
    m = _TITLE.search(str(v or ""))
    return html.unescape(m.group(1)).strip() if m and m.group(1).strip() else clean(v)


def header_field(h: str, i: int) -> str:
    h = clean(h)
    for zh, en in HEADER_MAP.items():
        if h.startswith(zh):
            return en
    return f"extra_{i}"


def full_time(raw: str, run_date: str) -> str:
    """'10-22 12:00' -> '2026-10-22 12:00'。跨年时（采集在 1 月、数据是 12 月）年份减一。"""
    m = re.match(r"^\s*(?:(\d{4})-)?(\d{1,2})-(\d{1,2})\s+(\d{1,2}):(\d{2})", raw or "")
    if not m:
        return ""
    year = int(m.group(1) or run_date[:4])
    month, day = int(m.group(2)), int(m.group(3))
    if not m.group(1) and month > int(run_date[5:7]):
        year -= 1
    return f"{year:04d}-{month:02d}-{day:02d} {int(m.group(4)):02d}:{m.group(5)}"


def fetch(session, page_index: int, page_size: int) -> dict:
    data = {
        "AreaID": "",
        "RiverID": "",
        "MNName": "",
        "PageIndex": str(page_index),
        "PageSize": str(page_size),
        "action": "getRealDatas",
    }
    headers = {
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://szzdjc.cnemc.cn:8070/GJZ/Business/Publish/RealDatas.html",
        "Origin": "https://szzdjc.cnemc.cn:8070",
    }
    last = None
    for attempt in range(4):
        try:
            r = session.post(API, data=data, headers=headers, timeout=60)
            r.raise_for_status()
            j = r.json()
            if j == -1 or j == "-1":  # 官网的限流提示：请求过于频繁
                raise RuntimeError("被限流（请求过于频繁）")
            if not isinstance(j, dict) or not j.get("result"):
                raise RuntimeError(f"返回无数据: {str(j)[:200]}")
            return j
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(65 if "限流" in str(e) else 10 * (attempt + 1))
    raise last  # type: ignore[misc]


def parse(j: dict, run_date: str) -> list[dict]:
    fields = [header_field(h, i) for i, h in enumerate(j.get("thead") or [])]
    rows = []
    for cells in j.get("tbody") or []:
        row = {}
        for i, v in enumerate(cells):
            f = fields[i] if i < len(fields) else f"extra_{i}"
            row[f] = station_name(v) if f == "station" else clean(v)
        code = row.get("water_class_code", "")
        row["water_class"] = CLASS_NAMES.get(code, "")
        row["monitor_time"] = full_time(row.get("monitor_time_raw", ""), run_date)
        rows.append(row)
    return rows


def collect(session, run) -> list[dict]:
    # 官网"全国"视图的取法：PageIndex=-1 表示不分页，一次取回全部断面
    j = fetch(session, -1, 9999)
    rows = parse(j, run.date)
    total_pages = int(j.get("total") or 1)
    if total_pages > 1 and len(rows) < 1000:
        # 万一不分页取法失效，退回逐页取（官网自己每页间隔 20 秒，这里同样放慢）
        rows = []
        for p in range(1, total_pages + 1):
            rows += parse(fetch(session, p, 60), run.date)
            time.sleep(20)
    # 同一次返回里重复的记录只留一条
    seen, out = set(), []
    for r in rows:
        k = tuple(r.get(f, "") for f in KEY)
        if k not in seen and r.get("station"):
            seen.add(k)
            out.append(
                {f: r.get(f, "") for f in FIELDS} | {k2: v for k2, v in r.items() if k2.startswith("extra_")}
            )
    return out
