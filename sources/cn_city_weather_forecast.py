"""全国约 2500 个城市的 7 天天气预报（每天存一次当天发布的版本），附空气质量与预警。

来源：中央气象台官网（nmc.cn）各城市天气页。官网只显示最新一次发布的预报，旧预报被覆盖后不再可查。
每天存下当天的预报，就能研究"预报准不准、提前几天准、哪里最不准"，
并与 cn_weather_hourly_obs（实况）对照。

说明：
- 每个城市每天 7 行（预报日期 = 今天起 7 天）。publish_time 是官网标注的预报发布时间。
- aqi / aqi_text / aqi_time 是官网同时显示的城市空气质量（AQI）及其时间，每个城市当天各行相同。
- warning_* 是采集时该城市生效的气象预警（如有），每个城市当天各行相同；没有预警时为空。
- 官网用 9999 表示缺测/无，本存档存为空值。
"""

from sources import _nmc

NAME = "cn_city_weather_forecast"
CATEGORY = "weather"
RUNNER = "server"
TITLE = "全国城市 7 天天气预报存档（中央气象台）"
SOURCE_URL = "https://www.nmc.cn/publish/forecast.html"
LICENSE = (
    "🟡 中央气象台官网公开显示的预报数据，官网未声明开放许可；"
    "本存档仅作非商业研究用途的历史保存，使用时请注明来源：中央气象台。"
)
FIELDS = {
    "city_code": "官网城市代码",
    "province": "省份",
    "city": "城市",
    "publish_time": "预报发布时间（北京时间）",
    "forecast_date": "预报日期",
    "lead_days": "提前天数（0 = 当天）",
    "day_weather": "白天天气现象",
    "day_temp_c": "白天气温（最高，℃）",
    "day_wind_direction": "白天风向",
    "day_wind_power": "白天风力",
    "night_weather": "夜间天气现象",
    "night_temp_c": "夜间气温（最低，℃）",
    "night_wind_direction": "夜间风向",
    "night_wind_power": "夜间风力",
    "precipitation_mm": "预报降水量（mm）",
    "aqi": "城市空气质量指数 AQI",
    "aqi_text": "空气质量等级",
    "aqi_time": "AQI 对应时间",
    "warning_signal": "生效中的气象预警类型（如暴雨、大风）",
    "warning_level": "预警等级（蓝/黄/橙/红）",
    "warning_issue_time": "预警发布时间",
    "warning_content": "预警内容",
}


def _days_between(a: str, b: str) -> str:
    from datetime import date

    try:
        return str((date.fromisoformat(b) - date.fromisoformat(a)).days)
    except Exception:  # noqa: BLE001
        return ""


def collect(session, run) -> list[dict]:
    res = _nmc.fetch_all(session, run)
    rows = []
    v = _nmc.val
    for c in res["cities"]:
        d = res["data"].get(c["code"])
        if not d:
            continue
        pred = d.get("predict") or {}
        air = d.get("air") or {}
        warn = (d.get("real") or {}).get("warn") or {}
        extra = {
            "aqi": v(air.get("aqi")),
            "aqi_text": v(air.get("text")),
            "aqi_time": v(air.get("forecasttime")),
            "warning_signal": v(warn.get("signaltype")),
            "warning_level": v(warn.get("signallevel")),
            "warning_issue_time": v(warn.get("issuetime")),
            "warning_content": v(warn.get("issuecontent")),
        }
        for day in pred.get("detail") or []:
            dd, nn = day.get("day") or {}, day.get("night") or {}
            rows.append(
                {
                    "city_code": c["code"],
                    "province": c["province"],
                    "city": c["city"],
                    "publish_time": v(day.get("pt") or pred.get("publish_time")),
                    "forecast_date": day.get("date", ""),
                    "lead_days": _days_between(run.date, day.get("date", "")),
                    "day_weather": v((dd.get("weather") or {}).get("info")),
                    "day_temp_c": v((dd.get("weather") or {}).get("temperature")),
                    "day_wind_direction": v((dd.get("wind") or {}).get("direct")),
                    "day_wind_power": v((dd.get("wind") or {}).get("power")),
                    "night_weather": v((nn.get("weather") or {}).get("info")),
                    "night_temp_c": v((nn.get("weather") or {}).get("temperature")),
                    "night_wind_direction": v((nn.get("wind") or {}).get("direct")),
                    "night_wind_power": v((nn.get("wind") or {}).get("power")),
                    "precipitation_mm": v(day.get("precipitation")),
                    **extra,
                }
            )
    rows.sort(key=lambda r: (r["province"], r["city"], r["forecast_date"]))
    return rows
