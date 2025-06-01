#!/bin/bash

# VisionFlow 智能監控系統 - 增強版部署腳本
# 完全容器化部署，宿主機無需安裝任何套件

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 項目配置
PROJECT_NAME="VisionFlow"
COMPOSE_FILE="docker-compose.optimized.yaml"
ENV_FILE=".env"

# 功能函數
print_header() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║            🎯 VisionFlow 智能監控系統 - 增強版                ║"
    echo "║                                                              ║"
    echo "║              完全容器化部署 | 現代化界面 | AI 分析             ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] ✅ $1${NC}"
}

print_info() {
    echo -e "${CYAN}[$(date '+%H:%M:%S')] ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] ⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] ❌ $1${NC}"
}

# 檢查依賴
check_dependencies() {
    print_info "檢查系統依賴..."
    
    # 檢查 Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安裝，請先安裝 Docker"
        echo "安裝指令: curl -fsSL https://get.docker.com | sh"
        exit 1
    fi
    
    # 檢查 Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose 未安裝，請先安裝 Docker Compose"
        exit 1
    fi
    
    # 檢查 Docker 服務狀態
    if ! docker info &> /dev/null; then
        print_error "Docker 服務未運行，請啟動 Docker 服務"
        exit 1
    fi
    
    print_step "系統依賴檢查完成"
}

# 創建環境配置
create_env_file() {
    print_info "創建環境配置檔案..."
    
    if [ ! -f "$ENV_FILE" ]; then
        cat > "$ENV_FILE" << EOF
# VisionFlow 智能監控系統 - 環境配置

# === 資料庫配置 ===
POSTGRES_USER=visionflow_user
POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
POSTGRES_DB=visionflow_db
DB_PORT=5432

# === Redis 配置 ===
REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
REDIS_PORT=6379

# === Flask 配置 ===
FLASK_ENV=production
FLASK_DEBUG=false
SECRET_KEY=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-50)
BACKEND_PORT=5000

# === Gunicorn 配置 ===
GUNICORN_WORKERS=4
GUNICORN_TIMEOUT=120
GUNICORN_KEEPALIVE=5
GUNICORN_MAX_REQUESTS=1000
GUNICORN_MAX_REQUESTS_JITTER=100

# === 攝影機控制器配置 ===
CAMERA_FETCH_INTERVAL=0.1
CAMERA_TIMEOUT=30
CAMERA_WORKER_THREADS=4
CAMERA_GUNICORN_WORKERS=4
CAMERA_WORKER_CONNECTIONS=1000

# === 物件辨識配置 ===
MODEL1_ENABLED=true
MODEL2_ENABLED=false
MODEL3_ENABLED=false
PROCESSING_SLEEP_INTERVAL=0.1
OBJECT_RECOGNITION_MAX_WORKERS=4
BATCH_SIZE=1
GPU_ENABLED=false
OBJECT_RECOGNITION_MEMORY_LIMIT=2G
OBJECT_RECOGNITION_MEMORY_RESERVATION=512M

# === Redis Worker 配置 ===
NUM_REDIS_WORKERS=3
RECONNECT_INTERVAL=30
FRAME_FETCH_INTERVAL=0.1
MAX_CONCURRENT_CAMERAS=10

# === 儲存配置 ===
ENABLE_IMAGE_SAVING=true
ENABLE_FILE_STORAGE=false

# === 通知配置 ===
ENABLE_EMAIL_NOTIFICATIONS=false
ENABLE_LINE_NOTIFICATIONS=false

# === 日誌配置 ===
LOG_LEVEL=INFO
ENABLE_FILE_LOGGING=true

# === 外部服務配置 ===
HUGGINGFACE_TOKEN=
DATASET_NAME=

# === CORS 配置 ===
CORS_ORIGINS=*
EOF
        print_step "環境配置檔案已創建"
    else
        print_info "環境配置檔案已存在，跳過創建"
    fi
}

