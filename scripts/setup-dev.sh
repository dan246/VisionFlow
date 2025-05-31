#!/bin/bash

# VisionFlow 本地開發環境設置腳本
# 此腳本用於快速設置本地開發環境

set -e  # 遇到錯誤時退出

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# 檢查必要工具
check_prerequisites() {
    log_info "檢查系統必要工具..."
    
    local missing_tools=()
    
    # 檢查 Docker
    if ! command -v docker &> /dev/null; then
        missing_tools+=("docker")
    fi
    
    # 檢查 Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        missing_tools+=("docker-compose")
    fi
    
    # 檢查 Python
    if ! command -v python3 &> /dev/null; then
        missing_tools+=("python3")
    fi
    
    # 檢查 Git
    if ! command -v git &> /dev/null; then
        missing_tools+=("git")
    fi
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "缺少必要工具: ${missing_tools[*]}"
        echo "請先安裝這些工具後再運行此腳本"
        exit 1
    fi
    
    log_success "所有必要工具已安裝"
}

# 設置 Python 虛擬環境
setup_python_env() {
    log_info "設置 Python 虛擬環境..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        log_success "Python 虛擬環境已建立"
    else
        log_warning "Python 虛擬環境已存在"
    fi
    
    # 啟用虛擬環境
    source venv/bin/activate
    
    # 更新 pip
    pip install --upgrade pip
    
    # 安裝開發依賴
    log_info "安裝開發依賴..."
    pip install black isort flake8 pytest pytest-cov pre-commit safety bandit
    
    log_success "Python 環境設置完成"
}

# 安裝專案依賴
install_dependencies() {
    log_info "安裝專案依賴..."
    
    # 為每個服務安裝依賴
    for service in web object_recognition camera_ctrler redisv1; do
        if [ -d "$service" ] && [ -f "$service/requirements.txt" ]; then
            log_info "安裝 $service 服務依賴..."
            pip install -r "$service/requirements.txt"
        fi
        
        if [ -d "$service" ] && [ -f "$service/requirements_new.txt" ]; then
            log_info "安裝 $service 服務新依賴..."
            pip install -r "$service/requirements_new.txt"
        fi
    done
    
    log_success "所有依賴安裝完成"
}

# 設置環境檔案
setup_env_files() {
    log_info "設置環境檔案..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log_success "環境檔案已從範例建立"
        else
            log_warning "找不到 .env.example 檔案"
        fi
    else
        log_warning ".env 檔案已存在"
    fi
}

# 設置 Git hooks
setup_git_hooks() {
    log_info "設置 Git hooks..."
    
    if [ -f ".pre-commit-config.yaml" ]; then
        pre-commit install
        log_success "Pre-commit hooks 已安裝"
    else
        log_warning "找不到 pre-commit 配置檔案"
    fi
}

# 建立開發用資料庫和 Redis
setup_dev_services() {
    log_info "啟動開發用服務..."
    
    # 建立開發用 docker-compose 檔案
    cat > docker-compose.dev.yml << EOF
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: dev_user
      POSTGRES_PASSWORD: dev_pass
      POSTGRES_DB: visionflow_dev
    ports:
      - "5432:5432"
    volumes:
      - postgres_dev_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_dev_data:/data

volumes:
  postgres_dev_data:
  redis_dev_data:
EOF

    # 啟動服務
    docker-compose -f docker-compose.dev.yml up -d
    
    log_success "開發用服務已啟動"
}

# 運行測試
run_tests() {
    log_info "運行程式碼品質檢查..."
    
    # 程式碼格式檢查
    if command -v black &> /dev/null; then
        black --check --diff .
    fi
    
    # 程式碼風格檢查
    if command -v flake8 &> /dev/null; then
        flake8 . --count --statistics --max-line-length=88
    fi
    
    # 安全檢查
    if command -v bandit &> /dev/null; then
        bandit -r . -f json || true
    fi
    
    log_success "程式碼品質檢查完成"
}

# 清理函數
cleanup() {
    log_info "清理開發環境..."
    
    # 停止開發服務
    if [ -f "docker-compose.dev.yml" ]; then
        docker-compose -f docker-compose.dev.yml down
    fi
    
    log_success "清理完成"
}

# 顯示使用說明
show_usage() {
    echo "使用方式: $0 [選項]"
    echo ""
    echo "選項:"
    echo "  setup     設置完整的開發環境"
    echo "  test      運行程式碼品質檢查"
    echo "  clean     清理開發環境"
    echo "  help      顯示此說明"
    echo ""
}

# 主函數
main() {
    case "${1:-setup}" in
        setup)
            log_info "開始設置 VisionFlow 開發環境..."
            check_prerequisites
            setup_python_env
            install_dependencies
            setup_env_files
            setup_git_hooks
            setup_dev_services
            run_tests
            log_success "VisionFlow 開發環境設置完成！"
            ;;
        test)
            run_tests
            ;;
        clean)
            cleanup
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            log_error "未知選項: $1"
            show_usage
            exit 1
            ;;
    esac
}

# 捕獲中斷信號
trap cleanup EXIT

# 執行主函數
main "$@"
