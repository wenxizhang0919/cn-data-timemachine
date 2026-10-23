<!-- 本文件由 make_catalog.py 自动生成，请勿手改 -->
# 广州新建商品房每日签约与库存（分区）

- 数据集 ID：`gz_housing_daily`（固定不变）
- 分类：房地产（`real_estate`）
- 状态：采集中
- 来源：<https://zfcj.gz.gov.cn/zfcj/tjxx/spfxstjxx/>
- 许可：🟡 广州市住房和城乡建设局网站公开数据，官网未声明开放许可；本存档仅作非商业研究用途的历史保存，使用时请注明来源：广州市住房和城乡建设局。
- 覆盖：2026-10-22 至 2026-10-23，已存档 2 天，缺失 0 天
- 文件：`data/raw/real_estate/gz_housing_daily/<YYYY-MM>/<YYYY-MM-DD>.csv`，每天一个 CSV（UTF-8，Excel 可直接打开）
- 频率：每天采集一次（当天首次成功的那次）
- 采集机器：国内云服务器（阿里云 杭州）

## 说明

广州市每日新建商品房签约、可售、未售情况（按行政区）。

来源：广州市住房和城乡建设局网站「商品房销售统计信息」页。页面每天只显示前一天的数据，
按行政区列出住宅、商业、办公、车位的签约套数与面积、可售套数与面积、未售套数与面积；
旧数据不保留，官方只另行发布月度汇总。每天存一次，即得广州各区新房成交与库存的日度面板。

说明：
- data_date 是官网标注的数据日期（通常是采集日的前一天）。
- kind：签约 = 当天网上签约（成交）；可售 = 纳入预售、可供销售的存量；未售 = 尚未售出的全部新建商品房。
- 面积单位：平方米。官网字段若新增，会以原始字段名追加保存。

## 字段

| 字段 | 说明 |
|---|---|
| `kind` | 类别：签约 / 可售 / 未售 |
| `district` | 行政区 |
| `data_date` | 官网标注的数据日期（YYYY-MM-DD） |
| `residential_units` | 住宅套数 |
| `residential_area_m2` | 住宅面积（平方米） |
| `commercial_units` | 商业套数 |
| `commercial_area_m2` | 商业面积（平方米） |
| `office_units` | 办公套数 |
| `office_area_m2` | 办公面积（平方米） |
| `parking_units` | 车位个数 |
| `parking_area_m2` | 车位面积（平方米） |
| `date` | 采集日期（北京时间），即数据版本日期 |
| `fetched_at_utc` | 实际采集时刻（UTC） |

## 读取

```python
import pandas as pd, glob
df = pd.concat(pd.read_csv(f) for f in sorted(glob.glob("data/raw/real_estate/gz_housing_daily/*/*.csv")))
```

## 引用

> 数据来自「每日数据时光机」存档（cn-data-timemachine），数据集 `gz_housing_daily`，版本 snapshot-YYYY-MM-DD，https://github.com/wenxizhang0919/cn-data-timemachine

每天文件的 SHA-256 和内容 ID 见 `ledger/<日期>.json`，可用 `python scripts/verify.py` 独立验证。
