# 数据下载脚本

> 📅 2026-05-31 | 配套 SMA Crossover 策略 + AI 板块研究

---

## 快速开始

```bash
# 1. 安装 Lean CLI（如果还没装）
pip install lean

# 2. 登录 QuantConnect（免费账号即可）
lean login

# 3. 一键下载全部 AI 板块数据
make download
```

## 使用方式

### Makefile（推荐）

| 命令 | 说明 |
|---|---|
| `make download` | 下载全部（基准 + AI + 半导体 + 光通信 + 存储 + ETF） |
| `make download-ai` | 仅 AI 核心龙头 + 应用层 |
| `make download-optical` | 仅光通信（LITE/CIEN/GLW/COHR/ANET） |
| `make download-semicon` | 仅半导体（ASML/AVGO/QCOM...） |
| `make download-storage` | 仅存储（MU/SNDK/WDC/STX/PSTG） |
| `make download-etfs` | 仅 ETF（AIQ/QTUM/SMH/SOXX...） + 基准 |
| `make dry-run` | 预览所有操作，不实际下载 |
| `make info` | 查看本地数据状态 |
| `make clean` | 删除本地数据 |
| `make help` | 显示完整帮助 |

### 直接调用脚本

```bash
# 下载全部
./scripts/download-data.sh

# 只下载光通信 + 存储
./scripts/download-data.sh optical storage

# 预览（不实际下载）
./scripts/download-data.sh --dry-run all

# 单线程下载（避免 API 限频）
./scripts/download-data.sh -p 1 all

# 强制重新下载已有数据
./scripts/download-data.sh --force ai_leaders
```

## 配置

编辑 `scripts/tickers.conf` 自定义标的列表和日期：

```bash
# 日期区间
START_DATE="20230101"     # 回测起始
END_DATE="20251231"       # 回测结束

# 并行数（QC 免费账号建议 ≤2）
PARALLEL=2

# 增删 ticker 直接改下面各组
AI_LEADERS="NVDA AVGO AMD ..."
```

## 板块覆盖

| 分组 | 标的 | 数量 |
|---|---|---|
| `benchmarks` | SPY, QQQ, VUG, IYW, XLK | 5 |
| `ai_leaders` | NVDA, AVGO, AMD, INTC, MSFT, GOOGL, AMZN, META, ORCL | 9 |
| `semiconductors` | ASML, QCOM, TSEM, NVTS, ON | 5 |
| `optical` | LITE, CIEN, GLW, COHR, ANET | 5 |
| `storage` | MU, SNDK, WDC, STX, PSTG | 5 |
| `ai_apps` | PLTR, CRWV, SNPS, ALAB, BE | 5 |
| `ai_etfs` | AIQ, QTUM, ARTY, BAI, BOTZ, AIPI, SMH, SOXX, SOXL | 9 |

**合计：43 个标的**

## 下载量估算

- 日线数据：每个标的约 500 条记录（2 年）≈ 50-200 KB zip
- 全部 43 个标的 ≈ **5-10 MB**
- 下载时间：并行 2 ≈ **3-5 分钟**（取决于网络和 QC API 限频）

## 下载后

```bash
# 本地回测
lean backtest algorithms/SmaCrossAlgorithm.py

# 查看报告
lean report

# 数据状态
make info
```

## 常见问题

**Q: `lean: command not found`**
```bash
pip install lean
```

**Q: 下载报错 API rate limit**
降低并行数: `./scripts/download-data.sh -p 1 ai_leaders`

**Q: 某个 ticker 下载失败**
单 ticker 手动下载：
```bash
lean data download \
  --dataset "TradeBarData/usa_equity_daily" \
  --ticker NVDA \
  --start 20230101 --end 20251231
```

**Q: 数据存在哪里？**
`data/equity/usa/daily/<ticker>/`（已被 .gitignore 忽略，不入版控）
