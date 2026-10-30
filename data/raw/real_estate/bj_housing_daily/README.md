<!-- 本文件由 make_catalog.py 自动生成，请勿手改 -->
# 北京新房与二手房每日网签及库存

- 数据集 ID：`bj_housing_daily`（固定不变）
- 分类：房地产（`real_estate`）
- 状态：采集中
- 来源：<http://bjjs.zjw.beijing.gov.cn/eportal/ui?pageId=307749>
- 许可：🟡 北京市住房和城乡建设委员会网站公开数据，官网未声明开放许可；本存档仅作非商业研究用途的历史保存，使用时请注明来源：北京市住房和城乡建设委员会。
- 覆盖：2026-10-22 至 2026-10-30，已存档 6 天，缺失 3 天
- 文件：`data/raw/real_estate/bj_housing_daily/<YYYY-MM>/<YYYY-MM-DD>.csv`，每天一个 CSV（UTF-8，Excel 可直接打开）
- 频率：每天采集一次（当天首次成功的那次）
- 采集机器：国内云服务器（阿里云 杭州）

## 说明

北京市每日新建商品房（期房、现房）与存量房（二手房）网上认购、签约，及可售/未签约库存。

来源：北京市住房和城乡建设委员会「房地产数据主题服务」页。页面每天只显示最近一天的
期房/现房网上认购与签约、存量房网上签约，以及当月预售许可、可售期房、未签约现房等库存数，
次日即被覆盖。每天存一次，即得北京新房、二手房成交与库存的日度时间序列。

存储格式（长表，适应官网改版）：
- 每个数字一行：section（表格标题，如"2026/10/21期房网上签约"）、period（从标题解析出的
  日期或月份；库存类表格无日期，为采集时点的存量）、item（指标名，如"网上签约套数"、
  "其中住宅套数·面积(m²)"）、value（数值原文）。
- group 是上一级栏目（如"期房、现房网上签约数据统计""存量房网上签约统计"）。
- 官网"面积"行紧跟在对应套数行后面，这里把它记为"上一指标·面积(m²)"，避免同名歧义。
- 多列表格（如"存量房网上签约月统计"按区域、按价格段的成交）记为 item = "行名|列名"；
  这类表格官网没有单独标题，section 为空，靠 group 识别，period 为空表示"官网当时展示的最近一期"。

## 字段

| 字段 | 说明 |
|---|---|
| `group` | 上一级栏目 |
| `section` | 表格标题（原文） |
| `period` | 数据所属日期（YYYY-MM-DD）或月份（YYYY-MM）；库存类为空，表示采集时点的存量 |
| `item` | 指标名 |
| `value` | 数值（原文） |
| `table_index` | 该表在页面中的序号（便于核对） |
| `date` | 采集日期（北京时间），即数据版本日期 |
| `fetched_at_utc` | 实际采集时刻（UTC） |

## 读取

```python
import pandas as pd, glob
df = pd.concat(pd.read_csv(f) for f in sorted(glob.glob("data/raw/real_estate/bj_housing_daily/*/*.csv")))
```

## 引用

> 数据来自「每日数据时光机」存档（cn-data-timemachine），数据集 `bj_housing_daily`，版本 snapshot-YYYY-MM-DD，https://github.com/wenxizhang0919/cn-data-timemachine

每天文件的 SHA-256 和内容 ID 见 `ledger/<日期>.json`，可用 `python scripts/verify.py` 独立验证。
