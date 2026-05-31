# ===================================================================
# QuantConnect AI 板块数据管理 Makefile
# ===================================================================
# 用法:
#   make download           # 下载全部 AI 板块数据
#   make download-optical   # 仅光通信
#   make download-semicon   # 仅半导体
#   make download-storage   # 仅存储
#   make download-ai        # 仅 AI 龙头
#   make download-etfs      # 仅 ETF
#   make report             # 生成本日收盘报告
#   make report-save        # 生成本日报告并保存
#   make dry-run            # 预览所有操作
#   make dry-run            # 预览所有操作
#   make info               # 显示数据状态
#   make clean              # 删除本地数据
#   make help               # 显示此帮助
# ===================================================================

SCRIPT  := ./scripts/download-data.sh
DATA    := ./data

.PHONY: help download dry-run info clean \
        download-optical download-semicon download-storage \
        download-ai download-etfs download-bench \
        report report-save install-report-deps

help:
	@head -18 Makefile

help:
	@head -18 Makefile

# ── 一键下载全部 ──────────────────────────────────
download:
	@chmod +x $(SCRIPT)
	@$(SCRIPT) all

download-all: download

# ── 按板块下载 ─────────────────────────────────────
download-optical:
	@chmod +x $(SCRIPT)
	@$(SCRIPT) optical

download-semicon:
	@chmod +x $(SCRIPT)
	@$(SCRIPT) semiconductors

download-storage:
	@chmod +x $(SCRIPT)
	@$(SCRIPT) storage

download-ai:
	@chmod +x $(SCRIPT)
	@$(SCRIPT) ai_leaders ai_apps

download-etfs:
	@chmod +x $(SCRIPT)
	@$(SCRIPT) ai_etfs benchmarks

download-bench:
	@chmod +x $(SCRIPT)
	@$(SCRIPT) benchmarks

# ── 预览 ───────────────────────────────────────────
dry-run:
	@chmod +x $(SCRIPT)
	@$(SCRIPT) --dry-run all

# ── 数据状态 ───────────────────────────────────────
info:
	@echo "============================================"
	@echo "  本地数据状态"
	@echo "============================================"
	@if [ -d "$(DATA)/equity/usa/daily" ]; then \
		count=$$(find $(DATA)/equity/usa/daily -name "*.zip" 2>/dev/null | wc -l); \
		size=$$(du -sh $(DATA) 2>/dev/null | cut -f1); \
		echo "  日线数据文件: $$count 个"; \
		echo "  数据总大小:   $$size"; \
		echo ""; \
		echo "  已下载标的:"; \
		find $(DATA)/equity/usa/daily -mindepth 1 -maxdepth 1 -type d 2>/dev/null | while read d; do \
			count=$$(ls "$$d"/*.zip 2>/dev/null | wc -l); \
			echo "    $$(basename $$d | tr '[:lower:]' '[:upper:]') ($$count 文件)"; \
		done; \
	else \
		echo "  ❌ 暂无本地数据，请先运行 make download"; \
	fi
	@echo "============================================"

# ── 清理 ──────────────────────────────────────────
clean:
	@echo "⚠️  即将删除所有本地数据: $(DATA)/equity/"
	@read -p "确认? [y/N] " yn; \
	case $$yn in \
		[Yy]* ) rm -rf $(DATA)/equity/ $(DATA)/forex/ $(DATA)/crypto/ $(DATA)/future/ $(DATA)/option/ $(DATA)/alternative/; \
		         echo "✅ 已清理";; \
		* ) echo "已取消";; \
	esac

# ── 收盘报告 ──────────────────────────────────────
install-report-deps:
	@pip install yfinance pandas numpy

report:
	@python3 scripts/report-bot/daily-report.py

report-save:
	@python3 scripts/report-bot/daily-report.py --save
	@echo "📁 报告已保存到 reports/"
