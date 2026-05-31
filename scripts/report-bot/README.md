# 美股 AI 板块收盘报告机器人

> **零依赖，纯 Python 标准库，OpenClaw sandbox 原生运行**

---

## 它是怎么跑的

```
Yahoo Finance API             OpenClaw cron
(免费, 无需 key)              (已注册)
      │                           │
      ├── NVDA $211.14 ───┐       │  20:30 UTC
      ├── AVGO $446.77 ───┤       │  美股收盘后
      ├── LITE $854.96 ───┤       │
      ├── SPY  $756.48 ───┤       ▼
      ├── ... 29 只 ──────┘   触发脚本
                                      │
                              daily-report.py
                              (纯 stdlib)
                                      │
                              SMA(20/50/200)
                              量比 · 趋势
                              涨跌排名 · 信号
                                      │
                                      ▼
                              飞书推送给小杨
```

---

## 覆盖标的（29 只）

| 板块 | 标的 |
|---|---|
| 📊 大盘 | SPY, QQQ |
| 🧠 AI 龙头 | NVDA, AVGO, AMD, MSFT, GOOGL, AMZN, META, ORCL, PLTR, ANET |
| 🔬 半导体 | ASML, QCOM, TSM, INTC, ON |
| 📡 光通信 | LITE, CIEN, GLW, COHR |
| 💾 存储 | MU, SNDK, WDC, STX |
| 📦 ETF | SMH, AIQ, QTUM, AIPI |

## 手动触发

```bash
# 完整报告
python3 scripts/report-bot/daily-report.py

# 只看部分标的
python3 scripts/report-bot/daily-report.py --tickers=NVDA,AVGO,LITE,SPY
```

## 定制

编辑 `daily-report.py` 顶部的 `WATCHLIST` 字典增删标的。

## 技术栈

- Python 3 stdlib: `urllib` + `json`
- 数据源: Yahoo Finance v8 chart API
- 零外部依赖，无需 pip install
