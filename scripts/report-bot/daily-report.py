#!/usr/bin/env python3
"""
美股 AI 板块收盘报告 — 纯标准库版 (OpenClaw sandbox 原生可用)

零 pip 依赖 · Python 3 stdlib only
数据源: Yahoo Finance chart API (免 key, 免注册)

用法:
  python3 daily-report.py              # 完整 Markdown 报告
  python3 daily-report.py --tickers NVDA,SPY,LITE   # 只看指定标的

OpenClaw cron 集成:
  在项目配置中添加 cron，美股收盘后触发，脚本输出 → feishu 消息发送
"""

import sys
import json
import math
import time
import urllib.request
from datetime import datetime, timedelta

# ── 配置 ─────────────────────────────────────────────

WATCHLIST = {
    # 大盘基准
    "SPY":  {"name": "标普 500",         "group": "benchmarks"},
    "QQQ":  {"name": "纳斯达克 100",     "group": "benchmarks"},

    # AI 核心龙头
    "NVDA": {"name": "NVIDIA",           "group": "ai"},
    "AVGO": {"name": "Broadcom",         "group": "ai"},
    "AMD":  {"name": "AMD",              "group": "ai"},
    "MSFT": {"name": "Microsoft",        "group": "ai"},
    "GOOGL":{"name": "Alphabet",         "group": "ai"},
    "AMZN": {"name": "Amazon",           "group": "ai"},
    "META": {"name": "Meta",             "group": "ai"},
    "ORCL": {"name": "Oracle",           "group": "ai"},
    "PLTR": {"name": "Palantir",         "group": "ai"},
    "ANET": {"name": "Arista",           "group": "ai"},

    # 半导体
    "ASML": {"name": "ASML 光刻机",      "group": "semi"},
    "QCOM": {"name": "Qualcomm",         "group": "semi"},
    "TSM":  {"name": "台积电",           "group": "semi"},
    "INTC": {"name": "Intel",            "group": "semi"},
    "ON":   {"name": "ON Semi",          "group": "semi"},

    # 光通信
    "LITE": {"name": "Lumentum",         "group": "optical"},
    "CIEN": {"name": "Ciena",            "group": "optical"},
    "GLW":  {"name": "Corning",          "group": "optical"},
    "COHR": {"name": "Coherent",         "group": "optical"},

    # 存储
    "MU":   {"name": "Micron",           "group": "storage"},
    "SNDK": {"name": "SanDisk",          "group": "storage"},
    "WDC":  {"name": "WD",               "group": "storage"},
    "STX":  {"name": "Seagate",          "group": "storage"},

    # AI ETF
    "SMH":  {"name": "半导体 ETF",       "group": "etfs"},
    "AIQ":  {"name": "AI 大数据 ETF",    "group": "etfs"},
    "QTUM": {"name": "量子计算 ETF",     "group": "etfs"},
    "AIPI": {"name": "AI 备兑 ETF",      "group": "etfs"},
}

SMA_PERIODS = [20, 50, 200]
YAHOO_API = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=1y&interval=1d"
UA = "Mozilla/5.0 (compatible; OpenClaw/1.0)"


# ── 数据获取 (Yahoo Finance chart API) ────────────────

def fetch(ticker):
    """拉取 1 年日线，返回 { closes, opens, highs, lows, volumes, timestamps }"""
    url = YAHOO_API.format(ticker=ticker)
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                                "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            d = json.loads(resp.read().decode())
    except Exception as e:
        print(f"  ⚠️ {ticker}: 请求失败 — {e}", file=sys.stderr)
        return None

    result = (d.get("chart", {}).get("result") or [None])[0]
    if not result:
        print(f"  ⚠️ {ticker}: 无数据", file=sys.stderr)
        return None

    meta = result.get("meta", {})
    quotes = (result.get("indicators", {}).get("quote") or [None])[0]
    if not quotes:
        return None

    closes = [v for v in (quotes.get("close") or []) if v is not None]
    if len(closes) < 2:
        return None

    return {
        "closes": closes,
        "opens":  quotes.get("open") or [],
        "highs":  quotes.get("high") or [],
        "lows":   quotes.get("low") or [],
        "volumes": quotes.get("volume") or [],
        "timestamps": result.get("timestamp") or [],
        "meta_price": meta.get("regularMarketPrice"),
        "meta_prev_close": meta.get("chartPreviousClose"),
    }


