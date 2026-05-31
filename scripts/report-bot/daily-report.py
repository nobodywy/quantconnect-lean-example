#!/usr/bin/env python3
"""
美股 AI 板块每日收盘报告生成器

用法:
  python3 scripts/report-bot/daily-report.py              # 输出到终端
  python3 scripts/report-bot/daily-report.py --save       # 保存到 reports/
  python3 scripts/report-bot/daily-report.py --today 2026-05-30  # 指定日期

依赖:
  pip install yfinance pandas numpy

在 macOS 上设置定时:
  # 编辑 crontab: crontab -e
  # 美股收盘后运行（16:30 ET = 4:30 AM UTC+8 = 20:30 UTC）
  30 20 * * 1-5 cd ~/quantconnect-lean-example && python3 scripts/report-bot/daily-report.py --save
"""

import sys
import os
import json
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path

try:
    import yfinance as yf
    import pandas as pd
    import numpy as np
except ImportError:
    print("❌ 缺少依赖，请先安装:")
    print("   pip install yfinance pandas numpy")
    sys.exit(1)

# ── 配置 ─────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent.parent
REPORT_DIR = ROOT / "reports"
TICKERS_MODULE = ROOT / "scripts" / "report-bot" / "tickers.py"

# SMA 周期
SMA_PERIODS = [20, 50, 200]

# ── 加载 ticker 配置 ──────────────────────────────────
import importlib.util
spec = importlib.util.spec_from_file_location("tickers", TICKERS_MODULE)
tickers_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tickers_mod)
WATCHLIST = tickers_mod.WATCHLIST

# ── 工具函数 ──────────────────────────────────────────

def emoji_for_change(pct):
    """根据涨跌幅返回 emoji"""
    if pct > 5:   return "🔥"
    if pct > 2:   return "🟢"
    if pct > 0:   return "🟢"
    if pct > -2:  return "🔴"
    if pct > -5:  return "🔴"
    return  "🩸"


def format_price(val):
    """智能格式化价格"""
    if pd.isna(val):
        return "—"
    return f"${val:,.2f}"


def format_pct(val):
    """格式化百分比"""
    if pd.isna(val):
        return "—"
    sign = "+" if val > 0 else ""
    return f"{sign}{val:+.2f}%"


def compute_smas(df, periods):
    """计算 SMA 值"""
    result = {}
    for p in periods:
        if len(df) >= p:
            result[p] = df['Close'].rolling(p).mean().iloc[-1]
        else:
            result[p] = None
    return result


def compute_volume_ratio(df):
    """当日成交量 vs 20日均量"""
    if len(df) < 22:
        return None
    today_vol = df['Volume'].iloc[-1]
    avg_vol = df['Volume'].rolling(20).mean().iloc[-2]  # 不含当日
    if avg_vol > 0:
        return today_vol / avg_vol
    return None


# ── 主逻辑 ─────────────────────────────────────────────

def fetch_all(tickers_meta, end_date=None):
    """批量拉取数据"""
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")

    # 拉足够多数据用于 SMA 200
    start_date = (datetime.strptime(end_date, "%Y-%m-%d")
                  - timedelta(days=300)).strftime("%Y-%m-%d")

    symbols = list(tickers_meta.keys())

    print(f"📡 拉取 {len(symbols)} 只标的数据 ({start_date} → {end_date}) ...")
    data = yf.download(
        symbols,
        start=start_date,
        end=end_date,
        progress=False,
        auto_adjust=True
    )

    return data, end_date


