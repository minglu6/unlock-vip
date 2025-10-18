#!/bin/bash
# Nginx + Docker 部署脚本

set -e

echo "========================================"
echo "  Unlock-VIP with Nginx 部署脚本"
echo "========================================"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 检查是否在项目目录
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}错误: 请在项目根目录运行此脚本${NC}"
    exit 1
fi

echo -e "${GREEN}[1/6] 检查 Docker 环境...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: 未安装 Docker${NC}"
    echo "请先安装 Docker: curl -fsSL https://get.docker.com | bash"
    exit 1
fi

echo -e "${GREEN}[2/6] 检查 cookies.json...${NC}"
if [ ! -f "cookies.json" ]; then
    echo -e "${RED}错误: cookies.json 文件不存在${NC}"
    echo "请先创建 cookies.json 文件"
    exit 1
fi

echo -e "${GREEN}[3/6] 创建必要目录...${NC}"
mkdir -p nginx/logs
mkdir -p downloads

echo -e "${GREEN}[4/6] 停止旧容器（如果存在）...${NC}"
docker compose down 2>/dev/null || true

echo -e "${GREEN}[5/6] 构建并启动服务...${NC}"
docker compose up -d --build

echo -e "${GREEN}[6/6] 等待服务启动...${NC}"
sleep 5

# 检查服务状态
echo ""
echo "容器状态:"
docker compose ps

echo ""
echo -e "${GREEN}========================================"
echo "  部署完成！"
echo "========================================${NC}"
echo ""
echo "访问地址:"
echo "  - 主页: http://175.24.164.85/"
echo "  - API文档: http://175.24.164.85/docs"
echo "  - 健康检查: http://175.24.164.85/health"
echo ""
echo "常用命令:"
echo "  - 查看日志: docker compose logs -f"
echo "  - 查看应用日志: docker compose logs -f unlock-vip"
echo "  - 查看Nginx日志: docker compose logs -f nginx"
echo "  - 重启服务: docker compose restart"
echo "  - 停止服务: docker compose down"
echo ""
echo "Nginx 日志位置:"
echo "  - 访问日志: ./nginx/logs/unlock-vip-access.log"
echo "  - 错误日志: ./nginx/logs/unlock-vip-error.log"
echo ""

# 测试健康检查
echo "正在测试服务..."
sleep 2
if curl -f http://localhost/health &> /dev/null; then
    echo -e "${GREEN}✓ 服务运行正常！${NC}"
else
    echo -e "${YELLOW}⚠ 服务可能还在启动中，请稍后访问${NC}"
fi