# ── 指标计算 ─────────────────────────────────────────

def sma(values, period):
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def compute(data):
    """从原始数据计算所有指标"""
    closes = data["closes"]
    volumes = data["volumes"]

    close = closes[-1]
    prev_close = closes[-2] if len(closes) >= 2 else close
    change_pct = ((close - prev_close) / prev_close) * 100 if prev_close > 0 else 0

    sma20  = sma(closes, 20)
    sma50  = sma(closes, 50)
    sma200 = sma(closes, 200)

    # 量比: 今日 / 20日均量
    vol_today = volumes[-1] if volumes and volumes[-1] else 0
    vol_ratio = None
    valid_vols = [v for v in volumes[-21:-1] if v and v > 0]
    if valid_vols and vol_today > 0:
        avg_vol = sum(valid_vols) / len(valid_vols)
        vol_ratio = vol_today / avg_vol if avg_vol > 0 else None

    # 趋势
    trend = "unknown"
    if sma200:
        trend = "above" if close > sma200 else "below"

    return {
        "close": close,
        "prev_close": prev_close,
        "open": data["opens"][-1] if data["opens"] else None,
        "high": data["highs"][-1] if data["highs"] else None,
        "low":  data["lows"][-1]  if data["lows"]  else None,
        "volume": vol_today,
        "sma20":  round(sma20, 2)  if sma20  else None,
        "sma50":  round(sma50, 2)  if sma50  else None,
        "sma200": round(sma200, 2) if sma200 else None,
        "change_pct": round(change_pct, 2),
        "vol_ratio": round(vol_ratio, 1) if vol_ratio else None,
        "trend": trend,
    }


# ── 格式化 ───────────────────────────────────────────

def fp(v):     return f"${v:,.2f}" if v is not None else "—"
def fpct(v):   return f"{'+' if v >= 0 else ''}{v:.2f}%" if v is not None else "—"
def fr(v):     return f"{v:.1f}×" if v is not None else "—"

def emoji(pct):
    if pct is None:  return "⚪"
    if pct > 5:      return "🔥"
    if pct > 2:      return "🟢"
    if pct > 0:      return "🟢"
    if pct > -2:     return "🔴"
    if pct > -5:     return "🔴"
    return "🩸"

def trend_label(m):
    t = (m or {}).get("trend")
    if t == "above": return "🟢 线上"
    if t == "below": return "🔴 线下"
    return "—"


# ── 信号检测 ─────────────────────────────────────────

def signals(sym, name, m):
    if not m:
        return []
    sigs = []
    c, s20, s50, s200, vr = m["close"], m["sma20"], m["sma50"], m["sma200"], m["vol_ratio"]
    pc = m["prev_close"]

    if c and s20 and s50 and s200:
        if c > s20 > s50 > s200:
            sigs.append("🟢 完美多头")
        elif c < s20 < s50 < s200:
            sigs.append("🔴 完美空头")
        elif s20 > s200 and c > s200 and s20 > s50:
            sigs.append("🟢 短期偏多")
        elif s20 < s200 and c < s200 and s20 < s50:
            sigs.append("🔴 短期偏空")
    if s200 and c:
        if c > s200 and pc <= s200:
            sigs.append("⬆️ 突破 200 日线")
        elif c < s200 and pc >= s200:
            sigs.append("⬇️ 跌破 200 日线")
    if vr and vr > 2.0:
        sigs.append(f"📈 爆量 {vr:.1f}×")
    return sigs


# ── 报告生成 ─────────────────────────────────────────

