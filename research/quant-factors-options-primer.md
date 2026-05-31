# 量化因子与期权基础手册

> 📅 2026-05-31 | 面向股票市场量化入门
> 🎯 从零开始：因子 → 组合 → 期权 → QuantConnect 实战

---

## 目录

- [第一部分：股票量化因子](#第一部分股票量化因子)
  - [1.1 什么是因子](#11-什么是因子)
  - [1.2 价值因子](#12-价值因子-value)
  - [1.3 动量因子](#13-动量因子-momentum)
  - [1.4 质量因子](#14-质量因子-quality)
  - [1.5 规模因子](#15-规模因子-size)
  - [1.6 低波动因子](#16-低波动因子-low-volatility)
  - [1.7 成长因子](#17-成长因子-growth)
  - [1.8 流动性因子](#18-流动性因子-liquidity)
  - [1.9 多因子组合](#19-多因子组合)
- [第二部分：期权基础](#第二部分期权基础)
  - [2.1 什么是期权](#21-什么是期权)
  - [2.2 期权四大希腊字母](#22-期权四大希腊字母-greeks)
  - [2.3 常见期权策略](#23-常见期权策略)
  - [2.4 QuantConnect 期权实战](#24-quantconnect-期权实战)
- [第三部分：学习路线图](#第三部分学习路线图)

---

# 第一部分：股票量化因子

## 1.1 什么是因子

> **因子（Factor）** = 能够解释或预测股票收益的某种特征/指标

举个最简单的例子：**你妈教你的「便宜买好货」**——市盈率（P/E）低的股票未来可能涨更多。往回看 100 年数据，这个规律确实存在。这就是**价值因子**。

学术圈和华尔街把这种规律系统地研究出来，叫**因子投资（Factor Investing）**。

### 最常见的六大类因子

```
                    ┌── 价值 (Value)      便宜 vs 贵
                    ├── 动量 (Momentum)    涨的继续涨
因子宇宙 ────────────┼── 质量 (Quality)     好公司 vs 烂公司
                    ├── 规模 (Size)        大公司 vs 小公司
                    ├── 低波动 (Low Vol)   稳 vs 浪
                    └── 成长 (Growth)      高速增长 vs 成熟
```

---

## 1.2 价值因子 (Value)

### 核心思想
**「打折货，捡便宜」**——买被市场低估的股票。

### 常用指标

| 指标 | 公式 | 含义 |
|---|---|---|
| **P/E** (市盈率) | 股价 ÷ 每股盈利 | 1 块钱利润市场愿意付多少钱 |
| **P/B** (市净率) | 股价 ÷ 每股净资产 | 股价相对公司「硬资产」的倍数 |
| **P/S** (市销率) | 总市值 ÷ 总营收 | 适用于尚未盈利的成长公司 |
| **P/CF** (市现率) | 股价 ÷ 每股现金流 | 比利润更难造假 |
| **Dividend Yield** | 每股股息 ÷ 股价 | 分红收益率 |

### 直觉理解

> P/E = 10 → 你花 100 块买一家每年赚 10 块的公司，10 年回本
> P/E = 100 → 你花 100 块买一家每年赚 1 块的公司，100 年才回本

理论上，**P/E 越低越好**（同等条件下）。

### QuantConnect 代码

```python
# 用 coarse universe 筛选低 P/E 股票
def CoarseFineSelection(self, coarse, fine):
    # fine 包含 Fundamental 数据
    filtered = [
        f for f in fine
        if f.ValuationRatios.PERatio > 0          # P/E 必须为正
        and f.ValuationRatios.PERatio < 15         # P/E < 15（便宜）
        and f.OperationRatios.ROE.Value > 10       # ROE > 10%（也得能赚钱）
    ]
    sorted_by_value = sorted(filtered,
                             key=lambda f: f.ValuationRatios.PERatio)
    return [f.Symbol for f in sorted_by_value[:20]]
```

### 风险提示
- 低 P/E 可能是因为公司基本面真的出问题了（价值陷阱）
- 建议结合质量因子（ROE、负债率）一起用

---

## 1.3 动量因子 (Momentum)

### 核心思想
**「趋势会延续」**——过去涨的好的，未来一段时间倾向于继续涨。

### 常用指标

| 指标 | 公式 | 典型窗口 |
|---|---|---|
| **价格动量** | 过去 N 个月的总回报 | 6 个月、12 个月 |
| **残差动量** | 剔除市场 Beta 后的超额收益 | 12 个月 |
| **均线信号** | SMA(快) vs SMA(慢) | 20/50/200 日 |
| **RSI** | 相对强弱指标 | 14 日 |

### 学术界最强发现

> 12-1 动量：过去 12 个月（剔除最近 1 个月）回报最高的股票，下个月平均跑赢最低组。
> 这个效应在美股、A 股、全球几乎所有市场都存在，是**最稳健的因子之一**。

### 直觉理解

```
动量 = 趋势跟踪 = 顺势而为

    不是说「追高」，而是「趋势确认后再上车」
    ── 同时设好止损，错了就认赔
```

### QuantConnect 代码

```python
# 12 个月动量筛选
def SelectByMomentum(self, symbols):
    history = self.History(symbols, 252, Resolution.Daily)  # ~12 个月

    momentum = {}
    for symbol in symbols:
        try:
            closes = history.loc[symbol]['close']
            if len(closes) < 200:
                continue
            # 12-1 动量：近 12 个月（跳过最近 21 天）的涨幅
            ret_12m = (closes.iloc[-21] / closes.iloc[-252]) - 1
            momentum[symbol] = ret_12m
        except:
            continue

    # 选动量最高的 20 只
    sorted_mom = sorted(momentum.items(), key=lambda x: x[1], reverse=True)
    return [s for s, _ in sorted_mom[:20]]
```

### 风险提示
- **动量崩溃（Momentum Crash）**：市场急转时，动量策略会巨亏（如 2009 年 3 月反弹）
- 建议结合波动率控制仓位

---

## 1.4 质量因子 (Quality)

### 核心思想
**「好公司长期跑赢烂公司」**——用财务指标筛选经营质量高的企业。

### 常用指标

| 指标 | 公式 | 含义 |
|---|---|---|
| **ROE** | 净利润 ÷ 净资产 | 股东投入 1 块钱能赚多少 |
| **ROA** | 净利润 ÷ 总资产 | 公司全部资产的利用效率 |
| **Gross Margin** | 毛利 ÷ 营收 | 定价能力（越高越好） |
| **Debt/Equity** | 总负债 ÷ 净资产 | 杠杆水平（越低越安全） |
| **Earnings Stability** | 过去 N 年 EPS 增长的标准差 | 盈利稳定性 |
| **Accruals** | (净利润 − 经营现金流) ÷ 总资产 | 利润「水分」（越小越好） |

### 直觉理解

> ROE = 20% → 你投 100 块进去，公司一年帮你赚 20 块
> ROE = 5% → 你投 100 块进去，公司一年帮你赚 5 块（不如存银行）
> 
> 但 ROE 太高也别盲目信——可能杠杆拉满的结果，还得看 Debt/Equity

### QuantConnect 代码

```python
# 质量筛选：高 ROE + 低杠杆 + 稳定盈利
def QualityFilter(self, fine):
    qualified = []
    for f in fine:
        roe = f.OperationRatios.ROE.Value
        de  = f.OperationRatios.TotalDebtToEquity.Value
        gm  = f.OperationRatios.GrossMargin.Value

        if (roe is not None and roe > 15 and          # ROE > 15%
            de  is not None and de  < 1.0 and          # 负债率 < 100%
            gm  is not None and gm  > 30):             # 毛利率 > 30%
            qualified.append((f.Symbol, roe))

    sorted_by_quality = sorted(qualified, key=lambda x: x[1], reverse=True)
    return [s for s, _ in sorted_by_quality[:30]]
```

---

## 1.5 规模因子 (Size)

### 核心思想
**「小盘股长期跑赢大盘股」**——但近年这个规律有所减弱。

| 指标 | 含义 |
|---|---|
| **Market Cap** | 总市值 = 股价 × 总股数 |
| 大盘股 | > $100 亿 |
| 中盘股 | $20 亿 ~ $100 亿 |
| 小盘股 | < $20 亿 |

### QuantConnect 代码

```python
# 市值中性化的多因子（控制规模偏误）
def SizeNeutralSelection(self, coarse):
    # 1. 按市值分 5 组
    # 2. 在每组内按动量/价值/质量排序
    # 3. 每组各选 top N
    pass  # 进阶话题，建议先跑通基础因子再说
```

---

## 1.6 低波动因子 (Low Volatility)

### 核心思想
**「慢即是快」**——低波动的股票长期风险调整后收益（夏普比）反而更高。

这有点反直觉：按理说高风险高回报，但数据显示**高波动股票的回报并没有足够高**，而**低波动股票有超额收益**。

| 指标 | 公式 |
|---|---|
| **Beta** | 相对市场的敏感度（1=跟市场同步） |
| **Historical Volatility** | 过去 N 日收益率标准差 |
| **Max Drawdown** | 历史最大回撤 |

### QuantConnect 代码

```python
# 低波动选股
def LowVolSelection(self, symbols):
    history = self.History(symbols, 252, Resolution.Daily)

    vols = {}
    for symbol in symbols:
        try:
            returns = history.loc[symbol]['close'].pct_change().dropna()
            vols[symbol] = returns.std()  # 年化波动率
        except:
            continue

    # 选波动率最低的 N 只
    sorted_vol = sorted(vols.items(), key=lambda x: x[1])
    return [s for s, _ in sorted_vol[:20]]
```

---

## 1.7 成长因子 (Growth)

### 核心思想
**「高速增长的公司值得更高估值」**

| 指标 | 公式 |
|---|---|
| **EPS Growth** | (今年 EPS − 去年 EPS) ÷ 去年 EPS |
| **Revenue Growth** | (今年营收 − 去年营收) ÷ 去年营收 |
| **PEG** | P/E ÷ EPS Growth | 成长估值比（< 1 偏便宜） |

---

## 1.8 流动性因子 (Liquidity)

- **Dollar Volume** = 日均成交量 × 股价 → 越高越容易进出
- **Bid-Ask Spread** → 越低流动性越好

**实务建议**：日成交额 < $500 万的股票直接过滤掉，避免「买得进卖不出」。

---

## 1.9 多因子组合

单独一个因子有时失效，组合起来更稳健。

### 经典组合方式

```
方式 1: 等权打分（Z-Score）

  原始值 → 标准化（Z-Score）→ 加权求和 → 排名
  例：Score = 0.4 × Z(Value) + 0.3 × Z(Momentum) + 0.3 × Z(Quality)

方式 2: 交叉筛选

  先用质量筛 → 再用价值排 → 最后选动量最高的 N 只

方式 3: 因子暴露（Barra 模型）

  控制行业/市值等风险因子，只暴露目标因子
  （机构主流做法，个人量化学有余力再看）
```

### QuantConnect 多因子示例

```python
class MultiFactorAlgorithm(QCAlgorithm):
    def CompositeScore(self, symbol):
        # 取三个因子的 Z-Score（越高越好）
        z_mom = self._zscore(symbol, 'momentum')
        z_val = self._zscore(symbol, 'value')     # P/E 倒数，越大越便宜
        z_qua = self._zscore(symbol, 'quality')    # ROE

        # 等权合成
        if z_mom and z_val and z_qua:
            return 0.4 * z_mom + 0.3 * z_val + 0.3 * z_qua
        return None
```

---

# 第二部分：期权基础

## 2.1 什么是期权

> **期权 = 一份「未来以约定价格买卖某个东西」的权利（不是义务）**

### 两个基本品种

| | Call（看涨期权） | Put（看跌期权） |
|---|---|---|
| **买方权利** | 以「行权价」买入标的 | 以「行权价」卖出标的 |
| **买方最大亏损** | 权利金（保费） | 权利金 |
| **买方最大收益** | 理论上无限 | 行权价 − 权利金 |
| **卖方最大收益** | 权利金 | 权利金 |
| **卖方最大亏损** | 理论上无限 | 行权价 − 权利金 |

### 一个直觉类比

```
买 Call ≈ 交押金锁定房价

  房子现在 500 万，你看涨，花 5 万买一个「一年后以 500 万买入」的权利
    → 一年后涨到 600 万：你行权，500 万买进，净赚 100−5=95 万
    → 一年后跌到 400 万：你放弃行权，亏 5 万押金（不需要 500 万买房）
```

```
卖 Covered Call ≈ 当包租公 + 卖涨价权

  你持有 100 股 AAPL（成本 $150），同时卖一张 $180 Call（收 $5 权利金）
    → AAPL 到期 < $180：赚了 $5 权利金，股票还在
    → AAPL 到期 > $180：股票被行权卖掉，赚 ($180−$150+$5)=$35/股
```

---

## 2.2 期权四大希腊字母 (Greeks)

Greeks 度量期权价格对各个因素的敏感度。交易期权必须懂。

| 希腊字母 | 衡量什么 | 直觉 | 范围 |
|---|---|---|---|
| **Delta (Δ)** | 标的涨 $1，期权价格变多少 | 方向性暴露 | Call: 0~1, Put: −1~0 |
| **Gamma (Γ)** | Delta 的变化速度 | 加速度 | 到期日越近越大 |
| **Theta (Θ)** | 时间每过一天，期权贬多少 | **时间的朋友（卖方）/ 敌人（买方）** | 总是负（买方） |
| **Vega (ν)** | 波动率涨 1%，期权价格变多少 | 恐慌/贪婪溢价 | 长期期权更大 |

### 实战记忆

```
期权买方：Long Delta, Long Gamma, Short Theta
          「对了赚很多，错了就亏权利金，但每天都在亏时间」

期权卖方：Short Gamma, Long Theta
          「每天收租，但一次黑天鹅可能亏穿底裤」
```

---

## 2.3 常见期权策略

### 策略一览

| 策略 | 构成 | 适用场景 | 风险等级 |
|---|---|---|---|
| **Covered Call** | 持股 + 卖 Call | 看微涨/横盘，赚权利金 | ⭐ |
| **Cash-Secured Put** | 现金 + 卖 Put | 想低价接货 + 赚权利金 | ⭐⭐ |
| **Protective Put** | 持股 + 买 Put | 买保险，防暴跌 | ⭐ |
| **Collar** | 持股 + 买 Put + 卖 Call | 零成本对冲 | ⭐⭐ |
| **Iron Condor** | 卖 Put 价差 + 卖 Call 价差 | 震荡市，吃时间价值 | ⭐⭐⭐ |
| **Straddle** | 买 Call + 买 Put（同行权价） | 赌大波动，不管方向 | ⭐⭐⭐ |
| **Strangle** | 买 OTM Call + OTM Put | 便宜版 Straddle | ⭐⭐⭐ |

### 策略详解

#### 1. Covered Call（备兑看涨）

```
你持有 NVDA，成本 $200
同时卖一张行权价 $250 的 Call，收 $10 权利金

到期情景：
  NVDA < $250  → Call 作废，你赚 $10，股票还在
  NVDA > $250  → 对方行权，你被迫 $250 卖掉，总共赚 ($250−200+10)=$60
```

**为什么用**：增强持有收益（AIPI ETF 就是这个策略，年化 34.8% 收益）

#### 2. Cash-Secured Put（现金担保卖 Put）

```
你想以 $180 买 AAPL（现价 $200）
卖一张 $180 Put，收 $5 权利金

到期情景：
  AAPL > $180  → 没买到股票，但白赚 $5
  AAPL < $180  → 被迫以 $180 买入，但收了 $5，实际成本 $175
```

**为什么用**：比直接挂限价单多一份权利金收入

#### 3. Iron Condor（铁秃鹰）

```
同时卖出：
  卖 OTM Put 价差  + 卖 OTM Call 价差
= 「我赌股价就在这个区间里不动」
= 赚时间价值 + 有最大亏损上限
```

### 盈亏结构速览

```
Covered Call:
      盈亏
        ↑    ╱
        │   ╱
    ────┼──╱────→ 到期股价
        │ ╱
        │╱

Iron Condor:
      盈亏
        ↑    ╱￣￣￣╲        ← 这个平台就是利润区
        │   ╱       ╲
    ────┼──╱─────────╲──→ 到期股价
        │ ╱           ╲
```

---

## 2.4 QuantConnect 期权实战

### Covered Call 策略代码

```python
class CoveredCallAlgorithm(QCAlgorithm):
    """
    持仓 NVDA，每周卖出 OTM Covered Call 收权利金
    """
    def Initialize(self):
        self.SetStartDate(2024, 1, 1)
        self.SetCash(100_000)

        self.equity = self.AddEquity("NVDA", Resolution.Minute)
        option = self.AddOption("NVDA", Resolution.Minute)
        option.SetFilter(lambda universe: universe.IncludeWeeklys()
                         .Strikes(+5, +15)           # 行权价高于现价 5~15 档
                         .Expiration(7, 30))          # 7~30 天到期
        self.option_symbol = option.Symbol

    def OnData(self, data):
        # 如果持有股票且没有卖出的 Call
        if (self.Portfolio["NVDA"].Invested
            and not self.Portfolio.Invested
            and self.Time.weekday() == 1):            # 每周二操作

            for chain in data.OptionChains.Values:
                # 选 OTM Call：行权价 > 现价 × 1.05
                calls = [c for c in chain
                         if c.Right == OptionRight.Call
                         and c.Strike > self.Securities["NVDA"].Price * 1.05]

                if calls:
                    # 选到期日最近的
                    call = sorted(calls, key=lambda x: x.Expiry)[0]
                    # 卖 1 张（对应 100 股）
                    self.Sell(call.Symbol, 1)
```

### 关键概念速记

```
1 张期权合约 = 100 股
  → 卖 1 张 NVDA Call = 对应 100 股 NVDA

期权链（OptionChain）= 某个标的所有可用期权合约
  → 按 行权价 × 到期日 排列

ITM / ATM / OTM
  → In The Money: 行权有利可图（Call: 股价 > 行权价）
  → At  The Money: 行权价 ≈ 现价
  → Out of The Money: 行权暂时不值得（Call: 股价 < 行权价）

  Covered Call 一般卖 OTM（留上涨空间）
  Protective Put 一般买 OTM（低成本保险）
```

---

# 第三部分：学习路线图

## 📚 推荐学习顺序

```
第 1 周：跑通基础 ─────────────────────────
  □ 读完本手册「因子」部分
  □ 在自己的 SMA 策略里加一个动量筛选
  □ 跑回测看结果

第 2 周：多因子 ───────────────────────────
  □ 实现价值 + 动量双因子选股
  □ 学 Z-Score 标准化
  □ 尝试等权 vs 不等权打分

第 3 周：风险控制 ─────────────────────────
  □ 加入波动率仓位控制（高波动时减仓）
  □ 回测最大回撤、夏普比等指标
  □ 对比单因子 vs 多因子的效果

第 4 周：期权入门 ─────────────────────────
  □ 先看懂 Covered Call（最简单）
  □ 在 QuantConnect 跑一遍 Covered Call 回测
  □ 再学 Protective Put 和 Cash-Secured Put

第 5 周+：进阶 ────────────────────────────
  □ Iron Condor / 波动率曲面
  □ 因子择时（不同市场环境用不同因子）
  □ 机器学习 + 因子（XGBoost 特征重要性）
```

## 📖 推荐阅读

| 级别 | 书名 | 关键词 |
|---|---|---|
| 入门 | 《The Little Book That Still Beats the Market》 | 价值投资，简单公式 |
| 入门 | 《A Random Walk Down Wall Street》 | 市场有效假说 |
| 进阶 | 《Quantitative Momentum》 | 动量因子详解 |
| 进阶 | 《Quantitative Value》 | 价值因子详解 |
| 期权 | 《Options as a Strategic Investment》 | 期权百科全书 |
| 期权 | 《Option Volatility and Pricing》 | Greeks 深入 |
| 代码 | QuantConnect Boot Camp | 免费教程，直接上手 |

## 🏷️ 因子速查表

| 因子 | 多空逻辑 | 数据来源 | 典型周期 |
|---|---|---|---|
| 价值 | Long 低 P/E，Short 高 P/E | Fundamental | 年度再平衡 |
| 动量 | Long 过去赢家，Short 输家 | 价格 | 月度再平衡 |
| 质量 | Long 高 ROE+低杠杆 | Fundamental | 季度再平衡 |
| 规模 | Long 小盘，Short 大盘 | 市值 | 年度再平衡 |
| 低波动 | Long 低 Beta | 价格 | 季度再平衡 |
| 成长 | Long 高 EPS Growth | Fundamental | 季度再平衡 |

---

*持续更新中。下一篇：多因子组合策略完整实现。*
