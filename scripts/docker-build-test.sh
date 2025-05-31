#!/bin/bash

# Docker 建構診斷腳本
# 用於診斷和修復 VisionFlow Docker 建構問題

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# 服務配置
SERVICES=(
    "web:Dockerfile:web"
    "camera-ctrl:cameractrlDockerfile:camera_ctrler"
    "object-recognition:objectrecognitionDockerfile:object_recognition"
    "redis-worker:rtsptestDockerfile:redisv1"
)

# 檢查 Docker 環境
check_docker_environment() {
    log_info "檢查 Docker 環境..."
    
    # 檢查 Docker 是否安裝
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安裝"
        exit 1
    fi
    
    # 檢查 Docker 服務是否運行
    if ! docker info &> /dev/null; then
        log_error "Docker 服務未運行"
        exit 1
    fi
    
    # 顯示 Docker 版本
    log_info "Docker 版本: $(docker --version)"
    log_info "Docker Compose 版本: $(docker-compose --version 2>/dev/null || echo 'N/A')"
    
    # 檢查 Docker 磁碟空間
    local disk_usage=$(docker system df --format "table {{.Type}}\t{{.TotalCount}}\t{{.Size}}\t{{.Reclaimable}}")
    log_info "Docker 磁碟使用情況:"
    echo "$disk_usage"
    
    log_success "Docker 環境檢查完成"
}

# 清理 Docker 環境
cleanup_docker() {
    log_info "清理 Docker 環境..."
    
    # 停止所有運行的容器
    local running_containers=$(docker ps -q)
    if [ ! -z "$running_containers" ]; then
        docker stop $running_containers || true
    fi
    
    # 清理未使用的資源
    docker system prune -f
    docker volume prune -f
    
    log_success "Docker 環境清理完成"
}

# 預拉取基底映像
pull_base_images() {
    log_info "預拉取基底映像..."
    
    local base_images=(
        "python:3.11-slim"
        "python:3.11-alpine"
        "redis:7-alpine"
        "postgres:15"
    )
    
    for image in "${base_images[@]}"; do
        log_info "拉取 $image..."
        if docker pull "$image"; then
            log_success "成功拉取 $image"
        else
            log_warning "無法拉取 $image，建構時可能會失敗"
        fi
    done
}

# 測試單個服務建構
test_service_build() {
    local service_name=$1
    local dockerfile=$2
    local context=$3
    
    log_info "測試建構 $service_name..."
    
    # 檢查 Dockerfile 是否存在
    if [ ! -f "$context/$dockerfile" ]; then
        log_error "Dockerfile 不存在: $context/$dockerfile"
        return 1
    fi
    
    # 檢查 requirements.txt 是否存在（對於 Python 服務）
    if [ ! -f "$context/requirements.txt" ] && [ ! -f "$context/requirements_new.txt" ]; then
        log_warning "$context 沒有 requirements.txt 文件"
    fi
    
    # 嘗試建構映像
    local image_tag="visionflow-test/$service_name:$(date +%s)"
    
    log_info "建構映像: $image_tag"
    if docker build -t "$image_tag" -f "$context/$dockerfile" "$context"; then
        log_success "$service_name 建構成功"
        
        # 簡單測試映像
        log_info "測試映像 $image_tag..."
        if docker run --rm "$image_tag" python --version &> /dev/null; then
            log_success "$service_name 映像測試通過"
        else
            log_warning "$service_name 映像測試失敗，但建構成功"
        fi
        
        # 清理測試映像
        docker rmi "$image_tag" || true
        return 0
    else
        log_error "$service_name 建構失敗"
        return 1
    fi
}

# 測試 Alpine 版本建構
test_alpine_build() {
    log_info "測試 Alpine 版本建構..."
    
    if [ -f "web/Dockerfile.alpine" ]; then
        if test_service_build "web-alpine" "Dockerfile.alpine" "web"; then
            log_success "Alpine 版本建構成功"
        else
            log_error "Alpine 版本建構失敗"
        fi
    else
        log_warning "未找到 Alpine Dockerfile"
    fi
}

