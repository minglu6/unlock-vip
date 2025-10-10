#!/bin/bash

################################################################################
# Unlock VIP 快速操作脚本
# 提供常用的管理命令
################################################################################

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 项目目录
PROJECT_DIR="/opt/unlock-vip"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.prod.yml"
ENV_FILE="$PROJECT_DIR/.env.prod"

# 日志函数
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

# 检查是否在项目目录
check_directory() {
    if [ ! -f "$COMPOSE_FILE" ]; then
        log_error "未找到 docker-compose.prod.yml"
        log_error "请确保在正确的目录运行此脚本"
        exit 1
    fi
}

# 显示菜单
show_menu() {
    cat <<EOF

╔══════════════════════════════════════════════════════════════╗
║            Unlock VIP 管理工具                               ║
╚══════════════════════════════════════════════════════════════╝

📦 容器管理:
  1. 启动所有服务
  2. 停止所有服务
  3. 重启所有服务
  4. 查看服务状态
  5. 查看实时日志

🔄 更新操作:
  6. 拉取最新镜像
  7. 更新并重启服务
  8. 回滚到上一版本

🔍 监控查询:
  9. 查看资源使用
  10. 查看健康状态
  11. 查看错误日志
  12. 查看磁盘使用

💾 备份恢复:
  13. 备份数据库
  14. 恢复数据库
  15. 导出配置

🛠️ 维护工具:
  16. 清理日志文件
  17. 清理 Docker 缓存
  18. 进入容器终端
  19. 执行数据库命令

0. 退出

EOF
    read -p "请选择操作 [0-19]: " choice
    return $choice
}

# 1. 启动服务
start_services() {
    log_info "启动所有服务..."
    cd "$PROJECT_DIR"
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d
    log_success "服务启动完成"
    sleep 2
    docker-compose -f "$COMPOSE_FILE" ps
}

# 2. 停止服务
stop_services() {
    log_info "停止所有服务..."
    cd "$PROJECT_DIR"
    docker-compose -f "$COMPOSE_FILE" down
    log_success "服务已停止"
}

# 3. 重启服务
restart_services() {
    log_info "重启所有服务..."
    cd "$PROJECT_DIR"
    docker-compose -f "$COMPOSE_FILE" restart
    log_success "服务已重启"
    sleep 2
    docker-compose -f "$COMPOSE_FILE" ps
}

# 4. 查看状态
show_status() {
    log_info "服务状态:"
    cd "$PROJECT_DIR"
    docker-compose -f "$COMPOSE_FILE" ps
    
    echo ""
    log_info "容器详细状态:"
    docker ps --filter "name=unlock-vip" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
}

# 5. 查看日志
show_logs() {
    log_info "可选服务: all, web, celery, celery-beat, mysql, redis, nginx, flower"
    read -p "请选择服务 [默认: all]: " service
    service=${service:-all}
    
    cd "$PROJECT_DIR"
    if [ "$service" = "all" ]; then
        docker-compose -f "$COMPOSE_FILE" logs -f --tail=100
    else
        docker-compose -f "$COMPOSE_FILE" logs -f --tail=100 "$service"
    fi
}

# 6. 拉取镜像
pull_images() {
    log_info "拉取最新镜像..."
    cd "$PROJECT_DIR"
    docker-compose -f "$COMPOSE_FILE" pull
    log_success "镜像拉取完成"
}

# 7. 更新并重启
update_and_restart() {
    log_warning "此操作将更新服务并重启，可能会有短暂的服务中断"
    read -p "确认继续？(y/n): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        log_info "操作已取消"
        return
    fi
    
    log_info "开始更新..."
    cd "$PROJECT_DIR"
    
    # 拉取最新镜像
    docker-compose -f "$COMPOSE_FILE" pull
    
    # 重启服务
    docker-compose -f "$COMPOSE_FILE" up -d
    
    log_success "更新完成"
    sleep 3
    docker-compose -f "$COMPOSE_FILE" ps
}

