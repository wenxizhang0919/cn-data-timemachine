"""香港停车场实时空位（每天一个固定时点的快照）。

来源：香港运输署开放数据 API（DATA.GOV.HK），只提供实时空位，不提供历史。
每天同一时刻存一次，可得到各停车场的日度占用面板。
"""

NAME = "hk_carpark_vacancy"
TITLE = "香港停车场实时空位"

URL = "https://api.data.gov.hk/v1/carpark-info-vacancy"


def collect(session, run) -> list[dict]:
    from collect import get_json

    vac = get_json(session, URL, params={"data": "vacancy", "lang": "zh_TW"})
    try:
        info = get_json(session, URL, params={"data": "info", "lang": "zh_TW"})
        names = {
            p.get("park_Id"): (p.get("name", ""), p.get("district", ""))
            for p in info.get("results", [])
        }
    except Exception:  # noqa: BLE001  名称只是补充信息，取不到也不影响空位数据
        names = {}

    rows = []
    for p in vac.get("results", []):
        pid = p.get("park_Id", "")
        name, district = names.get(pid, ("", ""))
        for vtype, items in p.items():
            if vtype == "park_Id" or not isinstance(items, list):
                continue
            for it in items:
                rows.append(
                    {
                        "park_id": pid,
                        "name": name,
                        "district": district,
                        "vehicle_type": vtype,
                        "vacancy_type": it.get("vacancy_type", ""),
                        "vacancy": it.get("vacancy", ""),
                        "vacancy_ev": it.get("vacancyEV", ""),
                        "vacancy_dis": it.get("vacancyDIS", ""),
                        "category": it.get("category", ""),
                        "last_update": it.get("lastupdate", ""),
                    }
                )
    return rows
