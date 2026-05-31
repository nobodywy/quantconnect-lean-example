# region imports
from AlgorithmImports import *
# endregion

class SmaCrossAlgorithm(QCAlgorithm):
    """
    SMA Crossover Algorithm with Risk Management

    A complete LEAN CLI example demonstrating:
      - Universe selection (dynamic top-N by dollar volume)
      - SMA crossover entry signals (fast/medium/slow)
      - ATR-based position sizing
      - Trailing stop loss
      - Portfolio heat-risk cap
      - Scheduled rebalance
      - Warm-up & history requests
    """

    # ── strategy parameters ──────────────────────────────────────────
    FAST_PERIOD   = 20
    MEDIUM_PERIOD = 50
    SLOW_PERIOD   = 100

    ATR_PERIOD          = 14
    ATR_STOP_MULTIPLIER = 2.0         # trailing stop = entry - N*ATR

    MAX_POSITIONS     = 10            # at most N open positions
    RISK_PER_POSITION = 0.01          # 1 % of portfolio per trade
    HEAT_CAP          = 0.50          # max 50 % of portfolio invested

    # universe filter
    UNIVERSE_COUNT     = 50           # consider top 50 by dollar volume
    MIN_DOLLAR_VOLUME  = 5_000_000    # $5M minimum daily dollar volume
    MAX_MARKET_CAP     = 500_000_000_000  # optional cap filter

    # ── lifecycle ─────────────────────────────────────────────────────
    def Initialize(self) -> None:
        self.SetStartDate(2023, 1, 1)
        self.SetEndDate(2024, 12, 31)
        self.SetCash(100_000)

        # broker / data settings
        self.SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage,
                               AccountType.Margin)
        self.SetWarmUp(TimeSpan.FromDays(self.SLOW_PERIOD + 5))

        # benchmark
        self.SetBenchmark("SPY")

        # ── coarse universe ────────────────────────────────────────
        self.AddUniverse(self.CoarseSelection)
        self.__universe_symbols: List[Symbol] = []

        # schedule weekly rebalance (Mon 10 AM)
        self.Schedule.On(self.DateRules.EveryDay(),
                         self.TimeRules.At(10, 0),
                         self.Rebalance)

        # rolling window to track high-water-mark per symbol
        self.__high_water: Dict[Symbol, float] = {}
        self.__entry_price: Dict[Symbol, float] = {}
        self.__is_invested: Dict[Symbol, bool] = {}

        # plotting
        chart = Chart("Strategy Equity")
        chart.AddSeries(Series("Equity", SeriesType.Line, "$", Color.Blue))
        self.AddChart(chart)

        self.Debug(f"Initialized SmaCrossAlgorithm | "
                   f"Fast={self.FAST_PERIOD} Medium={self.MEDIUM_PERIOD} "
                   f"Slow={self.SLOW_PERIOD}")

    # ── universe selection ────────────────────────────────────────────
    def CoarseSelection(self, coarse: List[CoarseFundamental]) -> List[Symbol]:
        """Dynamic universe: top N by dollar volume, exclude low-liquidity."""
        selected = sorted(
            [c for c in coarse
             if c.HasFundamentalData
             and c.DollarVolume > self.MIN_DOLLAR_VOLUME
             and c.Price > 5],
            key=lambda c: c.DollarVolume,
            reverse=True
        )[:self.UNIVERSE_COUNT]

        self.__universe_symbols = [c.Symbol for c in selected]
        return self.__universe_symbols

    # ── rebalance logic ───────────────────────────────────────────────
    def Rebalance(self) -> None:
        """
        Weekly entry logic:
          1. Compute SMA values via history request.
          2. Enter long positions when fast crosses above medium
             AND medium > slow (bullish alignment).
          3. Size with ATR-based risk.
        """
        if not self.__universe_symbols:
            return

        # ── batch history request ──────────────────────────────────
        history = self.History(
            self.__universe_symbols,
            self.SLOW_PERIOD + 1,
            Resolution.Daily
        )

        if history.empty:
            self.Debug("History is empty; skipping rebalance")
            return

        for symbol in self.__universe_symbols:
            if self.Portfolio[symbol].Invested:
                continue

            # safety check: keep within position cap
            if len([s for s in self.__universe_symbols
                    if self.Portfolio[s].Invested]) >= self.MAX_POSITIONS:
                break

            # price history for this symbol
            try:
                closes = history.loc[symbol]['close'].dropna()
            except (KeyError, AttributeError):
                continue
            if len(closes) < self.SLOW_PERIOD:
                continue

            # ── SMA values ──────────────────────────────────────────
            fast_sma   = closes.rolling(self.FAST_PERIOD).mean().iloc[-1]
            medium_sma = closes.rolling(self.MEDIUM_PERIOD).mean().iloc[-1]
            slow_sma   = closes.rolling(self.SLOW_PERIOD).mean().iloc[-1]

            # entry signal: fast > medium > slow
            if fast_sma <= medium_sma or medium_sma <= slow_sma:
                continue

            # ── ATR for sizing ──────────────────────────────────────
            atr = self._calc_atr(closes)
            if atr is None or atr <= 0:
                continue

            price = closes.iloc[-1]
            size = self._position_size(price, atr)
            if size <= 0:
                continue

            # ── place order ─────────────────────────────────────────
            self.MarketOrder(symbol, size)
            self.__entry_price[symbol] = price
            self.__high_water[symbol] = price

            self.Debug(
                f"ENTRY {symbol.Value} | Price={price:.2f} "
                f"Size={size} | Fast={fast_sma:.2f} "
                f"Med={medium_sma:.2f} Slow={slow_sma:.2f} | ATR={atr:.2f}"
            )

    # ── exit logic (daily check) ──────────────────────────────────────
    def OnData(self, data: Slice) -> None:
        """Trailing stop check on every bar."""
        for symbol, holding in list(self.Portfolio.items()):
            if not holding.Invested or not data.ContainsKey(symbol):
                continue

            price = data[symbol].Close
            entry = self.__entry_price.get(symbol)
            high  = self.__high_water.get(symbol, price)

            if entry is None:
                continue

            # update high-water mark
            if price > high:
                self.__high_water[symbol] = price
                high = price

            # ── ATR trailing stop ───────────────────────────────────
            atr = self._calc_atr_for_symbol(symbol)
            if atr is None:
                continue

            stop_price = high - self.ATR_STOP_MULTIPLIER * atr

            # exit when price drops below trailing stop
            if price <= stop_price:
                self.Liquidate(symbol, tag="TrailingStop")
                self.__entry_price.pop(symbol, None)
                self.__high_water.pop(symbol, None)
                self.Debug(
                    f"EXIT  {symbol.Value} | Price={price:.2f} "
                    f"Stop={stop_price:.2f} | High={high:.2f}"
                )

    # ── helpers ───────────────────────────────────────────────────────
    def _calc_atr(self, closes: pd.Series) -> Optional[float]:
        """Compute ATR from daily close series (simplified)."""
        diffs = closes.diff().abs()
        if len(diffs) < self.ATR_PERIOD:
            return None
        return diffs.rolling(self.ATR_PERIOD).mean().iloc[-1]

    def _calc_atr_for_symbol(self, symbol: Symbol) -> Optional[float]:
        """ATR from recent history for trailing stop."""
        history = self.History(symbol, self.ATR_PERIOD + 1, Resolution.Daily)
        if history.empty or 'close' not in history.columns:
            return None
        return self._calc_atr(history['close'])

    def _position_size(self, price: float, atr: float) -> int:
        """Risk-based sizing: 1 % of portfolio risk per trade."""
        account = self.Portfolio.TotalPortfolioValue
        risk_dollars = account * self.RISK_PER_POSITION

        # heat check
        invested = sum(abs(self.Portfolio[s].HoldingsValue)
                       for s in self.Portfolio.Keys
                       if self.Portfolio[s].Invested)
        if (invested + risk_dollars) / account > self.HEAT_CAP:
            return 0

        # shares = risk_dollars / (ATR * multiplier)
        raw_shares = int(risk_dollars / (atr * self.ATR_STOP_MULTIPLIER))
        return max(raw_shares, 0)

    # ── performance tracking ──────────────────────────────────────────
    def OnEndOfDay(self, symbol: Symbol) -> None:
        self.Plot("Strategy Equity", "Equity",
                  self.Portfolio.TotalPortfolioValue)
