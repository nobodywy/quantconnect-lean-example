#!/usr/bin/env bash
#
# download-data.sh — QuantConnect LEAN CLI 批量数据下载脚本
# ===================================================================
# 用法:
#   ./download-data.sh [选项] [分组名...]
#
# 选项:
#   -d, --dry-run     只打印将要执行的操作，不实际下载
#   -p, --parallel N  并行下载数 (默认读取 tickers.conf 中的 PARALLEL)
#   -f, --force       强制重新下载已存在的数据
#   -h, --help        显示帮助
#
# 分组名 (可选，不指定则下载全部):
#   benchmarks, ai_leaders, semiconductors, optical, storage,
#   ai_apps, ai_etfs, all
#
# 示例:
#   ./download-data.sh                           # 下载全部
#   ./download-data.sh optical semiconductors    # 只下载光通信+半导体
#   ./download-data.sh --dry-run all             # 预览所有操作
#   ./download-data.sh -p 1 ai_leaders           # 单线程下载 AI 龙头
#
# 依赖:
#   - lean CLI (pip install lean)
#   - lean login (需先登录 QuantConnect)
# ===================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONF_FILE="$SCRIPT_DIR/tickers.conf"
DATA_DIR="$(cd "$SCRIPT_DIR/.." && pwd)/data"

# ── 颜色 ───────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ── 默认值 ─────────────────────────────────────────
DRY_RUN=false
FORCE=false
PARALLEL=2
GROUPS=()

# ── 加载配置 ───────────────────────────────────────
if [[ -f "$CONF_FILE" ]]; then
  source "$CONF_FILE"
  PARALLEL=${PARALLEL:-2}
else
  echo -e "${RED}[ERROR]${NC} 配置文件不存在: $CONF_FILE"
  exit 1
fi

# ── 分组定义 ───────────────────────────────────────
declare -A GROUP_TICKERS
GROUP_TICKERS[benchmarks]="$BENCHMARKS"
GROUP_TICKERS[ai_leaders]="$AI_LEADERS"
GROUP_TICKERS[semiconductors]="$SEMICONDUCTORS"
GROUP_TICKERS[optical]="$OPTICAL"
GROUP_TICKERS[storage]="$STORAGE"
GROUP_TICKERS[ai_apps]="$AI_APPS"
GROUP_TICKERS[ai_etfs]="$AI_ETFS"

ALL_GROUPS="benchmarks ai_leaders semiconductors optical storage ai_apps ai_etfs"

# ── 参数解析 ───────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    -d|--dry-run) DRY_RUN=true; shift ;;
    -f|--force)   FORCE=true; shift ;;
    -p|--parallel) PARALLEL="$2"; shift 2 ;;
    -h|--help)
      head -30 "$0" | tail -18
      exit 0
      ;;
    all) GROUPS=($ALL_GROUPS); shift ;;
    *)
      if [[ -n "${GROUP_TICKERS[$1]:-}" ]]; then
        GROUPS+=("$1")
      else
        echo -e "${YELLOW}[WARN]${NC} 未知分组: $1 (已跳过)"
      fi
      shift
      ;;
  esac
done

# 默认全部
if [[ ${#GROUPS[@]} -eq 0 ]]; then
  GROUPS=($ALL_GROUPS)
fi

# ── 检查 lean CLI ──────────────────────────────────
if ! command -v lean &>/dev/null; then
  echo -e "${RED}[ERROR]${NC} 未找到 lean CLI，请先安装: pip install lean"
  exit 1
fi

# ── 摘要 ───────────────────────────────────────────
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  QuantConnect 数据下载工具${NC}"
echo -e "${BLUE}============================================${NC}"
echo -e "  数据集:     ${GREEN}$DATASET${NC}"
echo -e "  日期区间:   ${GREEN}$START_DATE → $END_DATE${NC}"
echo -e "  数据目录:   ${GREEN}$DATA_DIR${NC}"
echo -e "  下载分组:   ${GREEN}${GROUPS[*]}${NC}"
echo -e "  并行数:     ${GREEN}$PARALLEL${NC}"
echo -e "  Dry-run:    ${YELLOW}$DRY_RUN${NC}"
echo -e "  Force:      ${YELLOW}$FORCE${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# ── 统计 ──────────────────────────────────────────
TOTAL_TICKERS=0
for group in "${GROUPS[@]}"; do
  for ticker in ${GROUP_TICKERS[$group]}; do
    TOTAL_TICKERS=$((TOTAL_TICKERS + 1))
  done
done
echo -e "待下载: ${GREEN}$TOTAL_TICKERS${NC} 个标的\n"

# ── 下载函数 ──────────────────────────────────────
download_ticker() {
  local ticker="$1"
  local dataset="$2"
  local start="$3"
  local end="$4"
  local data_dir="$5"
  local force="$6"

  local cmd="lean data download"
  cmd="$cmd --dataset \"$dataset\""
  cmd="$cmd --ticker $ticker"
  cmd="$cmd --start $start"
  cmd="$cmd --end $end"
  cmd="$cmd --data-folder \"$data_dir\""

  if $DRY_RUN; then
    echo -e "  ${YELLOW}[DRY-RUN]${NC} $ticker"
    return 0
  fi

  # 跳过已存在（可 force 覆盖）
  local ticker_dir="$data_dir/equity/usa/daily/${ticker,,}"
  if ! $force && [[ -d "$ticker_dir" ]] && ls "$ticker_dir"/*.zip &>/dev/null; then
    echo -e "  ${GREEN}[SKIP]${NC}  $ticker (已下载)"
    return 0
  fi

  echo -e "  ${BLUE}[DOWNLOAD]${NC} $ticker ..."
  if eval "$cmd" &>/dev/null; then
    echo -e "  ${GREEN}[OK]${NC}    $ticker"
    return 0
  else
    echo -e "  ${RED}[FAIL]${NC}  $ticker (可重试或跳过)"
    return 1
  fi
}

# ── 构建下载队列 ──────────────────────────────────
QUEUE=()
for group in "${GROUPS[@]}"; do
  for ticker in ${GROUP_TICKERS[$group]}; do
    QUEUE+=("$ticker")
  done
done

# ── 并行执行 ──────────────────────────────────────
FAIL_COUNT=0
RUNNING=0
INDEX=0

while [[ $INDEX -lt ${#QUEUE[@]} ]]; do
  # 控制并行数
  while [[ $RUNNING -ge $PARALLEL ]]; do
    wait -n 2>/dev/null || true
    RUNNING=$((RUNNING - 1))
  done

  ticker="${QUEUE[$INDEX]}"
  download_ticker "$ticker" "$DATASET" "$START_DATE" "$END_DATE" "$DATA_DIR" "$FORCE" &
  RUNNING=$((RUNNING + 1))
  INDEX=$((INDEX + 1))

  # 短暂间隔避免 API 限频
  sleep 0.5
done

# 等待剩余任务
wait

# ── 完成 ──────────────────────────────────────────
echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "  ${GREEN}下载完成！${NC}"
echo -e "  数据目录: ${GREEN}$DATA_DIR${NC}"
echo ""
echo -e "  下一步:"
echo -e "    lean backtest algorithms/SmaCrossAlgorithm.py"
echo -e "    lean report"
echo -e "${BLUE}============================================${NC}"