GROUPS = [
    ("📊 大盘风向",     "benchmarks"),
    ("🧠 AI 核心龙头",  "ai"),
    ("🔬 半导体 & 上游", "semi"),
    ("📡 光通信",       "optical"),
    ("💾 存储 & 内存",   "storage"),
    ("📦 AI / 半导体 ETF", "etfs"),
]


def build_report(date_str, results):
    out = []
    out.append(f"# 🇺🇸 美股 AI 板块收盘报告")
    out.append(f"**{date_str}** · {datetime.utcnow().strftime('%H:%M UTC')}")
    out.append("")

    for title, group_key in GROUPS:
        members = [(s, m) for s, m in WATCHLIST.items() if m["group"] == group_key]
        if not members:
            continue
        out.append(f"## {title}")
        out.append("")
        out.append("| 代码 | 名称 | 收盘 | 涨跌 | SMA20 | SMA50 | SMA200 | 趋势 |")
        out.append("|------|------|------|------|-------|-------|--------|------|")
        for sym, meta in members:
            m = results.get(sym)
            if m:
                out.append(
                    f"| {emoji(m['change_pct'])} {sym} "
                    f"| {meta['name']} "
                    f"| {fp(m['close'])} "
                    f"| {fpct(m['change_pct'])} "
                    f"| {fp(m['sma20'])} "
                    f"| {fp(m['sma50'])} "
                    f"| {fp(m['sma200'])} "
                    f"| {trend_label(m)} |"
                )
            else:
                out.append(f"| {sym} | {meta['name']} | — | — | — | — | — | — |")
        out.append("")

    # 排名
    ranked = []
    for sym, m in results.items():
        if m and m["change_pct"] is not None:
            ranked.append((sym, WATCHLIST.get(sym, {}).get("name", sym),
                          m["change_pct"], m["close"]))
    ranked.sort(key=lambda x: x[2], reverse=True)

    out.append("## 🏆 日内排名")
    out.append("")
    out.append("**🔥 涨幅 TOP 5**")
    for i, (sym, name, pct, close) in enumerate(ranked[:5], 1):
        out.append(f"{i}. {emoji(pct)} **{sym}** ({name})　{fpct(pct)}　→ {fp(close)}")
    out.append("")
    out.append("**⚠️ 跌幅 TOP 5**")
    for i, (sym, name, pct, close) in enumerate(ranked[-5:][::-1], 1):
        out.append(f"{i}. {emoji(pct)} **{sym}** ({name})　{fpct(pct)}　→ {fp(close)}")
    out.append("")

    # 信号
    all_sigs = []
    for sym, m in results.items():
        name = WATCHLIST.get(sym, {}).get("name", sym)
        for s in signals(sym, name, m):
            all_sigs.append((sym, name, s))
    out.append("## ⚡ 技术信号")
    out.append("")
    if all_sigs:
        for sym, name, sig in all_sigs:
            out.append(f"- **{sym}** ({name}): {sig}")
    else:
        out.append("- 今日暂无显著信号")

    out.append("")
    out.append("---")
    out.append(f"*Yahoo Finance · 自动生成 · {len(results)}/{len(WATCHLIST)} 只 · 仅供参考*")
    return "\n".join(out)


# ── 主流程 ───────────────────────────────────────────

def main():
    tickers_arg = next((a.split("=")[1] for a in sys.argv
                        if a.startswith("--tickers=")), None)
    symbols = [t.strip().upper() for t in tickers_arg.split(",")] \
              if tickers_arg else list(WATCHLIST.keys())

    print(f"📡 拉取 {len(symbols)} 只标的数据...", file=sys.stderr)
    results = {}
    for i, ticker in enumerate(symbols):
        print(f"  [{i+1}/{len(symbols)}] {ticker}...", file=sys.stderr)
        data = fetch(ticker)
        if data:
            m = compute(data)
            if m:
                results[ticker] = m
        if i < len(symbols) - 1:
            time.sleep(0.3)

    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    print(f"✅ {len(results)}/{len(symbols)} 成功", file=sys.stderr)
    print(build_report(date_str, results))


if __name__ == "__main__":
    main()
