#!/bin/bash

# VisionFlow 部署腳本
# 支援多環境部署（開發、測試、生產）

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
DEFAULT_ENV="development"
DOCKER_COMPOSE_FILE="docker-compose.yaml"
ENV_FILE=".env"

# 日誌函數
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 檢查 Docker 環境
check_docker() {
    log_info "檢查 Docker 環境..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安裝"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安裝"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker 服務未運行"
        exit 1
    fi
    
    log_success "Docker 環境檢查通過"
}

# 檢查環境檔案
check_env_file() {
    local env=$1
    
    log_info "檢查環境配置檔案..."
    
    case $env in
        development)
            ENV_FILE=".env.dev"
            ;;
        staging)
            ENV_FILE=".env.staging"
            ;;
        production)
            ENV_FILE=".env.prod"
            ;;
        *)
            ENV_FILE=".env"
            ;;
    esac
    
    if [ ! -f "$ENV_FILE" ]; then
        log_warning "環境檔案 $ENV_FILE 不存在"
        if [ -f ".env.example" ]; then
            log_info "從範例建立環境檔案..."
            cp .env.example "$ENV_FILE"
            log_warning "請編輯 $ENV_FILE 設定正確的環境變數"
        else
            log_error "找不到環境範例檔案"
            exit 1
        fi
    fi
    
    log_success "環境檔案檢查完成"
}

# 拉取最新映像
pull_images() {
    log_info "拉取最新 Docker 映像..."
    
    docker-compose -f "$DOCKER_COMPOSE_FILE" --env-file "$ENV_FILE" pull
    
    log_success "映像拉取完成"
}

# 備份資料庫
backup_database() {
    log_info "備份資料庫..."
    
    local backup_dir="backups"
    local backup_file="$backup_dir/db_backup_$(date +%Y%m%d_%H%M%S).sql"
    
    mkdir -p "$backup_dir"
    
    # 檢查是否有運行中的資料庫容器
    if docker-compose -f "$DOCKER_COMPOSE_FILE" ps db | grep -q "Up"; then
        docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T db pg_dump -U user vision_notify > "$backup_file"
        log_success "資料庫備份完成: $backup_file"
    else
        log_warning "資料庫容器未運行，跳過備份"
    fi
}

# 部署應用
deploy() {
    local env=$1
    local no_backup=$2
    
    log_info "開始部署 VisionFlow ($env 環境)..."
    
    # 檢查環境
    check_docker
    check_env_file "$env"
    
    # 備份（生產環境）
    if [ "$env" = "production" ] && [ "$no_backup" != "true" ]; then
        backup_database
    fi
    
    # 拉取映像
    pull_images
    
    # 停止舊容器
    log_info "停止舊容器..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" --env-file "$ENV_FILE" down
    
    # 啟動新容器
    log_info "啟動新容器..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" --env-file "$ENV_FILE" up -d
    
    # 等待服務啟動
    log_info "等待服務啟動..."
    sleep 30
    
    # 健康檢查
    health_check
    
    log_success "VisionFlow 部署完成！"
}

# 健康檢查
health_check() {
    log_info "執行健康檢查..."
    
    local services=("web:5000" "camera_ctrl:5000" "object_recognition:5000")
    local all_healthy=true
    
    for service_port in "${services[@]}"; do
        local service=$(echo "$service_port" | cut -d: -f1)
        local port=$(echo "$service_port" | cut -d: -f2)
        
        log_info "檢查 $service 服務..."
        
        # 檢查容器狀態
        if ! docker-compose -f "$DOCKER_COMPOSE_FILE" ps "$service" | grep -q "Up"; then
            log_error "$service 容器未運行"
            all_healthy=false
            continue
        fi
        
        # 檢查服務回應
        local retries=0
        local max_retries=5
        while [ $retries -lt $max_retries ]; do
            if curl -f "http://localhost:$port/health" &> /dev/null; then
                log_success "$service 服務健康"
                break
            else
                retries=$((retries + 1))
                if [ $retries -eq $max_retries ]; then
                    log_error "$service 服務健康檢查失敗"
                    all_healthy=false
                else
                    log_warning "$service 服務暫未回應，重試中... ($retries/$max_retries)"
                    sleep 10
                fi
            fi
        done
    done
    
    if [ "$all_healthy" = true ]; then
        log_success "所有服務健康檢查通過"
    else
        log_error "部分服務健康檢查失敗"
        show_logs
        exit 1
    fi
}

# 顯示日誌
show_logs() {
    log_info "顯示服務日誌..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" logs --tail=50
}

# 停止服務
stop() {
    log_info "停止 VisionFlow 服務..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" down
    log_success "服務已停止"
}

# 重啟服務
restart() {
    local env=${1:-$DEFAULT_ENV}
    log_info "重啟 VisionFlow 服務..."
    stop
    deploy "$env" "true"
}

# 檢查狀態
status() {
    log_info "檢查 VisionFlow 服務狀態..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" ps
}

# 清理資源
cleanup() {
    log_info "清理未使用的 Docker 資源..."
    
    # 清理停止的容器
    docker container prune -f
    
    # 清理未使用的映像
    docker image prune -f
    
    # 清理未使用的網路
    docker network prune -f
    
    # 清理未使用的卷（謹慎使用）
    read -p "是否清理未使用的卷？這可能會刪除資料 (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker volume prune -f
    fi
    
    log_success "清理完成"
}

# 顯示使用說明
show_usage() {
    echo "VisionFlow 部署腳本"
    echo ""
    echo "使用方式: $0 [命令] [選項]"
    echo ""
    echo "命令:"
    echo "  deploy [env]     部署應用 (env: development|staging|production)"
    echo "  restart [env]    重啟應用"
    echo "  stop            停止應用"
    echo "  status          檢查服務狀態"
    echo "  logs            顯示服務日誌"
    echo "  health          執行健康檢查"
    echo "  backup          備份資料庫"
    echo "  cleanup         清理 Docker 資源"
    echo "  help            顯示此說明"
    echo ""
    echo "選項:"
    echo "  --no-backup     部署時跳過備份"
    echo ""
    echo "範例:"
    echo "  $0 deploy production"
    echo "  $0 restart staging"
    echo "  $0 deploy production --no-backup"
    echo ""
}

# 主函數
main() {
    local command=${1:-deploy}
    local env=${2:-$DEFAULT_ENV}
    local no_backup=false
    
    # 解析選項
    for arg in "$@"; do
        case $arg in
            --no-backup)
                no_backup=true
                shift
                ;;
        esac
    done
    
    case $command in
        deploy)
            deploy "$env" "$no_backup"
            ;;
        restart)
            restart "$env"
            ;;
        stop)
            stop
            ;;
        status)
            status
            ;;
        logs)
            show_logs
            ;;
        health)
            health_check
            ;;
        backup)
            backup_database
            ;;
        cleanup)
            cleanup
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            log_error "未知命令: $command"
            show_usage
            exit 1
            ;;
    esac
}

# 執行主函數
main "$@"
