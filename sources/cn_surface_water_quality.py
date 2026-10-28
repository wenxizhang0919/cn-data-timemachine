"""全国地表水水质自动监测站实时数据（每小时采集，逐个监测时刻存档）。

来源：中国环境监测总站「国家地表水水质自动监测实时数据发布系统」。
官网只滚动显示全国约 1500 个断面"最新一次"的监测值（多数断面每小时更新），
不提供历史查询或下载。本数据集由国内云服务器每小时抓取一次，
把每个断面每个监测时刻的数值都存下来，攒成全国断面 × 小时的面板数据。

说明：
- 官网注明"数据未经审核，仅供参考"，本存档如实保存发布值，不做任何修正或插补。
- 每个指标存两列：官网显示值（按发布规则修约）和 `_orig` 原始值（官网提示框里的
  "原始值"；与显示值相同时留空）。
- 官网显示"--"时，若提示框给出原因（如"当天质控不合格"），记录在 `notes` 列。
- 文件按采集日期（北京时间）划分；同一断面同一监测时刻只记一次，以第一次采到的为准。
  每天 0:27–22:27 每小时采集，23 点前后的监测值会在次日凌晨的采集中存入次日文件。
- 官网发布频率变化：2026-10-22 下午官网逐小时更新、约 1570 个断面；当晚起官网改为每天只发布
  0:00 一个时刻、约 975 个断面（2026-10-28 在官网页面核实）。本存档照常每小时检查一次，
  官网恢复逐小时发布时会自动存下每个时刻。
"""

import html
import re
import time

NAME = "cn_surface_water_quality"
CATEGORY = "weather"
RUNNER = "server"
INTRADAY = True  # 一天内多次采集，按 KEY 去重后追加到当天文件
# 健康检查里"多久没有新数据算服务器停了"：官网现在每天只更新一次，放宽到 26 小时
# （服务器停机仍可由一天一次的数据源到点缺失发现）
MAX_GAP_H = 26
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
}

# 测量指标列（有显示值/原始值/备注之分）
MEASURES = [
    "water_temp_c", "ph", "dissolved_oxygen_mg_l", "conductivity_us_cm", "turbidity_ntu",
    "permanganate_index_mg_l", "ammonia_nitrogen_mg_l", "total_phosphorus_mg_l",
    "total_nitrogen_mg_l", "chlorophyll_a_mg_l", "algae_density_cells_l",
]

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
}
for _m in MEASURES:
    FIELDS[f"{_m}_orig"] = f"{FIELDS[_m]}的原始值（未修约；与显示值相同时留空）"
FIELDS["notes"] = "官网提示框里的说明（如某指标\"当天质控不合格\"），多条用分号分隔"

_TAG = re.compile(r"<[^>]+>")
_TITLE = re.compile(r"""title\s*=\s*['"]([^'"]*)['"]""")


def clean(v) -> str:
    """去掉官网单元格里的 HTML 标签（提示框等），只留显示文字。"""
    if v is None:
        return ""
    s = html.unescape(_TAG.sub("", str(v))).strip()
    return "" if s in ("--", "&nbsp;") else s


def title_of(v) -> str:
    m = _TITLE.search(str(v or ""))
    return html.unescape(m.group(1)).strip() if m else ""


def station_name(v) -> str:
    """断面名称单元格可能是缩略显示，完整名称在 title 里。"""
    m = _TITLE.search(str(v or ""))
    return html.unescape(m.group(1)).strip() if m and m.group(1).strip() else clean(v)


def header_label(h: str) -> str:
    """'水温<br/><span class='unit'>(℃)</span>' -> '水温'"""
    return re.split(r"<br\s*/?>", str(h or ""))[0].strip() or clean(h)


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
    thead = j.get("thead") or []
    fields = [header_field(h, i) for i, h in enumerate(thead)]
    labels = [header_label(h) for h in thead]
    rows = []
    for cells in j.get("tbody") or []:
        row, notes = {}, []
        for i, v in enumerate(cells):
            f = fields[i] if i < len(fields) else f"extra_{i}"
            if f == "station":
                row[f] = station_name(v)
                continue
            row[f] = clean(v)
            if f in MEASURES or f.startswith("extra_"):
                t = title_of(v)
                m = re.match(r"^原始值[：:]\s*(.*)$", t)
                if m:
                    orig = m.group(1).strip()
                    row[f"{f}_orig"] = "" if orig == row[f] else orig
                elif t:
                    notes.append(f"{labels[i] if i < len(labels) else f}：{t}")
        row["notes"] = "；".join(notes)
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