# 創建必要目錄
create_directories() {
    print_info "創建必要目錄..."
    
    directories=(
        "db"
        "web/logs"
        "camera_ctrler/logs"
        "camera_ctrler/images"
        "object_recognition/logs"
        "object_recognition/saved_images"
        "redisv1/logs"
        "redisv1/storage"
        "AImodels/object_recognition/model"
        "AImodels/object_recognition/tmp"
    )
    
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_info "已創建目錄: $dir"
        fi
    done
    
    print_step "目錄創建完成"
}

# 檢查端口
check_ports() {
    print_info "檢查端口可用性..."
    
    ports=(5000 5432 6379 15440)
    
    for port in "${ports[@]}"; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            print_warning "端口 $port 已被佔用"
            read -p "是否繼續部署? (y/n): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                print_error "部署已取消"
                exit 1
            fi
        fi
    done
    
    print_step "端口檢查完成"
}

# 構建映像檔
build_images() {
    print_info "構建 Docker 映像檔..."
    
    echo -e "${PURPLE}正在構建映像檔，這可能需要幾分鐘時間...${NC}"
    
    if docker-compose -f "$COMPOSE_FILE" build --no-cache; then
        print_step "映像檔構建完成"
    else
        print_error "映像檔構建失敗"
        exit 1
    fi
}

# 啟動服務
start_services() {
    print_info "啟動 VisionFlow 服務..."
    
    echo -e "${PURPLE}正在啟動所有服務...${NC}"
    
    if docker-compose -f "$COMPOSE_FILE" up -d; then
        print_step "服務啟動完成"
    else
        print_error "服務啟動失敗"
        exit 1
    fi
}

# 等待服務就緒
wait_for_services() {
    print_info "等待服務就緒..."
    
    services=("db" "redis" "backend")
    
    for service in "${services[@]}"; do
        print_info "等待 $service 服務啟動..."
        timeout=60
        while [ $timeout -gt 0 ]; do
            if docker-compose -f "$COMPOSE_FILE" exec -T "$service" echo "OK" >/dev/null 2>&1; then
                print_step "$service 服務已就緒"
                break
            fi
            sleep 2
            timeout=$((timeout - 2))
        done
        
        if [ $timeout -eq 0 ]; then
            print_warning "$service 服務啟動超時，但繼續部署"
        fi
    done
}

# 初始化資料庫
init_database() {
    print_info "初始化資料庫..."
    
    if docker-compose -f "$COMPOSE_FILE" exec -T backend python -c "
from app import app
from extensions import db
with app.app_context():
    db.create_all()
    print('Database initialized successfully')
" 2>/dev/null; then
        print_step "資料庫初始化完成"
    else
        print_warning "資料庫初始化失敗，但服務可能仍可正常運行"
    fi
}

# 顯示部署資訊
show_deployment_info() {
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║              🎉 VisionFlow 部署成功！                        ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    echo -e "${CYAN}📋 服務訪問資訊:${NC}"
    echo -e "   🌐 主要界面:     http://localhost:5000"
    echo -e "   📊 現代化儀表板: http://localhost:5000/advanced-dashboard"
    echo -e "   🎛️  攝影機控制:   http://localhost:15440"
    echo -e "   💾 資料庫:       postgresql://localhost:5432"
    echo -e "   🔄 Redis:        redis://localhost:6379"
    echo ""
    
    echo -e "${CYAN}🔧 管理指令:${NC}"
    echo -e "   📊 查看狀態:     docker-compose -f $COMPOSE_FILE ps"
    echo -e "   📜 查看日誌:     docker-compose -f $COMPOSE_FILE logs -f [service]"
    echo -e "   ⏹️  停止服務:     docker-compose -f $COMPOSE_FILE down"
    echo -e "   🔄 重啟服務:     docker-compose -f $COMPOSE_FILE restart"
    echo -e "   🧹 清理資源:     docker-compose -f $COMPOSE_FILE down -v --rmi all"
    echo ""
    
    echo -e "${CYAN}📝 默認帳戶 (如果啟用):${NC}"
    echo -e "   👤 使用者名稱:   admin"
    echo -e "   🔑 密碼:         admin123"
    echo ""
    
    echo -e "${YELLOW}⚠️  重要提醒:${NC}"
    echo -e "   • 首次啟動可能需要數分鐘來初始化所有服務"
    echo -e "   • 請確保所有服務都處於健康狀態後再使用"
    echo -e "   • 環境變數已保存在 .env 檔案中，請妥善保管"
    echo -e "   • 建議定期備份資料庫和配置檔案"
}

