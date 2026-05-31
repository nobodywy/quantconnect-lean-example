# QuantConnect LEAN CLI Example — AI 板块量化策略

一个完整的 QuantConnect LEAN CLI 示例项目，包含 **SMA 交叉策略**、**AI 板块研究数据**（半导体/光通信/存储/ETF）和**可配置的数据下载工具链**，专为 macOS 本地开发优化。

---

## 🧠 策略概览

| 组件 | 详情 |
|---|---|
| **入场信号** | SMA 三线排列：`SMA(20)` > `SMA(50)` > `SMA(100)` |
| **宏观过滤** | SPY 在 200 SMA 之上才允许开仓 🆕 |
| **个股过滤** | 个股价格自身也在 200 SMA 之上 🆕 |
| **选股池** | 动态 top-50 高成交量标的（日成交额 $5M+，股价 > $5） |
| **仓位管理** | ATR(14) 风险预算，单笔风险 1% |
| **止损** | ATR trailing stop（2× 乘数） |
| **调仓** | 每周一 10:00 AM |
| **热度上限** | 最多 10 个持仓，总仓位 ≤ 50% |

---

## 📁 仓库说明书

### 顶层文件

| 文件 | 用途 | 什么时候改 |
|---|---|---|
| `Makefile` | 一键命令入口：`make download` / `make info` / `make help` | 想加新快捷命令时 |
| `lean.json` | LEAN CLI 项目配置（环境名、引擎镜像等） | 不需要改 |
| `config.json` | LEAN 引擎运行参数（交易成本、数据源、基准等） | 调整滑点/手续费时 |
| `Dockerfile` | Docker 运行环境定义（Python 版本、依赖） | 需要额外系统包时 |
| `docker-compose.yml` | Docker 一键编排（挂载目录、端口、环境变量） | 改端口/数据目录时 |
| `requirements.txt` | Python 依赖清单（lean、pandas、numpy 等） | pip install 新库时 |
| `.gitignore` | 告诉 Git 什么不提交（`data/`、`__pycache__`、`.DS_Store`） | 很少需要改 |

---

### `algorithms/` — 策略代码

这是整个仓库的核心。每个 `.py` 文件都是一个完整的 QuantConnect 算法，可以直接跑回测或部署实盘。

| 文件 | 策略 | 难度 | 核心逻辑 |
|---|---|---|---|
| `SmaCrossAlgorithm.py` | SMA 三线交叉 + 200MA 宏观过滤 | ⭐⭐ | SMA(20) > SMA(50) > SMA(100)，SPY 在 200MA 上方才开仓，ATR 止损，动态 top-50 选股池 |
| `CoveredCallAlgorithm.py` | 每周备兑看涨期权 | ⭐⭐⭐ | 持有 NVDA，每周卖 5% OTM Call 收权利金，到期或被行权后重新卖出 |

> 💡 **怎么用**：`lean backtest algorithms/XXX.py`  
> 💡 **怎么切换变种**：改文件顶部的 `FAST_PERIOD`、`SLOW_PERIOD` 等参数

---

### `research/` — 研究文档

量化知识库。从零到进阶，覆盖策略、板块、因子的学习笔记。

| 文件 | 内容 | 适合谁 |
|---|---|---|
| `us-ai-stocks-etfs-2026.md` | 📊 2026 年 5 月 AI 板块全景：43 只标的，含半导体/光通信/存储/ETF 四大方向，附代码和数据来源 | 想了解 AI 赛道有哪些标的 |
| `quant-factors-options-primer.md` | 📘 量化因子 + 期权从零入门：价值/动量/质量等 6 大因子、期权 Greeks、7 种策略，每节附 QuantConnect 代码 | 刚接触量化/期权 |
| `200ma-strategy-handbook.md` | 📈 200 均线策略完全手册：14 种变种（金叉死叉/Ribbon/布林带/斜率/分阶段进出等），每种附完整代码 | 想深入均线策略 |

> 💡 这些文档和策略代码是配对的——看懂了可以直接去 `algorithms/` 跑

---

### `scripts/` — 数据下载工具

帮你拉 QuantConnect 市场数据到本地，不用手动一条条敲。