def build_report(data, end_date):
    """生成报告"""
    lines = []
    lines.append(f"# 🇺🇸 美股 AI 板块收盘报告")
    lines.append(f"**{end_date}**  (生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')})")
    lines.append("")

    # ── 大盘概览 ────────────────────────────────────
    spy_pct = None
    qqq_pct = None
    lines.append("## 📊 大盘基准")
    lines.append("")
    lines.append("| 标的 | 收盘价 | 日涨跌 | SMA 20 | SMA 50 | SMA 200 | 量比 | 趋势 |")
    lines.append("|------|--------|--------|--------|--------|---------|------|------|")

    for sym in ["SPY", "QQQ"]:
        try:
            df = data['Close'][sym].dropna()
            row = build_stock_row(sym, data, df)
            lines.append(row)
            if sym == "SPY" and df is not None:
                spy_pct = (df.iloc[-1] / df.iloc[-2] - 1) * 100
            if sym == "QQQ" and df is not None:
                qqq_pct = (df.iloc[-1] / df.iloc[-2] - 1) * 100
        except KeyError:
            lines.append(f"| {sym} | — | — | — | — | — | — | — |")

    lines.append("")

    # ── 各组板块 ────────────────────────────────────
    groups = {
        "ai_stocks":      ("🧠 AI 核心龙头", []),
        "semiconductors": ("🔬 半导体", []),
        "optical":        ("📡 光通信", []),
        "storage":        ("💾 存储", []),
        "etfs":           ("📦 AI / 半导体 ETF", []),
    }

    for sym, meta in WATCHLIST.items():
        group = meta['group']
        if group in groups:
            groups[group][1].append(sym)

    for key, (title, syms) in groups.items():
        if not syms:
            continue
        lines.append(f"## {title}")
        lines.append("")
        lines.append("| 代码 | 名称 | 收盘价 | 日涨跌 | SMA 20 | SMA 50 | SMA 200 | 量比 |")
        lines.append("|------|------|--------|--------|--------|--------|---------|------|")

        for sym in syms:
            try:
                df = data['Close'][sym].dropna()
                row = build_stock_row(sym, data, df, table_mode="sector")
                lines.append(row)
            except KeyError:
                name = WATCHLIST.get(sym, {}).get('name', sym)
                lines.append(f"| {sym} | {name} | — | — | — | — | — | — |")

        lines.append("")

    # ── 日内强弱榜 ──────────────────────────────────
    lines.append("## 🏆 日内涨跌排名")
    lines.append("")
    lines.append("### 涨幅 TOP 5")
    lines.append("")
    gains = []
    for sym in WATCHLIST:
        try:
            df = data['Close'][sym].dropna()
            pct = (df.iloc[-1] / df.iloc[-2] - 1) * 100
            gains.append((sym, WATCHLIST[sym]['name'], pct))
        except (KeyError, IndexError):
            continue
    gains.sort(key=lambda x: x[2], reverse=True)

    for i, (sym, name, pct) in enumerate(gains[:5]):
        emoji = emoji_for_change(pct)
        lines.append(f"{i+1}. {emoji} **{sym}** ({name}): {format_pct(pct)}")

    lines.append("")
    lines.append("### 跌幅 TOP 5")
    lines.append("")
    for i, (sym, name, pct) in enumerate(gains[-5:]):
        emoji = emoji_for_change(pct)
        lines.append(f"{i+1}. {emoji} **{sym}** ({name}): {format_pct(pct)}")

    lines.append("")

    # ── 信号提示 ─────────────────────────────────────
    lines.append("## ⚡ 技术信号")
    lines.append("")
    signals = []

    for sym in WATCHLIST:
        try:
            df = data['Close'][sym].dropna()
            if len(df) < 200:
                continue
            close = df.iloc[-1]
            prev_close = df.iloc[-2]
            smas = compute_smas(df, SMA_PERIODS)
            sma20, sma50, sma200 = smas.get(20), smas.get(50), smas.get(200)

            if sma20 and sma50 and sma200:
                if close > sma20 > sma50:
                    # 短期强势
                    if sma20 > sma200 and close > sma200:
                        signals.append((sym, WATCHLIST[sym]['name'], "🟢 多头排列", "strong"))
                if close < sma20 < sma50 and sma50 < sma200:
                    signals.append((sym, WATCHLIST[sym]['name'], "🔴 空头排列", "weak"))

            # 量比异常
            vol_ratio = compute_volume_ratio(data['Volume'][sym].dropna()
                                             if 'Volume' in data.columns
                                             else None)
            if vol_ratio is None:
                try:
                    vol_df = data['Volume'][sym].dropna()
                    vol_ratio = compute_volume_ratio(vol_df)
                except (KeyError, AttributeError):
                    pass

            if vol_ratio and vol_ratio > 2.0:
                signals.append((sym, WATCHLIST[sym]['name'],
                              f"📈 爆量 {vol_ratio:.1f}×", "volume"))
        except (KeyError, IndexError):
            continue

    if signals:
        for sym, name, signal, _ in signals[:15]:
            lines.append(f"- **{sym}** ({name}): {signal}")
    else:
        lines.append("- 暂无显著信号")

    lines.append("")
    lines.append("---")
    lines.append(f"*由 daily-report.py 自动生成 · 数据来源: Yahoo Finance*")
    lines.append("")
    lines.append("*⚠️ 仅供研究参考，不构成投资建议*")

    return "\n".join(lines)


def build_stock_row(sym, data, closes, table_mode="full"):
    """构造单行数据"""
    name = WATCHLIST.get(sym, {}).get('name', sym)

    if closes is None or len(closes) < 2:
        return f"| {sym} | {name} | — | — | — | — | — | — | — |"

    close = closes.iloc[-1]
    prev_close = closes.iloc[-2] if len(closes) >= 2 else close
    change_pct = (close / prev_close - 1) * 100
    emoji = emoji_for_change(change_pct)

    smas = compute_smas(closes, SMA_PERIODS)
    sma20_str = format_price(smas[20])
    sma50_str = format_price(smas[50])
    sma200_str = format_price(smas[200])

    # 趋势方向
    trend = ""
    if smas[200] and close > smas[200]:
        trend = "🟢 线上"
    elif smas[200]:
        trend = "🔴 线下"
    else:
        trend = "—"

    vol_ratio_str = "—"
    try:
        vol_df = data['Volume'][sym].dropna()
        vol_ratio = compute_volume_ratio(vol_df)
        if vol_ratio:
            vol_ratio_str = f"{vol_ratio:.1f}×"
    except (KeyError, AttributeError):
        pass

    if table_mode == "full":
        return (f"| {emoji} {sym} | {name} | {format_price(close)} "
                f"| {format_pct(change_pct)} | {sma20_str} | {sma50_str} "
                f"| {sma200_str} | {vol_ratio_str} | {trend} |")
    else:
        return (f"| {emoji} {sym} | {name} | {format_price(close)} "
                f"| {format_pct(change_pct)} | {sma20_str} | {sma50_str} "
                f"| {sma200_str} | {vol_ratio_str} |")


# ── 入口 ──────────────────────────────────────────────

def main():
    save = "--save" in sys.argv
    end_date = None

    for i, arg in enumerate(sys.argv):
        if arg == "--today" and i + 1 < len(sys.argv):
            end_date = sys.argv[i + 1]

    data, end_date = fetch_all(WATCHLIST, end_date)
    report = build_report(data, end_date)

    print(report)

    if save:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        fname = f"report-{end_date}.md"
        fpath = REPORT_DIR / fname
        fpath.write_text(report)
        print(f"\n💾 已保存: {fpath}")


if __name__ == "__main__":
    main()
