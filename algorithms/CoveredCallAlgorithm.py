# region imports
from AlgorithmImports import *
# endregion

class CoveredCallAlgorithm(QCAlgorithm):
    """
    Covered Call Strategy — 持仓 + 卖 OTM Call 收权利金

    逻辑:
      1. 持有底层股票（默认 NVDA）
      2. 每周卖出虚值（OTM）看涨期权，行权价高于现价 5%
      3. 到期未行权 → 白赚权利金
      4. 被行权 → 卖掉股票（锁定利润），等待下次入场机会重新买回
    """

    # ── 参数 ───────────────────────────────────────────
    TICKER           = "NVDA"       # 底层标的
    OTM_PCT           = 0.05        # 卖出的 Call 行权价高出现价 5%
    MIN_DTE           = 7           # 最少还有 7 天到期
    MAX_DTE           = 35          # 最多 35 天到期
    OPERATION_DAY     = 1           # 每周二操作 (Monday=0)
    POSITION_PCT      = 0.95        # 95% 资金买股票，留 5% 现金

    def Initialize(self) -> None:
        self.SetStartDate(2024, 1, 1)
        self.SetEndDate(2025, 12, 31)
        self.SetCash(100_000)

        # 底层股票
        self.equity = self.AddEquity(self.TICKER, Resolution.Minute)
        self.SetBenchmark(self.TICKER)

        # 期权
        option = self.AddOption(self.TICKER, Resolution.Minute)
        option.SetFilter(self.OptionFilter)

        self.option_symbol = option.Symbol

        # 状态
        self._call_sold = False

        self.Debug(f"Covered Call initialized | {self.TICKER} | "
                   f"OTM={self.OTM_PCT*100:.0f}%")

    def OptionFilter(self, universe: OptionFilterUniverse) -> OptionFilterUniverse:
        """只选 OTM Call，7~35 天到期"""
        return universe.IncludeWeeklys() \
                       .Strikes(+5, +15) \
                       .Expiration(self.MIN_DTE, self.MAX_DTE) \
                       .CallsOnly()

    def OnData(self, data: Slice) -> None:
        # ── 建仓：买股票 ────────────────────────────
        if not self.Portfolio[self.TICKER].Invested:
            price = self.Securities[self.TICKER].Price
            qty = int((self.Portfolio.Cash * self.POSITION_PCT)
                      / price)
            if qty > 0:
                self.MarketOrder(self.TICKER, qty)
                self.Debug(f"BUY {qty} shares of {self.TICKER} @ ${price:.2f}")
            return

        # ── 每周操作日 ───────────────────────────────
        if self.Time.weekday() != self.OPERATION_DAY:
            return

        # ── 检查是否有期权到期，腾出状态 ─────────────
        has_option = False
        for symbol, holding in list(self.Portfolio.items()):
            if (holding.Invested
                and symbol.SecurityType == SecurityType.Option):
                has_option = True
                # 检查是否到期
                expiry = symbol.ID.Date
                if self.Time.date() >= expiry:
                    self.Debug(f"Option {symbol.Value} expired")
                    # 期权过期自动清零，状态恢复
                    self._call_sold = False
                    has_option = False

        if has_option:
            return  # 还有未到期期权，不动

        # ── 卖出新的 Covered Call ───────────────────
        price = self.Securities[self.TICKER].Price

        if data.OptionChains.TryGetValue(self.option_symbol,
                                         out var chain):
            # 选 OTM Call
            target_strike = price * (1 + self.OTM_PCT)
            calls = [c for c in chain
                     if c.Right == OptionRight.Call
                     and c.Strike >= target_strike]

            if not calls:
                return

            # 选离目标行权价最近、到期日最远的（权利金更丰厚）
            best = sorted(
                calls,
                key=lambda c: (abs(c.Strike - target_strike), -c.Expiry.timestamp())
            )[0]

            # 卖 1 张（对应 100 股底层）
            # 注意：实际中应为 持股数 ÷ 100 张
            self.Sell(best.Symbol, 1)
            self._call_sold = True

            self.Debug(
                f"SELL COVERED CALL | Strike=${best.Strike:.2f} "
                f"Premium=${best.AskPrice:.2f} "
                f"Expiry={best.Expiry:%Y-%m-%d} | "
                f"Stock=${price:.2f}"
            )

    def OnOrderEvent(self, orderEvent: OrderEvent) -> None:
        """监控订单成交"""
        if orderEvent.Status == OrderStatus.Filled:
            if orderEvent.Ticket.OrderType == OrderType.OptionExercise:
                self.Debug(
                    f"OPTION ASSIGNED | {orderEvent.Symbol} "
                    f"Qty={orderEvent.FillQuantity}"
                )
                # 股票被行权卖出后，下次 OnData 会自动检测
                # 到没有持仓，然后重新买入
                self._call_sold = False

    def OnEndOfDay(self, symbol: Symbol) -> None:
        if symbol.Value == self.TICKER:
            self.Plot("Covered Call", "Portfolio Value",
                      self.Portfolio.TotalPortfolioValue)