| 文件 | 用途 | 怎么改 |
|---|---|---|
| `tickers.conf` | 🎛️ 标的配置文件：7 个分组，43 只 ticker，可调整日期区间和并行数 | 直接改 ticker、日期、并行数 |
| `download-data.sh` | 🚀 批量下载脚本：支持并行下载、dry-run 预览、强制覆盖、单板块下载 | 通常不用改 |
| `README.md` | 📖 下载工具专属文档：常见问题、下载量估算、单 ticker 手动下载 | 不用改 |

---

### `notebooks/` — LEAN 研究 Notebook

| 文件 | 用途 |
|---|---|
| `research.ipynb` | Jupyter Notebook，在 LEAN 研究环境里跑，做数据探索和策略雏形 |

---

### `data/` — 本地市场数据 ⚠️ 不提交 Git

```
data/
└── equity/usa/daily/
    ├── nvda/          ← NVDA 日线 .zip 文件
    ├── spy/           ← SPY 日线
    ├── lite/          ← Lumentum 日线
    └── ...            ← 其他已下载标的
```

| 操作 | 命令 |
|---|---|
| 下载 | `make download` 或 `./scripts/download-data.sh` |
| 查看 | `make info` |
| 清空 | `make clean` |
| 手动下载单只 | `lean data download --dataset "TradeBarData/usa_equity_daily" --ticker NVDA --start 20230101 --end 20251231` |

---

### 文件流转图

```
tickers.conf          ← 你配好要下载什么
    │
    ▼
download-data.sh      ← 跑 lean data download 拉数据
    │
    ▼
data/equity/...       ← 数据落地
    │
    ▼
algorithms/*.py       ← 回测从 data/ 读数据
    │
    ▼
lean report           ← 打开浏览器看收益曲线
    │
    ▼
research/*.md         ← 对照研究文档理解策略逻辑
```

---

## 🖥️ macOS 环境搭建

### 前置条件

你需要先安装以下工具。在终端（Terminal.app）中逐条执行：

#### 1. 安装 Homebrew（macOS 包管理器）

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

安装后会提示你运行两行命令来配置 PATH，照着做就行。

#### 2. 安装 Docker Desktop（LEAN 本地回测需要）

```bash
brew install --cask docker
```

安装后打开 Docker Desktop 应用，等它启动完成（菜单栏出现 🐳 图标）。

> **为什么需要 Docker？**
> LEAN CLI 会把策略代码注入到一个预装了 LEAN 引擎的 Docker 容器里执行。Docker 提供了与 QuantConnect 云端一致的运行环境。

#### 3. 安装 Python 和 LEAN CLI

```bash
# macOS 自带 python3，确认版本
python3 --version   # 应该 ≥ 3.9

# 安装 LEAN CLI
pip3 install lean

# 确认安装成功
lean --version
```

#### 4. 登录 QuantConnect

```bash
lean login
```

这会打开浏览器，登录你的 QuantConnect 账号（没有的话去 https://www.quantconnect.com 免费注册一个），然后授权 CLI。

### `make` 是什么？

`make` 不是一个编程语言，而是一个**构建自动化工具**（1976 年诞生，Unix 家族原住民）。

`Makefile` 文件里定义的是一组**快捷命令**（类似 npm scripts / shell 别名），让你不用记一堆参数，打一个单词就能执行。

```bash
make download      # 等于执行 ./scripts/download-data.sh all
make info          # 等于执行一串 shell 命令查看数据状态
make help          # 列出所有可用命令
```

macOS 自带 `make`，不需要额外安装。

---

## 🚀 快速开始（macOS）

```bash
# 1. 克隆仓库
git clone https://github.com/nobodywy/quantconnect-lean-example.git
cd quantconnect-lean-example

# 2. 下载 AI 板块数据（43 个标的，约 3-5 分钟）
make download

# 3. 运行回测
lean backtest algorithms/SmaCrossAlgorithm.py

# 4. 查看报告（自动打开浏览器）
lean report
```

---

## 📊 数据下载

### Makefile 快捷命令

