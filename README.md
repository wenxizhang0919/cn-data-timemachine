# 每日数据时光机 · cn-data-timemachine

[![运行状态](https://github.com/wenxizhang0919/cn-data-timemachine/actions/workflows/health.yml/badge.svg)](STATUS.md) [![每日采集](https://github.com/wenxizhang0919/cn-data-timemachine/actions/workflows/daily.yml/badge.svg)](https://github.com/wenxizhang0919/cn-data-timemachine/actions/workflows/daily.yml)

**今天的数据到齐了吗？看 [STATUS.md](STATUS.md)**：每个数据集今天是否到齐、连续了多少天、有没有问题，随每次数据入库自动更新。

很多公开数据源只提供**"现在这一刻"**的数据：排行榜、价格、实时空位、最新一版预报……它们不保留历史，或者历史只能花大钱买。等到写论文、打比赛需要面板数据时，才发现过去的数据已经拿不到了。

这个仓库每天自动给这些数据源拍一张快照，**从 2026-10-21 开始一天接一天地存下来，并且让任何人都能验证这些记录没有被改过。**

代码谁都能写，但历史补不回来。启动日期就是资产。

## 四条原则

1. **连续**：从启动日起每天采集，一天不断。采集失败会自动报警；真断了的日期会如实留在账本里，不补造。
2. **可引用**：每个数据集有固定 ID、来源 URL、字段说明、采集时间、许可声明（见 [数据集目录](DATASETS.md)）。每一天都有版本标签 `snapshot-YYYY-MM-DD`，论文里可以写到具体某一天的版本。
3. **可复现**：采集脚本全部公开；原始快照 `data/raw/` 过了当天永不修改；以后的清洗数据单独放在另一层，不覆盖原始数据。任何人都能重跑。
4. **不替代原服务**：只做每日历史存档，供研究使用。不提供实时查询，不转售，不采集个人信息。

## 账本：借鉴区块链的"账本思想"，但不上链

一份存档最怕的不是没人看，而是别人不信：数据是不是事后改的？断采的日子有没有补造？口径变过没有？这里借用的是区块链背后的思想：只增不改、哈希链、时间戳、公开可验证。不涉及币，也不需要矿工。

| 思想 | 在这里的做法 |
|---|---|
| 只增不改 | `data/raw/` 下每个文件只在当天写入，之后永不修改；提交前由 [`scripts/check_immutable.py`](scripts/check_immutable.py) 自动拦截任何对历史文件的改动。修正只写入 changelog，不覆盖原文件。 |
| 哈希链 | 每天生成 `ledger/YYYY-MM-DD.json`，记录当天每个文件的 SHA-256、行数、字节数，**并包含前一天账本文件的 SHA-256**。一天扣一天，改动任何一天都会让后面的链断开。 |
| 时间戳 | 除了 Git 提交时间，每天的账本还提交给 [OpenTimestamps](https://opentimestamps.org/)（`ledger/*.json.ots`），几小时后锚定到比特币区块，证明这份账本在那个时间之前就已存在。 |
| 内容寻址 | 每份数据都有内容 ID：`数据集ID@日期#哈希前12位`，例如 `appstore_cn@2026-10-21#3f2a9c...`。同一份数据永远对应同一个 ID。 |
| 公开可验证 | 仓库、脚本、账本全部公开。任何人下载后运行 `python scripts/verify.py`，即可重算全部哈希并检查整条链。 |
| 分布式见证 | 欢迎 fork 本仓库，在你自己的 GitHub 上同时运行采集。多份独立记录的哈希值对得上，就证明数据在采集时没有造假。 |

验证方法：

```bash
git clone https://github.com/wenxizhang0919/cn-data-timemachine
cd cn-data-timemachine
python scripts/verify.py                      # 检查哈希链和所有数据文件
pip install opentimestamps-client
ots verify ledger/2026-10-21.json.ots         # 核验某天账本的公共时间戳
```

## 保险设施

连续性是这个存档的全部价值，所以每一种已知的失败方式都有对应的保险：

| 风险 | 保险 |
|---|---|
| GitHub 定时任务延迟或被丢弃 | 每天 4 次定时尝试（北京时间 10:17 / 13:37 / 17:07 / 20:37），先成功者采集，其余自动跳过 |
| 全天都没有触发，且没有任何提醒 | 两路互相独立的值守：① GitHub 每晚 22:47 / 23:17 / 23:47 健康检查（[`health.yml`](.github/workflows/health.yml)），发现问题先自动补跑，仍有问题就发邮件；② GitHub 之外的外部值守每晚 21:13 做同样检查，并通过 [`.github/kick`](.github/kick) 补触发、通知维护者 |
| 国内服务器停机、断网、卡死 | 服务器上每次运行最多 50 分钟，超时强制结束；水质等每小时数据超过 3 小时没有更新，健康检查即报警；服务器负责的数据会出现在 [STATUS.md](STATUS.md) 上 |
| GitHub 当天没能采到它负责的数据 | 国内服务器每晚 21:47 兜底：GitHub 负责的数据源若当天还没有文件，由服务器代采（状态里记为服务器采集） |
| 服务器磁盘写满 | 剩余空间低于 3 GB 时写入状态文件，健康检查报警 |
| 改服务器定时要登录服务器 | 定时任务写在仓库的 [`deploy/server/crontab`](deploy/server/crontab)，服务器每次运行自动同步（带安全检查，防止误删定时） |
| 单个数据源请求失败 | 自动重试；失败时整次运行标红，GitHub 发邮件提醒 |
| 数据源改版导致"采到了但数据不对" | 异常检测：行数低于前一次的一半即报警（数据照常如实保存，问题记入 CHANGELOG） |
| 改代码改坏了采集 | 每次推送代码自动运行测试和整链验证（[`tests.yml`](.github/workflows/tests.yml)） |
| 部分数据源拒绝海外机房访问 | 国内云服务器专门采集这些数据源（[`deploy/server/`](deploy/server/)），推送后自动并入当天账本 |
| GitHub 仓库或账号出问题 | 每周自动提交给 [Software Heritage](https://www.softwareheritage.org/) 永久存档（[`archive.yml`](.github/workflows/archive.yml)）；也欢迎 fork 作为分布式备份 |

手动补触发：在 GitHub 网页上编辑 `.github/kick`（改任意内容）并提交即可。

## 已收录的数据

数据按分类存放，每个数据集一个独立文件夹，点进去就有它自己的说明页。按分类分组的完整目录见 **[DATASETS.md](DATASETS.md)**（机器可读版本：[`datasets.json`](datasets.json)）。

| 分类 | 目录 |
|---|---|
| 应用与游戏 | [`data/raw/apps/`](data/raw/apps/) |
| 内容与媒体 | [`data/raw/media/`](data/raw/media/) |
| 人工智能 | [`data/raw/ai/`](data/raw/ai/) |
| 天气与环境 | [`data/raw/weather/`](data/raw/weather/) |
| 交通出行 | [`data/raw/transport/`](data/raw/transport/) |
| 房地产 | [`data/raw/real_estate/`](data/raw/real_estate/) |

| ID | 内容 | 许可 |
|---|---|---|
| `appstore_cn` | App Store 中国区：iPhone 免费/付费/畅销榜（总榜 + 全部 25 个分类）、iPad 三榜、Mac 免费榜、新上架榜，各前 100 名 | 🟢 Apple 官方公开 RSS |
| `appstore_global` | 全球 37 个国家/地区 App Store 免费榜、畅销榜、游戏免费榜、游戏畅销榜，可追踪中国应用出海 | 🟢 Apple 官方公开 RSS |
| `mi_appstore_rank` | 小米应用商店总榜与 17 个分类榜（每榜约前 108 名，含安卓包名），可与 App Store 对照研究国内 iOS / 安卓市场 | 🟡 小米应用商店网页（由国内服务器采集） |
| `apple_podcasts_cn` | Apple 播客中国区排行榜（总榜 + 18 个分类） | 🟢 Apple 官方公开 RSS |
| `huggingface_models` | Hugging Face 模型、数据集、Spaces 应用热度，及中国主要 AI 机构模型的下载量 | 🟢 Hugging Face 公开 API |
| `llm_api_prices` | OpenRouter 上全部大模型的 API 价格、上下文长度、免费与否 | 🟢 OpenRouter 公开 API |
| `steam_cn` | Steam 中国区畅销榜、热门新品榜，含价格、折扣、评测数、好评率 | 🟡 Steam 商店公开页面（由国内服务器采集） |
| `hk_weather_forecast` | 香港天文台九天预报（存下每天发布的预报，可研究预报准确率） | 🟢 香港天文台开放数据 |
| `hk_carpark_vacancy` | 香港约 430 个停车场实时空位（每日固定时点快照） | 🟢 香港运输署开放数据 |
| `bj_housing_daily` | 北京每日新房（期房、现房）与二手房网上认购、签约套数和面积，及可售、未签约库存 | 🟡 北京市住建委官网（由国内服务器采集） |
| `gz_housing_daily` | 广州 11 个区每日新建商品房签约、可售、未售的套数和面积（住宅/商业/办公/车位） | 🟡 广州市住建局官网（由国内服务器采集） |
| `cn_weather_hourly_obs` | 全国约 2500 个城市**逐小时**天气实况：气温、降水、湿度、气压、风向风速（每天存下过去 24 小时） | 🟡 中央气象台官网（由国内服务器采集） |
| `cn_city_weather_forecast` | 全国约 2500 个城市每天发布的 7 天预报，附城市 AQI 与生效中的气象预警，可研究预报准确率 | 🟡 中央气象台官网（由国内服务器采集） |
| `cn_surface_water_quality` | 全国约 1500 个地表水水质自动监测断面，**每小时**一个监测时刻：水温、pH、溶解氧、氨氮、总磷、总氮等 11 项指标与水质类别，含未修约原始值与质控说明 | 🟡 中国环境监测总站公开发布（由国内服务器每小时采集） |

## 目录结构

```
data/raw/<分类>/<数据集ID>/<年-月>/<日期>.csv   原始快照（UTF-8，Excel 可直接打开），过了当天永不修改
data/raw/<分类>/<数据集ID>/README.md           该数据集的说明：来源、许可、字段、覆盖天数、引用方式
data/raw/<分类>/README.md                      该分类下的数据集一览
data/raw/_status/<日期>.json                   每天的采集日志：行数、耗时、sha256、失败原因
ledger/<日期>.json                        当天账本（哈希链的一环）
ledger/<日期>.json.ots                    当天账本的 OpenTimestamps 时间戳证明
ledger/HEAD                               最新账本的日期和哈希
DATASETS.md / datasets.json               数据集目录（自动生成）
```

合并成面板数据（Python）：

```python
import pandas as pd, glob
df = pd.concat(pd.read_csv(f) for f in sorted(glob.glob("data/raw/apps/appstore_cn/*/*.csv")))
panel = df[df.chart_name == "iPhone 畅销榜"].pivot_table(index="date", columns="name", values="rank")
```

## 如何引用

> 数据来自「每日数据时光机」存档（cn-data-timemachine），数据集 `appstore_cn`，版本 snapshot-2026-10-21，https://github.com/wenxizhang0919/cn-data-timemachine

如需精确到文件，可附上账本中的内容 ID（如 `appstore_cn@2026-10-21#3f2a9c...`）。GitHub 页面右侧的 "Cite this repository" 也可以直接生成引用格式（见 [`CITATION.cff`](CITATION.cff)）。

## 收录原则

只收录"只公开当前/当天记录，不提供历史，或历史需要高价购买"的数据源。每个数据源标注授权等级：

- 🟢 **可发布**：官方开放接口，或明确允许再利用的开放数据平台
- 🟡 **注明来源发布**：未作声明的公开页面，遵守 robots.txt，每天只请求一次；权利人要求即下架
- 🔴 **不收录**：网站明确禁止下载使用，或 robots.txt 不允许抓取

只存档事实数据（排名、价格、数量等）。App、游戏、节目名称和商标归各自权利人。如果你是某个数据的权利人，希望下架，请开 [Issue](../../issues)。

## 运行与贡献

数据由 GitHub Actions 每天北京时间 10:17 左右自动采集并提交。本地运行：

```bash
pip install -r requirements.txt
python collect.py              # 采集全部数据源（写入当天文件）
python ledger.py               # 生成当天账本
python scripts/verify.py       # 验证整条链
```

新增数据源：在 `sources/` 下新建一个模块，提供 `NAME`、`CATEGORY`（见 [`sources/_categories.py`](sources/_categories.py)）、`TITLE`、`SOURCE_URL`、`LICENSE`、`FIELDS` 和 `collect(session, run)`，参考 [`sources/appstore_cn.py`](sources/appstore_cn.py)。欢迎在 Issue 里推荐"只有实时、没有历史"的数据源。

## 许可

代码以 [MIT](LICENSE) 许可发布。数据的权利归原始来源方，使用时请遵守各数据集标注的来源条款；本仓库只对汇编整理工作主张署名。
