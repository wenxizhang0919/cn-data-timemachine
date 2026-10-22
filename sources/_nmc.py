"""中央气象台（nmc.cn）城市天气接口的共用抓取逻辑。

一次请求返回一个城市的：过去 24 小时逐小时实况、未来 7 天预报、空气质量等。
多个数据集（逐小时实况、7 天预报）共用同一批请求：同一次运行里只抓一遍，结果缓存在内存里。

省内存（服务器只有 2G）：每个城市的返回只保留各数据集用到的几个字段（雷达图、气候统计等丢弃），
2500 个城市缓存约 20–30 MB。
"""

from __future__ import annotations

import time

BASE = "https://www.nmc.cn"
HEADERS = {"Referer": "https://www.nmc.cn/", "X-Requested-With": "XMLHttpRequest"}
SLEEP = 0.25  # 每个请求之间的间隔（秒），2500 个城市约 15–20 分钟，对网站压力很小
MAX_FAIL_RATIO = 0.2  # 失败城市超过 20% 视为本次采集失败（不保存，留给下一个时点重试）
MISSING = 9999  # 官网用 9999 表示缺测

_cache: dict = {}


def get(session, path: str, retries: int = 3):
    last = None
    for i in range(retries):
        try:
            r = session.get(BASE + path, headers=HEADERS, timeout=30)
            r.raise_for_status()
            return r.json()
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(3 * (i + 1))
    raise last  # type: ignore[misc]


def cities(session) -> list[dict]:
    out = []
    for p in get(session, "/rest/province/all"):
        for c in get(session, f"/rest/province/{p['code']}"):
            out.append({"code": c.get("code", ""), "province": c.get("province") or p.get("name", ""), "city": c.get("city", "")})
        time.sleep(SLEEP)
    return out


def fetch_all(session, run, limit: int | None = None) -> dict:
    """返回 {"cities": [...], "data": {code: data}, "failed": [...]}；同一天同一进程只抓一次。"""
    key = (run.date, limit)
    if key in _cache:
        return _cache[key]
    cs = cities(session)
    if limit:
        cs = cs[:limit]
    data, failed = {}, []
    for c in cs:
        try:
            j = get(session, f"/rest/weather?stationid={c['code']}", retries=2)
            if j.get("code") != 0 or not j.get("data"):
                raise RuntimeError(j.get("msg") or "无数据")
            data[c["code"]] = slim(j["data"])
        except Exception:  # noqa: BLE001
            failed.append(c["code"])
        time.sleep(SLEEP)
    if not cs or len(failed) > len(cs) * MAX_FAIL_RATIO:
        raise RuntimeError(f"{len(failed)}/{len(cs)} 个城市抓取失败，放弃本次采集")
    res = {"cities": cs, "data": data, "failed": failed}
    _cache[key] = res
    return res


def slim(d: dict) -> dict:
    """只留数据集用到的部分，其余（雷达图、气候、图片等）丢弃以节省内存。"""
    real = d.get("real") or {}
    return {
        "passedchart": d.get("passedchart") or [],
        "predict": d.get("predict") or {},
        "air": d.get("air") or {},
        "real": {"warn": real.get("warn") or {}},
    }


def val(v):
    """9999 / 空 -> 空字符串；其余原样。"""
    if v is None or v == "" or v == MISSING or v == str(MISSING):
        return ""
    return v
