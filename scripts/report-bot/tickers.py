"""
美股 AI 板块收盘汇总 — ticker 配置文件

格式: TICKER = { "name": "中文名", "group": "分组" }
分组: ai_stocks | semiconductors | optical | storage | etfs | benchmarks

增删标的直接改下面字典即可。
"""

WATCHLIST = {
    # ── AI 核心龙头 ─────────────────────────────────────
    "NVDA":  {"name": "NVIDIA",             "group": "ai_stocks"},
    "AVGO":  {"name": "Broadcom",           "group": "ai_stocks"},
    "AMD":   {"name": "AMD",                "group": "ai_stocks"},
    "MSFT":  {"name": "Microsoft",          "group": "ai_stocks"},
    "GOOGL": {"name": "Alphabet",           "group": "ai_stocks"},
    "AMZN":  {"name": "Amazon",             "group": "ai_stocks"},
    "META":  {"name": "Meta",               "group": "ai_stocks"},
    "ORCL":  {"name": "Oracle",             "group": "ai_stocks"},
    "PLTR":  {"name": "Palantir",           "group": "ai_stocks"},
    "ANET":  {"name": "Arista Networks",    "group": "ai_stocks"},

    # ── 半导体 ──────────────────────────────────────────
    "ASML":  {"name": "ASML (光刻机)",       "group": "semiconductors"},
    "QCOM":  {"name": "Qualcomm",           "group": "semiconductors"},
    "TSM":   {"name": "台积电",             "group": "semiconductors"},
    "INTC":  {"name": "Intel",              "group": "semiconductors"},
    "ON":    {"name": "ON Semiconductor",   "group": "semiconductors"},

    # ── 光通信 ──────────────────────────────────────────
    "LITE":  {"name": "Lumentum",           "group": "optical"},
    "CIEN":  {"name": "Ciena",              "group": "optical"},
    "GLW":   {"name": "Corning",            "group": "optical"},
    "COHR":  {"name": "Coherent",           "group": "optical"},

    # ── 存储 / 内存 ─────────────────────────────────────
    "MU":    {"name": "Micron Technology",   "group": "storage"},
    "SNDK":  {"name": "SanDisk",            "group": "storage"},
    "WDC":   {"name": "Western Digital",    "group": "storage"},
    "STX":   {"name": "Seagate",            "group": "storage"},

    # ── ETF ─────────────────────────────────────────────
    "SPY":   {"name": "标普 500 基准",       "group": "benchmarks"},
    "QQQ":   {"name": "纳斯达克 100",        "group": "benchmarks"},
    "SMH":   {"name": "半导体 ETF",          "group": "etfs"},
    "AIQ":   {"name": "AI & 大数据 ETF",     "group": "etfs"},
    "QTUM":  {"name": "量子计算 ETF",        "group": "etfs"},
    "AIPI":  {"name": "AI Covered Call ETF", "group": "etfs"},
    "DRAM":  {"name": "内存 ETF",            "group": "etfs"},
}
