#!/bin/bash

# VisionFlow 監控與日誌管理腳本
# 用於監控服務狀態、收集日誌和性能指標

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
DOCKER_COMPOSE_FILE="docker-compose.yaml"
LOGS_DIR="logs"
METRICS_DIR="metrics"
ALERTS_FILE="$LOGS_DIR/alerts.log"

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

# 創建必要目錄
setup_dirs() {
    mkdir -p "$LOGS_DIR" "$METRICS_DIR"
}

# 收集系統指標
collect_system_metrics() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local metrics_file="$METRICS_DIR/system_metrics_$(date '+%Y%m%d').log"
    
    log_info "收集系統指標..."
    
    {
        echo "[$timestamp] SYSTEM_METRICS"
        echo "CPU_USAGE: $(top -l 1 | grep "CPU usage" | awk '{print $3}' | sed 's/%//')"
        echo "MEMORY_USAGE: $(vm_stat | grep "Pages active" | awk '{print $3}' | sed 's/\.//')"
        echo "DISK_USAGE: $(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')"
        echo "LOAD_AVERAGE: $(uptime | awk -F'load averages:' '{print $2}')"
        echo "---"
    } >> "$metrics_file"
}

# 收集 Docker 指標
collect_docker_metrics() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local metrics_file="$METRICS_DIR/docker_metrics_$(date '+%Y%m%d').log"
    
    log_info "收集 Docker 指標..."
    
    {
        echo "[$timestamp] DOCKER_METRICS"
        echo "CONTAINERS_RUNNING: $(docker ps --format "table {{.Names}}" | tail -n +2 | wc -l | tr -d ' ')"
        echo "IMAGES_COUNT: $(docker images | tail -n +2 | wc -l | tr -d ' ')"
        echo "VOLUMES_COUNT: $(docker volume ls | tail -n +2 | wc -l | tr -d ' ')"
        echo "NETWORKS_COUNT: $(docker network ls | tail -n +2 | wc -l | tr -d ' ')"
        
        # 各服務的資源使用情況
        echo "SERVICE_STATS:"
        docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}" | tail -n +2
        echo "---"
    } >> "$metrics_file"
}

