# 美股 AI 板块每日收盘报告机器人

> macOS 本地运行，yfinance 拉数据，自动生成 Markdown 报告

---

## 快速开始

```bash
# 1. 安装依赖
pip install yfinance pandas numpy

# 2. 跑一次看效果
python3 scripts/report-bot/daily-report.py

# 3. 保存到文件
python3 scripts/report-bot/daily-report.py --save
# → reports/report-2026-05-31.md
```

## 报告内容

| 模块 | 说明 |
|---|---|
| 📊 大盘基准 | SPY / QQQ 收盘价、涨跌、SMA(20/50/200)、成交量比、200MA 趋势 |
| 🧠 AI 核心龙头 | NVDA, AVGO, AMD, MSFT, GOOGL, AMZN, META, ORCL, PLTR, ANET |
| 🔬 半导体 | ASML, QCOM, TSM, INTC, ON |
| 📡 光通信 | LITE, CIEN, GLW, COHR |
| 💾 存储 | MU, SNDK, WDC, STX |
| 📦 ETF | SMH, AIQ, QTUM, AIPI, DRAM |
| 🏆 排名 | 日内涨跌 TOP 5 + 垫底 5 |
| ⚡ 信号 | 自动检测多头/空头排列、爆量、突破/跌破 200MA |

## 定时运行（macOS）

### 方式一：launchd（推荐）

```bash
# 1. 创建 plist
cat > ~/Library/LaunchAgents/com.quantconnect.daily-report.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
 "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.quantconnect.daily-report</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/你的用户名/quantconnect-lean-example/scripts/report-bot/daily-report.py</string>
        <string>--save</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>      <integer>5</integer>   <!-- UTC+8 早上 5 点 -->
        <key>Minute</key>    <integer>0</integer>
        <key>Weekday</key>   <integer>1,2,3,4,5</integer>  <!-- 周一~周五 -->
    </dict>
    <key>StandardOutPath</key>
    <string>/tmp/daily-report.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/daily-report.err</string>
</dict>
</plist>
EOF

# 2. 加载
launchctl load ~/Library/LaunchAgents/com.quantconnect.daily-report.plist

# 3. 验证
launchctl list | grep daily-report
```

> ⚠️ 记得把 `/Users/你的用户名/` 改成实际路径。

### 方式二：crontab

```bash
crontab -e
# 添加：
# 美股收盘约 4:30 AM UTC+8（16:30 ET），工作日下午 5:00 运行（确保数据全部出来）
0 17 * * 1-5 cd ~/quantconnect-lean-example && /usr/bin/python3 scripts/report-bot/daily-report.py --save >> /tmp/daily-report.log 2>&1
```

## 自定义标的

编辑 `scripts/report-bot/tickers.py`，按格式增删：

```python
WATCHLIST = {
    "NVDA":  {"name": "NVIDIA",   "group": "ai_stocks"},
    "TSLA":  {"name": "Tesla",    "group": "ai_stocks"},   # ← 加新标的
    # "PLTR":  {"name": "Palantir", "group": "ai_stocks"}, # ← 注释掉不要的
}
```

分组名可选: `ai_stocks`, `semiconductors`, `optical`, `storage`, `etfs`, `benchmarks`

## 预期输出

```
# 🇺🇸 美股 AI 板块收盘报告
**2026-05-31**  (生成时间: 2026-05-31 21:30 UTC)

## 📊 大盘基准
| 标的 | 收盘价 | 日涨跌 | SMA 20 | SMA 50 | SMA 200 | 量比 | 趋势 |
|------|--------|--------|--------|--------|---------|------|------|
| 🟢 SPY | $595.32 | +0.42% | $592.10 | $589.50 | $575.80 | 0.9× | 🟢 线上 |
...

## 🏆 日内涨跌排名
### 涨幅 TOP 5
1. 🔥 LITE (Lumentum): +8.32%
2. 🟢 SNDK (SanDisk): +5.74%
...
```

## 常见问题

**Q: `No module named 'yfinance'`**
```bash
pip install yfinance pandas numpy
```

**Q: 拉不到某些股票数据**
- 确认 ticker 正确（美股不用加后缀，如 `NVDA` 不是 `NVDA.US`）
- 可能是退市/改名/数据源缺
- 检查网络:`ping pypi.org`

**Q: launchd 没跑起来**
```bash
# 查看日志
cat /tmp/daily-report.log
cat /tmp/daily-report.err

# 手动跑一次验证路径
/usr/bin/python3 ~/quantconnect-lean-example/scripts/report-bot/daily-report.py
```

**Q: 想把报告发到飞书**
报告 `.md` 文件存在 `reports/` 下，可以由 OpenClaw bot 定时读取并通过飞书消息发送。
