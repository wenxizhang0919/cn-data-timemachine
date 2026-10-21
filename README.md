# 每日数据时光机 · cn-data-timemachine

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

## 已收录的数据

完整字段说明和每个数据集的覆盖天数，见自动生成的 **[数据集目录](DATASETS.md)**（机器可读版本：[`datasets.json`](datasets.json)）。

| ID | 内容 | 许可 |
|---|---|---|
| `appstore_cn` | App Store 中国区：iPhone 免费/付费/畅销榜（总榜 + 全部 25 个分类）、iPad 三榜、Mac 免费榜、新上架榜，各前 100 名 | 🟢 Apple 官方公开 RSS |
| `appstore_global` | 全球 37 个国家/地区 App Store 免费榜、畅销榜、游戏免费榜、游戏畅销榜，可追踪中国应用出海 | 🟢 Apple 官方公开 RSS |
| `apple_podcasts_cn` | Apple 播客中国区排行榜（总榜 + 18 个分类） | 🟢 Apple 官方公开 RSS |
| `huggingface_models` | Hugging Face 模型、数据集、Spaces 应用热度，及中国主要 AI 机构模型的下载量 | 🟢 Hugging Face 公开 API |
| `llm_api_prices` | OpenRouter 上全部大模型的 API 价格、上下文长度、免费与否 | 🟢 OpenRouter 公开 API |
| `steam_cn` | Steam 中国区畅销榜、热门新品榜，含价格、折扣、评测数、好评率 | 🟡 Steam 商店公开页面 |
| `hk_weather_forecast` | 香港天文台九天预报（存下每天发布的预报，可研究预报准确率） | 🟢 香港天文台开放数据 |
| `hk_carpark_vacancy` | 香港约 430 个停车场实时空位（每日固定时点快照） | 🟢 香港运输署开放数据 |

## 目录结构

```
data/raw/<数据集ID>/<年-月>/<日期>.csv    原始快照（UTF-8，Excel 可直接打开），过了当天永不修改
data/raw/_status/<日期>.json              每天的采集日志：行数、耗时、sha256、失败原因
ledger/<日期>.json                        当天账本（哈希链的一环）
ledger/<日期>.json.ots                    当天账本的 OpenTimestamps 时间戳证明
ledger/HEAD                               最新账本的日期和哈希
DATASETS.md / datasets.json               数据集目录（自动生成）
```

合并成面板数据（Python）：

```python
import pandas as pd, glob
df = pd.concat(pd.read_csv(f) for f in sorted(glob.glob("data/raw/appstore_cn/*/*.csv")))
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

新增数据源：在 `sources/` 下新建一个模块，提供 `NAME`、`TITLE`、`SOURCE_URL`、`LICENSE`、`FIELDS` 和 `collect(session, run)`，参考 [`sources/appstore_cn.py`](sources/appstore_cn.py)。欢迎在 Issue 里推荐"只有实时、没有历史"的数据源。

## 许可

代码以 [MIT](LICENSE) 许可发布。数据的权利归原始来源方，使用时请遵守各数据集标注的来源条款；本仓库只对汇编整理工作主张署名。