# 檢查服務健康狀態
check_service_health() {
    log_info "檢查服務健康狀態..."
    
    local services=("web:5000" "camera_ctrl:5000" "object_recognition:5000")
    local unhealthy_services=()
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    for service_port in "${services[@]}"; do
        local service=$(echo "$service_port" | cut -d: -f1)
        local port=$(echo "$service_port" | cut -d: -f2)
        
        # 檢查容器狀態
        if docker-compose -f "$DOCKER_COMPOSE_FILE" ps "$service" | grep -q "Up"; then
            # 檢查服務回應
            if curl -f -s "http://localhost:$port/health" > /dev/null 2>&1; then
                log_success "$service 服務健康"
                echo "[$timestamp] HEALTH_OK: $service" >> "$LOGS_DIR/health.log"
            else
                log_warning "$service 服務無回應"
                unhealthy_services+=("$service")
                echo "[$timestamp] HEALTH_FAIL: $service - No response" >> "$ALERTS_FILE"
            fi
        else
            log_error "$service 容器未運行"
            unhealthy_services+=("$service")
            echo "[$timestamp] HEALTH_FAIL: $service - Container not running" >> "$ALERTS_FILE"
        fi
    done
    
    if [ ${#unhealthy_services[@]} -gt 0 ]; then
        log_error "不健康的服務: ${unhealthy_services[*]}"
        return 1
    fi
    
    return 0
}

# 收集應用日誌
collect_app_logs() {
    log_info "收集應用日誌..."
    
    local log_date=$(date '+%Y%m%d')
    local services=("web" "camera_ctrl" "object_recognition" "redis_worker")
    
    for service in "${services[@]}"; do
        local log_file="$LOGS_DIR/${service}_${log_date}.log"
        
        if docker-compose -f "$DOCKER_COMPOSE_FILE" ps "$service" | grep -q "Up"; then
            log_info "收集 $service 服務日誌..."
            docker-compose -f "$DOCKER_COMPOSE_FILE" logs --tail=1000 "$service" >> "$log_file" 2>/dev/null || true
        fi
    done
}

# 分析日誌異常
analyze_logs() {
    log_info "分析日誌異常..."
    
    local today=$(date '+%Y%m%d')
    local error_patterns=("ERROR" "CRITICAL" "FATAL" "Exception" "Failed" "denied")
    local alert_threshold=10
    
    for pattern in "${error_patterns[@]}"; do
        local count=$(grep -i "$pattern" "$LOGS_DIR"/*_${today}.log 2>/dev/null | wc -l | tr -d ' ')
        
        if [ "$count" -gt "$alert_threshold" ]; then
            local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
            log_warning "發現 $count 個 $pattern 日誌"
            echo "[$timestamp] LOG_ALERT: $pattern count=$count (threshold=$alert_threshold)" >> "$ALERTS_FILE"
        fi
    done
}

# 清理舊日誌
cleanup_old_logs() {
    local retention_days=${1:-7}
    
    log_info "清理 $retention_days 天前的日誌..."
    
    # 清理應用日誌
    find "$LOGS_DIR" -name "*.log" -type f -mtime +$retention_days -delete 2>/dev/null || true
    
    # 清理指標文件
    find "$METRICS_DIR" -name "*.log" -type f -mtime +$retention_days -delete 2>/dev/null || true
    
    log_success "舊日誌清理完成"
}

# 生成監控報告
generate_report() {
    local report_file="$LOGS_DIR/monitoring_report_$(date '+%Y%m%d_%H%M%S').txt"
    
    log_info "生成監控報告..."
    
    {
        echo "=========================================="
        echo "VisionFlow 監控報告"
        echo "生成時間: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "=========================================="
        echo ""
        
        echo "系統狀態:"
        echo "----------"
        uptime
        echo ""
        
        echo "Docker 服務狀態:"
        echo "---------------"
        docker-compose -f "$DOCKER_COMPOSE_FILE" ps
        echo ""
        
        echo "服務健康檢查:"
        echo "------------"
        if check_service_health > /dev/null 2>&1; then
            echo "✅ 所有服務健康"
        else
            echo "❌ 部分服務異常"
        fi
        echo ""
        
        echo "資源使用情況:"
        echo "------------"
        docker stats --no-stream
        echo ""
        
        echo "最近警告 (最近24小時):"
        echo "---------------------"
        if [ -f "$ALERTS_FILE" ]; then
            tail -20 "$ALERTS_FILE" | grep "$(date '+%Y-%m-%d')" || echo "無警告"
        else
            echo "無警告記錄"
        fi
        echo ""
        
        echo "磁碟使用情況:"
        echo "------------"
        df -h
        echo ""
        
    } > "$report_file"
    
    log_success "監控報告已生成: $report_file"
}

# 發送警告通知 (可擴展)
send_alert() {
    local message="$1"
    local severity="${2:-WARNING}"
    
    log_warning "發送警告: $message"
    
    # 這裡可以添加實際的通知邏輯
    # 例如: 發送郵件、Slack、Discord 等
    
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] ALERT_SENT: [$severity] $message" >> "$ALERTS_FILE"
}

# 完整監控檢查
full_monitoring() {
    log_info "執行完整監控檢查..."
    
    setup_dirs
    collect_system_metrics
    collect_docker_metrics
    collect_app_logs
    
    if ! check_service_health; then
        send_alert "VisionFlow 服務健康檢查失敗" "CRITICAL"
    fi
    
    analyze_logs
    generate_report
    
    log_success "監控檢查完成"
}

# 實時監控
real_time_monitoring() {
    log_info "啟動實時監控 (按 Ctrl+C 停止)..."
    
    while true; do
        clear
        echo "VisionFlow 實時監控 - $(date '+%Y-%m-%d %H:%M:%S')"
        echo "=========================================="
        
        # 服務狀態
        echo "服務狀態:"
        docker-compose -f "$DOCKER_COMPOSE_FILE" ps
        echo ""
        
        # 資源使用
        echo "資源使用:"
        docker stats --no-stream
        echo ""
        
        # 健康檢查
        echo "健康檢查:"
        if check_service_health > /dev/null 2>&1; then
            echo "✅ 所有服務正常"
        else
            echo "❌ 部分服務異常"
        fi
        
        sleep 10
    done
}

# 顯示使用說明
show_usage() {
    echo "VisionFlow 監控腳本"
    echo ""
    echo "使用方式: $0 [命令] [選項]"
    echo ""
    echo "命令:"
    echo "  monitor         執行完整監控檢查"
    echo "  health          檢查服務健康狀態"
    echo "  logs            收集應用日誌"
    echo "  metrics         收集系統和 Docker 指標"
    echo "  report          生成監控報告"
    echo "  realtime        實時監控 (互動模式)"
    echo "  cleanup [days]  清理舊日誌 (預設7天)"
    echo "  help            顯示此說明"
    echo ""
    echo "範例:"
    echo "  $0 monitor"
    echo "  $0 cleanup 14"
    echo "  $0 realtime"
    echo ""
}

# 主函數
main() {
    local command=${1:-monitor}
    
    case $command in
        monitor)
            full_monitoring
            ;;
        health)
            check_service_health
            ;;
        logs)
            setup_dirs
            collect_app_logs
            ;;
        metrics)
            setup_dirs
            collect_system_metrics
            collect_docker_metrics
            ;;
        report)
            setup_dirs
            generate_report
            ;;
        realtime)
            real_time_monitoring
            ;;
        cleanup)
            cleanup_old_logs "${2:-7}"
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

# 捕獲中斷信號
trap 'log_info "監控已停止"; exit 0' INT TERM

# 執行主函數
main "$@"