| 命令 | 下载内容 | 标的总数 |
|---|---|---|
| `make download` | 🔥 全部（基准 + AI + 半导体 + 光通信 + 存储 + ETF） | 43 |
| `make download-ai` | AI 龙头 + 应用层 | 14 |
| `make download-optical` | 光通信（LITE/CIEN/GLW/COHR/ANET） | 5 |
| `make download-semicon` | 半导体（ASML/AVGO/QCOM/TSEM/NVTS/ON） | 5 |
| `make download-storage` | 存储（MU/SNDK/WDC/STX/PSTG） | 5 |
| `make download-etfs` | AI ETF + 基准（SPY/QQQ/SMH...） | 14 |
| `make dry-run` | 🧪 预览操作，不实际下载 | — |
| `make info` | 📋 查看本地已下载数据 | — |
| `make clean` | 🗑️ 删除本地数据（带确认） | — |
| `make help` | ❓ 完整帮助 | — |

### 自定义配置

编辑 `scripts/tickers.conf`：

```bash
# 加自己的标的
AI_LEADERS="NVDA AVGO AMD INTC TSLA"   # 加 TSLA

# 拉更长时间段
START_DATE="20200101"
END_DATE="20260531"

# 调并行数（免费账号建议 1-2）
PARALLEL=1
```

### 不用 make，直接调脚本

```bash
# 下载光通信 + 存储
./scripts/download-data.sh optical storage

# 只预览不下载
./scripts/download-data.sh --dry-run all

# 单线程（慢但稳）
./scripts/download-data.sh -p 1 all
```

---

## 🔧 回测与部署

### 本地回测（免费无限次）

```bash
# 用刚下载的数据跑回测
lean backtest algorithms/SmaCrossAlgorithm.py

# 查看交互式 HTML 报告
lean report
```

### 云端回测

```bash
# 推代码到 QC 云端（不需要本地数据）
lean cloud push

# 云端回测
lean cloud backtest algorithms/SmaCrossAlgorithm.py
```

### 实盘部署

```bash
lean cloud live deploy \
  --project "SmaCrossAlgorithm" \
  --brokerage "InteractiveBrokersBrokerage"
```

---

## 🎛️ 策略参数调优

在 `algorithms/SmaCrossAlgorithm.py` 中修改这些参数：

```python
FAST_PERIOD         = 20       # 快线 SMA
MEDIUM_PERIOD       = 50       # 中线 SMA
SLOW_PERIOD         = 100      # 慢线 SMA
TREND_PERIOD        = 200      # 200 SMA 趋势过滤 🆕
MACRO_SYMBOL        = "SPY"    # 宏观过滤标的 🆕
ENABLE_MACRO_FILTER = True     # 是否启用 SPY 200MA 开关 🆕
ATR_PERIOD          = 14       # ATR 回溯周期
ATR_STOP_MULTIPLIER = 2.0      # 止损宽度（越大越宽松）
MAX_POSITIONS       = 10       # 最大持仓数
RISK_PER_POSITION   = 0.01     # 单笔风险 1%
HEAT_CAP            = 0.50     # 总仓位上限 50%
```

---

## 🏷️ AI 板块研究

见 `research/us-ai-stocks-etfs-2026.md`，覆盖：

| 板块 | 个股 | ETF |
|---|---|---|
| AI 核心龙头 | NVDA, MSFT, GOOGL, AMZN, META... | AIQ, QTUM, AIPI... |
| 半导体 | ASML, AVGO, QCOM, TSEM, NVTS, ON | SMH, SOXX, SOXL, SOXS |
| 光通信 🆕 | LITE, CIEN, GLW, COHR, ANET | — |
| 存储/内存 | MU, SNDK, WDC, STX, PSTG | DRAM |

---

## 📚 参考资料

- [QuantConnect LEAN CLI 文档](https://www.quantconnect.com/docs/v2/lean-cli)
- [LEAN Engine GitHub](https://github.com/QuantConnect/Lean)
- [算法框架概述](https://www.quantconnect.com/docs/v2/writing-algorithms/algorithm-framework/overview)
- [LEAN 研究环境](https://www.quantconnect.com/docs/v2/research-environment)

## 📝 License

MIT
