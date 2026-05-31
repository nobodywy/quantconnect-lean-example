# QuantConnect LEAN CLI Example — AI 板块量化策略

一个完整的 QuantConnect LEAN CLI 示例项目，包含 **SMA 交叉策略**、**AI 板块研究数据**（半导体/光通信/存储/ETF）和**可配置的数据下载工具链**，专为 macOS 本地开发优化。

---

## 🧠 策略概览

| 组件 | 详情 |
|---|---|
| **入场信号** | SMA 三线交叉：`SMA(20)` > `SMA(50)` > `SMA(100)` |
| **选股池** | 动态 top-50 高成交量标的（日成交额 $5M+） |
| **仓位管理** | ATR(14) 风险预算，单笔风险 1% |
| **止损** | ATR trailing stop（2× 乘数） |
| **调仓** | 每周一 10:00 AM |
| **热度上限** | 最多 10 个持仓，总仓位 ≤ 50% |

---

## 📁 项目结构

```
quantconnect-lean-example/
├── algorithms/
│   └── SmaCrossAlgorithm.py       # 核心策略
├── scripts/
│   ├── tickers.conf               # 标的配置（43 只，7 个分组）
│   ├── download-data.sh           # 批量下载脚本
│   └── README.md                  # 下载工具文档
├── research/
│   └── us-ai-stocks-etfs-2026.md  # 2026 AI 板块全景研究
├── notebooks/
│   └── research.ipynb             # LEAN 研究 Notebook
├── data/                          # 本地市场数据（由 CLI 管理，不入 git）
├── Makefile                       # 顶层快捷命令
├── lean.json                      # LEAN CLI 配置
├── config.json                    # LEAN 引擎配置
├── Dockerfile + docker-compose.yml # Docker 运行时
├── requirements.txt
└── .gitignore
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
SLOW_PERIOD         = 100      # 慢线 SMA（趋势过滤）
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
