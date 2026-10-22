"""全国约 2500 个城市的逐小时天气实况（每天存一次过去 24 小时）。

来源：中央气象台官网（nmc.cn）各城市天气页。官网每个城市只显示"过去 24 小时"的逐小时实况，
更早的不再显示；成体系的历史逐小时站点数据需向气象部门申请或付费获取。
本数据集每天抓一次全部城市，把过去 24 小时的逐小时记录存下来，攒成"全国城市 × 小时"的面板。

说明：
- 每天由国内服务器在第一个成功的时点（通常 10:47）采集，文件里是采集时刻往前 24 小时的记录
  （例如 10:47 采集得到前一天 11:00 至当天 10:00）。相邻两天的文件可能有少量重叠小时
  （某天在较晚的时点才采集成功时），按 (city_code, obs_time) 去重即可。
- 官网用 9999 表示缺测，本存档存为空值。
- city_code 是官网的城市代码；官网若更换代码体系，可用 province + city 对齐。
"""

from sources import _nmc

NAME = "cn_weather_hourly_obs"
CATEGORY = "weather"
RUNNER = "server"
ENABLED = False  # 待在服务器上实测解析无误后启用
TITLE = "全国城市逐小时天气实况（中央气象台）"
SOURCE_URL = "https://www.nmc.cn/publish/forecast.html"
LICENSE = (
    "🟡 中央气象台官网公开显示的实况数据，官网未声明开放许可；"
    "本存档仅作非商业研究用途的历史保存，使用时请注明来源：中央气象台。"
)
FIELDS = {
    "city_code": "官网城市代码",
    "province": "省份",
    "city": "城市",
    "obs_time": "观测时刻（北京时间，YYYY-MM-DD HH:MM）",
    "temperature_c": "气温（℃）",
    "rain_1h_mm": "过去 1 小时降水量（mm）",
    "humidity_pct": "相对湿度（%）",
    "pressure_hpa": "气压（hPa）",
    "wind_direction_deg": "风向（度，0 为北风，顺时针）",
    "wind_speed_ms": "风速（m/s）",
}


def collect(session, run) -> list[dict]:
    res = _nmc.fetch_all(session, run)
    rows = []
    for c in res["cities"]:
        d = res["data"].get(c["code"])
        if not d:
            continue
        for h in d.get("passedchart") or []:
            rows.append(
                {
                    "city_code": c["code"],
                    "province": c["province"],
                    "city": c["city"],
                    "obs_time": h.get("time", ""),
                    "temperature_c": _nmc.val(h.get("temperature")),
                    "rain_1h_mm": _nmc.val(h.get("rain1h")),
                    "humidity_pct": _nmc.val(h.get("humidity")),
                    "pressure_hpa": _nmc.val(h.get("pressure")),
                    "wind_direction_deg": _nmc.val(h.get("windDirection")),
                    "wind_speed_ms": _nmc.val(h.get("windSpeed")),
                }
            )
    rows.sort(key=lambda r: (r["province"], r["city"], r["obs_time"]))
    return rows
