"""香港天文台九天天气预报。

来源：香港天文台开放数据 API（DATA.GOV.HK）。接口只提供"最新一版"预报，
过去发布过的预报不存档。每天存一次，就能研究预报准确率、预报修正等。
"""

NAME = "hk_weather_forecast"
TITLE = "香港天文台九天预报"
SOURCE_URL = 'https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=fnd'
LICENSE = '🟢 香港天文台开放数据（DATA.GOV.HK 使用条款），来源：香港天文台。'
FIELDS = {
    'issued_at': '预报发布时间',
    'lead_day': '提前天数（1=明天）',
    'forecast_date': '被预报的日期',
    'week': '星期',
    'max_temp_c': '预报最高气温（℃）',
    'min_temp_c': '预报最低气温（℃）',
    'max_rh_pct': '预报最高相对湿度（%）',
    'min_rh_pct': '预报最低相对湿度（%）',
    'weather': '天气描述',
    'wind': '风力风向描述',
    'icon': '天气图标代码',
    'psr': '显著降雨概率等级',
    'general_situation': '天气概况',
}

URL = "https://data.weather.gov.hk/weatherAPI/opendata/weather.php"


def _v(d, key):
    x = d.get(key) or {}
    return x.get("value", "") if isinstance(x, dict) else x


def collect(session, run) -> list[dict]:
    from collect import get_json

    data = get_json(session, URL, params={"dataType": "fnd", "lang": "tc"})
    issued = data.get("updateTime", "")
    situation = data.get("generalSituation", "")
    rows = []
    for lead, f in enumerate(data.get("weatherForecast", []), start=1):
        rows.append(
            {
                "issued_at": issued,
                "lead_day": lead,
                "forecast_date": f.get("forecastDate", ""),
                "week": f.get("week", ""),
                "max_temp_c": _v(f, "forecastMaxtemp"),
                "min_temp_c": _v(f, "forecastMintemp"),
                "max_rh_pct": _v(f, "forecastMaxrh"),
                "min_rh_pct": _v(f, "forecastMinrh"),
                "weather": f.get("forecastWeather", ""),
                "wind": f.get("forecastWind", ""),
                "icon": f.get("ForecastIcon", ""),
                "psr": f.get("PSR", ""),  # 降雨概率等级
                "general_situation": situation,
            }
        )
    return rows
