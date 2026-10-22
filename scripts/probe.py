"""探测候选数据源：从本机（国内服务器）访问一批网址，打印状态、标题、关键词附近的内容和相关链接。
只读、不写文件，用于找新数据源。

用法：python scripts/probe.py [网址 ...]      不给网址时探测下面 CANDIDATES 里的全部
"""

from __future__ import annotations

import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import collect  # noqa: E402

KEYWORDS = ["成交", "网签", "签约", "套数", "客流", "客运量", "水位", "流量", "库容", "昨日", "今日"]

CANDIDATES = [
    # 房地产：每日网签/成交
    "http://bjjs.zjw.beijing.gov.cn/eportal/ui?pageId=307749",
    "http://bjjs.zjw.beijing.gov.cn/eportal/ui?pageId=307670",
    "https://zjw.beijing.gov.cn/",
    "https://zjj.sz.gov.cn/ris/szfdc/showcjgs/esfcjgs.aspx",
    "https://zjj.sz.gov.cn/ris/szfdc/showcjgs/ysfcjgs.aspx",
    "https://zjj.sz.gov.cn:8004/",
    "https://www.cdzjryb.com/SCXX/Default.aspx?action=ucEveryday",
    "http://zfcj.gz.gov.cn/",
    "https://fgj.hangzhou.gov.cn/",
    # 地铁客流
    "https://www.shmetro.com/",
    "https://www.gzmtr.com/",
    "https://www.szmc.net/",
    "https://www.bjsubway.com/",
    # 水利部 全国水雨情
    "http://xxfb.mwr.cn/sq_djdh.html",
    "http://xxfb.mwr.cn/sq_dxsk.html",
]


def probe(session, url: str) -> None:
    print("=" * 100)
    print(url)
    t = time.time()
    try:
        r = session.get(url, timeout=20, allow_redirects=True)
    except Exception as e:  # noqa: BLE001
        print(f"  失败：{e!r}"[:300])
        return
    r.encoding = r.apparent_encoding or r.encoding
    text = r.text
    title = re.search(r"<title[^>]*>(.*?)</title>", text, re.S | re.I)
    print(f"  {r.status_code} {time.time() - t:.1f}s {r.headers.get('content-type', '')} {len(r.content)}B -> {r.url}")
    print(f"  标题：{title.group(1).strip()[:80] if title else '-'}")
    if re.search(r"\$_ts|/[A-Za-z0-9]{12}/[A-Za-z0-9]{12}\.[0-9a-f]+\.js", text):
        print("  ⚠️ 疑似瑞数等反爬（动态脚本），不采")
    plain = re.sub(r"<script.*?</script>|<style.*?</style>", " ", text, flags=re.S | re.I)
    plain = re.sub(r"<[^>]+>", " ", plain)
    plain = re.sub(r"\s+", " ", plain)
    shown = 0
    for kw in KEYWORDS:
        for m in re.finditer(kw, plain):
            print(f"  …{plain[max(0, m.start() - 40): m.end() + 60]}…")
            shown += 1
            if shown >= 6:
                break
        if shown >= 6:
            break
    links = []
    for href, label in re.findall(r"""<a[^>]+href=["']([^"']+)["'][^>]*>(.*?)</a>""", text, re.S | re.I):
        label = re.sub(r"<[^>]+>|\s+", " ", label).strip()
        if any(k in label for k in KEYWORDS + ["数据", "统计", "公示", "水情", "实时"]):
            links.append(f"{label[:30]} -> {urljoin(r.url, href)}")
    for l in links[:12]:
        print(f"  链接：{l}")
    apis = sorted(set(re.findall(r"""["'](/[A-Za-z0-9_/.-]*(?:api|Api|ajax|Ajax|json|ashx|do)[A-Za-z0-9_/.?=&-]*)["']""", text)))
    for a in apis[:10]:
        print(f"  接口线索：{a}")


def main() -> int:
    s = collect.make_session()
    for url in sys.argv[1:] or CANDIDATES:
        probe(s, url)
        time.sleep(1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