# 8. 回滚
rollback() {
    log_warning "回滚功能需要指定镜像版本"
    read -p "请输入要回滚到的版本 (如 1.0.0): " version
    
    if [ -z "$version" ]; then
        log_error "版本号不能为空"
        return
    fi
    
    # 修改 .env.prod 中的版本
    sed -i.bak "s/VERSION=.*/VERSION=$version/" "$ENV_FILE"
    
    log_info "版本已修改为: $version"
    log_info "重启服务以应用更改..."
    
    cd "$PROJECT_DIR"
    docker-compose -f "$COMPOSE_FILE" up -d
    
    log_success "回滚完成"
}

# 9. 资源使用
show_resources() {
    log_info "容器资源使用情况:"
    docker stats --no-stream --filter "name=unlock-vip" \
        --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}"
}

# 10. 健康状态
check_health() {
    log_info "检查服务健康状态..."
    
    # API 健康检查
    if curl -sf http://localhost/health > /dev/null 2>&1; then
        log_success "✓ API 服务正常"
    else
        log_error "✗ API 服务异常"
    fi
    
    # MySQL 检查
    if docker exec unlock-vip-mysql-prod mysqladmin ping -h localhost --silent 2>/dev/null; then
        log_success "✓ MySQL 数据库正常"
    else
        log_error "✗ MySQL 数据库异常"
    fi
    
    # Redis 检查
    source "$ENV_FILE"
    if docker exec unlock-vip-redis-prod redis-cli -a "$REDIS_PASSWORD" ping 2>/dev/null | grep -q PONG; then
        log_success "✓ Redis 缓存正常"
    else
        log_error "✗ Redis 缓存异常"
    fi
    
    # Celery Worker 检查
    if docker exec unlock-vip-celery celery -A app.core.celery_app inspect ping 2>/dev/null | grep -q "pong"; then
        log_success "✓ Celery Worker 正常"
    else
        log_error "✗ Celery Worker 异常"
    fi
}

# 11. 错误日志
show_errors() {
    log_info "最近的错误日志:"
    
    cd "$PROJECT_DIR"
    echo ""
    echo "=== Web 错误 ==="
    docker-compose -f "$COMPOSE_FILE" logs --tail=20 web 2>&1 | grep -i error || echo "无错误"
    
    echo ""
    echo "=== Celery 错误 ==="
    docker-compose -f "$COMPOSE_FILE" logs --tail=20 celery 2>&1 | grep -i error || echo "无错误"
    
    echo ""
    echo "=== Nginx 错误 ==="
    docker exec unlock-vip-nginx tail -20 /var/log/nginx/error.log 2>/dev/null || echo "无错误日志"
}

