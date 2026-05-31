# QuantConnect LEAN CLI Example

A production-ready SMA Crossover algorithmic trading strategy built with **QuantConnect LEAN** and the **LEAN CLI** for local backtesting and live deployment.

## 🧠 Strategy Overview

| Component | Detail |
|---|---|
| **Entry Signal** | SMA Crossover: `SMA(20)` > `SMA(50)` > `SMA(100)` |
| **Universe** | Dynamic top-50 by daily dollar volume ($5M+ minimum) |
| **Position Sizing** | ATR-based, 1% portfolio risk per trade |
| **Stop Loss** | ATR(14) trailing stop with 2× multiplier |
| **Rebalance** | Weekly (Monday 10 AM) |
| **Heat Cap** | Max 50% of portfolio deployed |
| **Max Positions** | 10 concurrent holdings |

## 📁 Project Structure

```
quantconnect-lean-example/
├── algorithms/
│   └── SmaCrossAlgorithm.py      # Core trading algorithm
├── notebooks/
│   └── research.ipynb             # LEAN research notebook
├── data/                          # Local market data (managed by CLI)
├── lean.json                      # LEAN CLI configuration
├── config.json                    # LEAN engine configuration
├── Dockerfile                     # Docker runtime
├── docker-compose.yml             # Local Docker orchestration
├── requirements.txt               # Python dependencies
└── .gitignore
```

## 🚀 Quick Start

### 1. Install LEAN CLI

```bash
pip install lean
```

### 2. Authenticate with QuantConnect

```bash
lean login
```

Generate your API credentials at: https://www.quantconnect.com/account

### 3. Pull market data

```bash
# Pull SPY daily data for backtesting
lean data download \
  --dataset "TradeBarData/usa_equity_daily" \
  --ticker SPY \
  --start 20230101 \
  --end 20241231

# Pull coarse universe data
lean data download \
  --dataset "CoarseUniverseGenerator" \
  --start 20230101 \
  --end 20241231
```

### 4. Run backtest

```bash
# Run locally with Docker
lean backtest algorithms/SmaCrossAlgorithm.py

# Run in QuantConnect cloud
lean cloud backtest algorithms/SmaCrossAlgorithm.py
```

### 5. View results

```bash
lean report
# Opens an interactive HTML report with charts and metrics
```

## 🔧 Live Deployment

1. Create a live project in QuantConnect Cloud
2. Set environment variables:
   ```bash
   export QC_USER_ID="your-user-id"
   export QC_API_TOKEN="your-api-token"
   ```
3. Deploy:
   ```bash
   lean cloud live deploy \
     --project "SmaCrossAlgorithm" \
     --brokerage "InteractiveBrokersBrokerage"
   ```

## 📊 Key Parameters

Modify these in `SmaCrossAlgorithm.py` to tune the strategy:

```python
FAST_PERIOD         = 20      # Fast SMA
MEDIUM_PERIOD       = 50      # Medium SMA
SLOW_PERIOD         = 100     # Slow SMA (trend filter)
ATR_PERIOD          = 14      # ATR lookback
ATR_STOP_MULTIPLIER = 2.0     # Trailing stop width
MAX_POSITIONS       = 10      # Max concurrent positions
RISK_PER_POSITION   = 0.01    # 1% risk per trade
HEAT_CAP            = 0.50    # Max 50% of portfolio
```

## 📚 References

- [QuantConnect LEAN CLI Docs](https://www.quantconnect.com/docs/v2/lean-cli)
- [LEAN Engine GitHub](https://github.com/QuantConnect/Lean)
- [Algorithm Framework](https://www.quantconnect.com/docs/v2/writing-algorithms/algorithm-framework/overview)

## 📝 License

MIT