# 檢查服務狀態
check_service_status() {
    print_info "檢查服務運行狀態..."
    
    echo -e "${CYAN}當前服務狀態:${NC}"
    docker-compose -f "$COMPOSE_FILE" ps
    
    echo -e "\n${CYAN}服務健康檢查:${NC}"
    
    # 檢查 Web 服務
    if curl -s http://localhost:5000/health/health >/dev/null 2>&1; then
        echo -e "   ✅ Web 服務: ${GREEN}正常${NC}"
    else
        echo -e "   ❌ Web 服務: ${RED}異常${NC}"
    fi
    
    # 檢查資料庫
    if docker-compose -f "$COMPOSE_FILE" exec -T db pg_isready >/dev/null 2>&1; then
        echo -e "   ✅ 資料庫: ${GREEN}正常${NC}"
    else
        echo -e "   ❌ 資料庫: ${RED}異常${NC}"
    fi
    
    # 檢查 Redis
    if docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping >/dev/null 2>&1; then
        echo -e "   ✅ Redis: ${GREEN}正常${NC}"
    else
        echo -e "   ❌ Redis: ${RED}異常${NC}"
    fi
}

# 主函數
main() {
    case "${1:-deploy}" in
        "deploy")
            print_header
            check_dependencies
            create_env_file
            create_directories
            check_ports
            build_images
            start_services
            wait_for_services
            init_database
            show_deployment_info
            check_service_status
            ;;
        "start")
            print_info "啟動 VisionFlow 服務..."
            docker-compose -f "$COMPOSE_FILE" up -d
            check_service_status
            ;;
        "stop")
            print_info "停止 VisionFlow 服務..."
            docker-compose -f "$COMPOSE_FILE" down
            ;;
        "restart")
            print_info "重啟 VisionFlow 服務..."
            docker-compose -f "$COMPOSE_FILE" restart
            check_service_status
            ;;
        "status")
            check_service_status
            ;;
        "logs")
            service=${2:-}
            if [ -n "$service" ]; then
                docker-compose -f "$COMPOSE_FILE" logs -f "$service"
            else
                docker-compose -f "$COMPOSE_FILE" logs -f
            fi
            ;;
        "clean")
            print_warning "這將刪除所有容器、映像檔和資料卷"
            read -p "確定要繼續嗎? (y/n): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                docker-compose -f "$COMPOSE_FILE" down -v --rmi all
                print_step "清理完成"
            fi
            ;;
        "update")
            print_info "更新 VisionFlow 系統..."
            docker-compose -f "$COMPOSE_FILE" pull
            docker-compose -f "$COMPOSE_FILE" up -d --force-recreate
            check_service_status
            ;;
        *)
            echo "VisionFlow 智能監控系統 - 部署腳本"
            echo ""
            echo "用法: $0 [指令]"
            echo ""
            echo "可用指令:"
            echo "  deploy    - 完整部署系統 (默認)"
            echo "  start     - 啟動服務"
            echo "  stop      - 停止服務"
            echo "  restart   - 重啟服務"
            echo "  status    - 查看服務狀態"
            echo "  logs      - 查看日誌 (可指定服務名稱)"
            echo "  clean     - 清理所有資源"
            echo "  update    - 更新系統"
            echo ""
            echo "範例:"
            echo "  $0 deploy          # 完整部署"
            echo "  $0 logs backend    # 查看後端日誌"
            echo "  $0 status          # 查看服務狀態"
            ;;
    esac
}

# 執行主函數
main "$@"