# 12. 磁盘使用
show_disk_usage() {
    log_info "磁盘使用情况:"
    
    echo ""
    echo "=== 数据目录 ==="
    du -sh /data/unlock-vip/*
    
    echo ""
    echo "=== Docker 占用 ==="
    docker system df
    
    echo ""
    echo "=== 系统磁盘 ==="
    df -h /data
}

# 13. 备份数据库
backup_database() {
    log_info "开始备份数据库..."
    
    BACKUP_DIR="/data/backups/mysql"
    mkdir -p "$BACKUP_DIR"
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$BACKUP_DIR/manual_backup_$TIMESTAMP.sql"
    
    source "$ENV_FILE"
    
    docker exec unlock-vip-mysql-prod mysqldump \
        -uroot -p"$DATABASE_ROOT_PASSWORD" \
        --single-transaction \
        --routines \
        --triggers \
        --databases unlock_vip > "$BACKUP_FILE"
    
    gzip "$BACKUP_FILE"
    
    log_success "备份完成: $BACKUP_FILE.gz"
    log_info "文件大小: $(du -h $BACKUP_FILE.gz | cut -f1)"
}

# 14. 恢复数据库
restore_database() {
    log_warning "此操作将覆盖当前数据库！"
    log_info "可用的备份文件:"
    
    BACKUP_DIR="/data/backups/mysql"
    ls -lh "$BACKUP_DIR"/*.sql.gz 2>/dev/null || {
        log_error "未找到备份文件"
        return
    }
    
    read -p "请输入备份文件名: " backup_file
    
    if [ ! -f "$BACKUP_DIR/$backup_file" ]; then
        log_error "文件不存在"
        return
    fi
    
    read -p "确认恢复？此操作不可逆！(yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        log_info "操作已取消"
        return
    fi
    
    log_info "开始恢复数据库..."
    
    source "$ENV_FILE"
    
    gunzip -c "$BACKUP_DIR/$backup_file" | \
        docker exec -i unlock-vip-mysql-prod mysql \
        -uroot -p"$DATABASE_ROOT_PASSWORD"
    
    log_success "数据库恢复完成"
}

# 15. 导出配置
export_config() {
    log_info "导出配置文件..."
    
    EXPORT_DIR="/tmp/unlock-vip-config-$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$EXPORT_DIR"
    
    # 复制配置文件（隐藏敏感信息）
    cp "$ENV_FILE" "$EXPORT_DIR/.env.prod"
    sed -i 's/PASSWORD=.*/PASSWORD=***HIDDEN***/g' "$EXPORT_DIR/.env.prod"
    sed -i 's/KEY=.*/KEY=***HIDDEN***/g' "$EXPORT_DIR/.env.prod"
    
    # 复制其他配置
    cp -r "$PROJECT_DIR/nginx" "$EXPORT_DIR/"
    cp -r "$PROJECT_DIR/mysql-conf.d" "$EXPORT_DIR/"
    cp "$COMPOSE_FILE" "$EXPORT_DIR/"
    
    tar -czf "$EXPORT_DIR.tar.gz" -C /tmp "$(basename $EXPORT_DIR)"
    rm -rf "$EXPORT_DIR"
    
    log_success "配置已导出到: $EXPORT_DIR.tar.gz"
}

# 16. 清理日志
cleanup_logs() {
    log_info "清理日志文件..."
    
    read -p "清理多少天前的日志？[默认: 7]: " days
    days=${days:-7}
    
    log_info "清理 $days 天前的日志..."
    
    find /data/unlock-vip/logs -name "*.log" -mtime +$days -delete
    find /data/unlock-vip/logs -name "*.log.*" -mtime +$days -delete
    
    log_success "日志清理完成"
    du -sh /data/unlock-vip/logs/*
}

# 17. 清理 Docker
cleanup_docker() {
    log_warning "此操作将清理未使用的 Docker 资源"
    read -p "确认继续？(y/n): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        log_info "操作已取消"
        return
    fi
    
    log_info "清理 Docker 缓存..."
    
    docker system prune -a -f
    docker volume prune -f
    
    log_success "清理完成"
    docker system df
}

# 18. 进入容器
enter_container() {
    log_info "可选容器:"
    docker ps --filter "name=unlock-vip" --format "{{.Names}}"
    
    read -p "请输入容器名称 [默认: unlock-vip-api]: " container
    container=${container:-unlock-vip-api}
    
    log_info "进入容器: $container"
    docker exec -it "$container" bash
}

# 19. 数据库命令
database_command() {
    log_info "进入 MySQL 命令行..."
    
    source "$ENV_FILE"
    
    docker exec -it unlock-vip-mysql-prod mysql \
        -uroot -p"$DATABASE_ROOT_PASSWORD" \
        unlock_vip
}

# 主循环
main() {
    check_directory
    
    while true; do
        show_menu
        choice=$?
        
        case $choice in
            1) start_services ;;
            2) stop_services ;;
            3) restart_services ;;
            4) show_status ;;
            5) show_logs ;;
            6) pull_images ;;
            7) update_and_restart ;;
            8) rollback ;;
            9) show_resources ;;
            10) check_health ;;
            11) show_errors ;;
            12) show_disk_usage ;;
            13) backup_database ;;
            14) restore_database ;;
            15) export_config ;;
            16) cleanup_logs ;;
            17) cleanup_docker ;;
            18) enter_container ;;
            19) database_command ;;
            0) 
                log_info "退出管理工具"
                exit 0
                ;;
            *)
                log_error "无效的选择"
                ;;
        esac
        
        echo ""
        read -p "按回车键继续..."
    done
}

# 执行主函数
main