# 網路連線測試
test_network_connectivity() {
    log_info "測試網路連線..."
    
    local test_urls=(
        "https://registry-1.docker.io"
        "https://archive.ubuntu.com"
        "https://deb.debian.org"
        "https://pypi.org"
    )
    
    for url in "${test_urls[@]}"; do
        if curl -s --connect-timeout 10 "$url" &> /dev/null; then
            log_success "連接到 $url 成功"
        else
            log_error "無法連接到 $url"
        fi
    done
}

# 診斷建構失敗
diagnose_build_failure() {
    local service_name=$1
    local dockerfile=$2
    local context=$3
    
    log_info "診斷 $service_name 建構失敗..."
    
    # 檢查 Dockerfile 語法
    log_info "檢查 Dockerfile 語法..."
    if docker build --dry-run -f "$context/$dockerfile" "$context" &> /dev/null; then
        log_success "Dockerfile 語法正確"
    else
        log_error "Dockerfile 語法錯誤"
        docker build --dry-run -f "$context/$dockerfile" "$context" || true
    fi
    
    # 檢查依賴文件
    if [ -f "$context/requirements.txt" ]; then
        log_info "檢查 requirements.txt..."
        if python3 -m pip install --dry-run -r "$context/requirements.txt" &> /dev/null; then
            log_success "requirements.txt 格式正確"
        else
            log_warning "requirements.txt 可能有問題"
        fi
    fi
    
    # 建議解決方案
    log_info "建議的解決方案:"
    echo "1. 檢查網路連線"
    echo "2. 更新 Docker"
    echo "3. 清理 Docker 快取"
    echo "4. 嘗試使用不同的基底映像"
    echo "5. 檢查 Dockerfile 中的套件名稱"
}

# 主函數
main() {
    echo "=== VisionFlow Docker 建構診斷工具 ==="
    echo ""
    
    # 解析命令列參數
    case "${1:-all}" in
        "check")
            check_docker_environment
            test_network_connectivity
            ;;
        "clean")
            cleanup_docker
            ;;
        "pull")
            pull_base_images
            ;;
        "test")
            check_docker_environment
            pull_base_images
            
            for service_config in "${SERVICES[@]}"; do
                IFS=':' read -r service_name dockerfile context <<< "$service_config"
                test_service_build "$service_name" "$dockerfile" "$context" || \
                diagnose_build_failure "$service_name" "$dockerfile" "$context"
            done
            
            test_alpine_build
            ;;
        "diagnose")
            check_docker_environment
            test_network_connectivity
            
            for service_config in "${SERVICES[@]}"; do
                IFS=':' read -r service_name dockerfile context <<< "$service_config"
                diagnose_build_failure "$service_name" "$dockerfile" "$context"
            done
            ;;
        "all"|*)
            check_docker_environment
            test_network_connectivity
            pull_base_images
            
            log_info "開始建構所有服務..."
            local failed_services=()
            
            for service_config in "${SERVICES[@]}"; do
                IFS=':' read -r service_name dockerfile context <<< "$service_config"
                if ! test_service_build "$service_name" "$dockerfile" "$context"; then
                    failed_services+=("$service_name")
                fi
            done
            
            # 總結
            echo ""
            echo "=== 建構總結 ==="
            if [ ${#failed_services[@]} -eq 0 ]; then
                log_success "所有服務建構成功！"
            else
                log_error "以下服務建構失敗: ${failed_services[*]}"
                echo ""
                log_info "運行 './scripts/docker-build-test.sh diagnose' 獲取詳細診斷資訊"
            fi
            ;;
    esac
}

# 顯示使用說明
show_usage() {
    echo "使用方法: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  all       - 運行完整的診斷和測試 (預設)"
    echo "  check     - 僅檢查 Docker 環境和網路連線"
    echo "  clean     - 清理 Docker 環境"
    echo "  pull      - 預拉取基底映像"
    echo "  test      - 測試所有服務建構"
    echo "  diagnose  - 診斷建構問題"
    echo ""
}

# 檢查是否請求幫助
if [[ "${1}" == "-h" || "${1}" == "--help" ]]; then
    show_usage
    exit 0
fi

# 運行主函數
main "$@"
