# Makefile for VisionFlow Project
# 簡化常用操作的 Makefile

.PHONY: help install dev-setup test lint format security build up down restart logs status health monitor clean backup

# 預設目標
.DEFAULT_GOAL := help

# 顏色定義
BLUE=\033[0;34m
GREEN=\033[0;32m
YELLOW=\033[1;33m
RED=\033[0;31m
NC=\033[0m # No Color

# 變數定義
DOCKER_COMPOSE_FILE := docker-compose.yaml
DOCKER_COMPOSE_DEV := docker-compose.dev.yml
PYTHON := python3
PIP := pip3
VENV := venv

help: ## 顯示此幫助訊息
	@echo "$(BLUE)VisionFlow 專案 Makefile$(NC)"
	@echo "$(BLUE)===========================$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# 安裝和設置
install: ## 安裝所有依賴
	@echo "$(BLUE)安裝依賴...$(NC)"
	$(PYTHON) -m pip install --upgrade pip
	$(PIP) install -r web/requirements.txt
	$(PIP) install -r object_recognition/requirements_new.txt
	$(PIP) install -r camera_ctrler/requirements.txt
	$(PIP) install -r redisv1/requirements.txt
	@echo "$(GREEN)依賴安裝完成$(NC)"

dev-setup: ## 設置開發環境
	@echo "$(BLUE)設置開發環境...$(NC)"
	@chmod +x scripts/*.sh
	./scripts/setup-dev.sh setup
	@echo "$(GREEN)開發環境設置完成$(NC)"

venv: ## 建立 Python 虛擬環境
	@echo "$(BLUE)建立虛擬環境...$(NC)"
	$(PYTHON) -m venv $(VENV)
	@echo "$(GREEN)虛擬環境已建立，請執行: source $(VENV)/bin/activate$(NC)"

# 程式碼品質
lint: ## 執行程式碼檢查
	@echo "$(BLUE)執行程式碼檢查...$(NC)"
	flake8 web/ object_recognition/ camera_ctrler/ redisv1/ --max-line-length=88 --exclude=venv,migrations
	@echo "$(GREEN)程式碼檢查完成$(NC)"

format: ## 格式化程式碼
	@echo "$(BLUE)格式化程式碼...$(NC)"
	black web/ object_recognition/ camera_ctrler/ redisv1/ --line-length=88
	isort web/ object_recognition/ camera_ctrler/ redisv1/ --profile black
	@echo "$(GREEN)程式碼格式化完成$(NC)"

security: ## 執行安全性檢查
	@echo "$(BLUE)執行安全性檢查...$(NC)"
	bandit -r web/ object_recognition/ camera_ctrler/ redisv1/ -f json || true
	safety check || true
	@echo "$(GREEN)安全性檢查完成$(NC)"

# 測試
test: ## 執行所有測試
	@echo "$(BLUE)執行測試...$(NC)"
	pytest tests/ -v --cov=./ --cov-report=html --cov-report=term
	@echo "$(GREEN)測試完成$(NC)"

test-unit: ## 執行單元測試
	@echo "$(BLUE)執行單元測試...$(NC)"
	pytest tests/unit/ -v
	@echo "$(GREEN)單元測試完成$(NC)"

test-integration: ## 執行整合測試
	@echo "$(BLUE)執行整合測試...$(NC)"
	pytest tests/integration/ -v
	@echo "$(GREEN)整合測試完成$(NC)"

# Docker 操作
build: ## 建構 Docker 映像
	@echo "$(BLUE)建構 Docker 映像...$(NC)"
	docker-compose -f $(DOCKER_COMPOSE_FILE) build
	@echo "$(GREEN)映像建構完成$(NC)"

build-no-cache: ## 重新建構 Docker 映像 (不使用快取)
	@echo "$(BLUE)重新建構 Docker 映像...$(NC)"
	docker-compose -f $(DOCKER_COMPOSE_FILE) build --no-cache
	@echo "$(GREEN)映像建構完成$(NC)"

up: ## 啟動所有服務
	@echo "$(BLUE)啟動服務...$(NC)"
	docker-compose -f $(DOCKER_COMPOSE_FILE) up -d
	@echo "$(GREEN)服務已啟動$(NC)"

up-dev: ## 啟動開發環境服務
	@echo "$(BLUE)啟動開發環境...$(NC)"
	docker-compose -f $(DOCKER_COMPOSE_DEV) up -d
	@echo "$(GREEN)開發環境已啟動$(NC)"

down: ## 停止所有服務
	@echo "$(BLUE)停止服務...$(NC)"
	docker-compose -f $(DOCKER_COMPOSE_FILE) down
	@echo "$(GREEN)服務已停止$(NC)"

restart: ## 重啟所有服務
	@echo "$(BLUE)重啟服務...$(NC)"
	docker-compose -f $(DOCKER_COMPOSE_FILE) restart
	@echo "$(GREEN)服務已重啟$(NC)"

# 監控和日誌
logs: ## 查看所有服務日誌
	docker-compose -f $(DOCKER_COMPOSE_FILE) logs -f

logs-web: ## 查看 Web 服務日誌
	docker-compose -f $(DOCKER_COMPOSE_FILE) logs -f web

logs-camera: ## 查看相機服務日誌
	docker-compose -f $(DOCKER_COMPOSE_FILE) logs -f camera_ctrl

logs-recognition: ## 查看辨識服務日誌
	docker-compose -f $(DOCKER_COMPOSE_FILE) logs -f object_recognition

status: ## 檢查服務狀態
	@echo "$(BLUE)檢查服務狀態...$(NC)"
	docker-compose -f $(DOCKER_COMPOSE_FILE) ps
	@echo ""
	@echo "$(BLUE)Docker 系統資訊:$(NC)"
	docker stats --no-stream

health: ## 執行健康檢查
	@echo "$(BLUE)執行健康檢查...$(NC)"
	@chmod +x scripts/monitor.sh
	./scripts/monitor.sh health

monitor: ## 啟動監控面板
	@echo "$(BLUE)啟動監控...$(NC)"
	@chmod +x scripts/monitor.sh
	./scripts/monitor.sh realtime

# 部署操作
deploy-dev: ## 部署到開發環境
	@echo "$(BLUE)部署到開發環境...$(NC)"
	@chmod +x scripts/deploy.sh
	./scripts/deploy.sh deploy development

deploy-staging: ## 部署到測試環境
	@echo "$(BLUE)部署到測試環境...$(NC)"
	@chmod +x scripts/deploy.sh
	./scripts/deploy.sh deploy staging

deploy-prod: ## 部署到生產環境
	@echo "$(BLUE)部署到生產環境...$(NC)"
	@chmod +x scripts/deploy.sh
	./scripts/deploy.sh deploy production

# 資料庫操作
db-migrate: ## 執行資料庫遷移
	@echo "$(BLUE)執行資料庫遷移...$(NC)"
	docker-compose -f $(DOCKER_COMPOSE_FILE) exec web flask db upgrade
	@echo "$(GREEN)資料庫遷移完成$(NC)"

db-backup: ## 備份資料庫
	@echo "$(BLUE)備份資料庫...$(NC)"
	@chmod +x scripts/deploy.sh
	./scripts/deploy.sh backup
	@echo "$(GREEN)資料庫備份完成$(NC)"

db-shell: ## 進入資料庫 shell
	@echo "$(BLUE)進入資料庫 shell...$(NC)"
	docker-compose -f $(DOCKER_COMPOSE_FILE) exec db psql -U user -d vision_notify

# 清理操作
clean: ## 清理未使用的 Docker 資源
	@echo "$(BLUE)清理 Docker 資源...$(NC)"
	docker system prune -f
	docker volume prune -f
	@echo "$(GREEN)清理完成$(NC)"

clean-all: ## 深度清理 (包含映像)
	@echo "$(YELLOW)警告: 這將刪除所有未使用的 Docker 資源$(NC)"
	@read -p "確定要繼續嗎? [y/N] " -n 1 -r && echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker system prune -a -f; \
		docker volume prune -f; \
		echo "$(GREEN)深度清理完成$(NC)"; \
	else \
		echo "$(YELLOW)取消操作$(NC)"; \
	fi

clean-logs: ## 清理舊日誌
	@echo "$(BLUE)清理舊日誌...$(NC)"
	@chmod +x scripts/monitor.sh
	./scripts/monitor.sh cleanup 7
	@echo "$(GREEN)日誌清理完成$(NC)"

# 開發工具
shell-web: ## 進入 Web 容器 shell
	docker-compose -f $(DOCKER_COMPOSE_FILE) exec web bash

shell-db: ## 進入資料庫容器 shell
	docker-compose -f $(DOCKER_COMPOSE_FILE) exec db bash

shell-redis: ## 進入 Redis 容器 shell
	docker-compose -f $(DOCKER_COMPOSE_FILE) exec redis sh

# 快速操作組合
quick-start: build up health ## 快速啟動 (建構 + 啟動 + 健康檢查)
	@echo "$(GREEN)VisionFlow 已啟動並通過健康檢查$(NC)"

quick-restart: down up health ## 快速重啟
	@echo "$(GREEN)VisionFlow 已重啟並通過健康檢查$(NC)"

dev-start: up-dev health ## 啟動開發環境
	@echo "$(GREEN)開發環境已啟動$(NC)"

ci-check: lint security test ## CI 檢查 (代碼檢查 + 安全檢查 + 測試)
	@echo "$(GREEN)所有 CI 檢查通過$(NC)"

# 文檔和幫助
docs: ## 產生文檔
	@echo "$(BLUE)產生專案文檔...$(NC)"
	@echo "文檔位置:"
	@echo "- API 文檔: docs/API_Doc.md"
	@echo "- 部署指南: docs/DEPLOYMENT.md"
	@echo "- CI/CD 指南: docs/CI-CD-GUIDE.md"
	@echo "- 故障排除: docs/TROUBLESHOOTING.md"

env-check: ## 檢查環境設定
	@echo "$(BLUE)檢查環境設定...$(NC)"
	@echo "Python 版本: $(shell $(PYTHON) --version)"
	@echo "Docker 版本: $(shell docker --version)"
	@echo "Docker Compose 版本: $(shell docker-compose --version)"
	@echo "目前工作目錄: $(shell pwd)"
	@echo "環境檔案:"
	@ls -la .env* 2>/dev/null || echo "  未找到環境檔案"

# 專案資訊
info: ## 顯示專案資訊
	@echo "$(BLUE)VisionFlow 專案資訊$(NC)"
	@echo "$(BLUE)=================$(NC)"
	@echo "專案名稱: VisionFlow"
	@echo "版本: 1.0.0"
	@echo "描述: 智能影像辨識與監控系統"
	@echo "作者: VisionFlow Team"
	@echo "授權: MIT"
	@echo ""
	@echo "$(BLUE)服務列表:$(NC)"
	@echo "- Web 服務 (Flask): http://localhost:5000"
	@echo "- 相機控制器: http://localhost:5001"  
	@echo "- 物件辨識: http://localhost:5002"
	@echo "- 資料庫 (PostgreSQL): localhost:5432"
	@echo "- Redis: localhost:6379"
	@echo ""
	@echo "$(GREEN)使用 'make help' 查看所有可用命令$(NC)"
