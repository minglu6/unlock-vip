#!/bin/bash
# 部署脚本 - 一键部署 unlock-vip 到云服务器

set -e  # 遇到错误立即退出

echo "========================================"
echo "  Unlock-VIP 部署脚本"
echo "========================================"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 项目路径
PROJECT_DIR="/opt/unlock-vip"

# 检查是否为 root 用户
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}错误: 请使用 root 用户运行此脚本${NC}"
    echo "使用: sudo bash deploy.sh"
    exit 1
fi

echo -e "${GREEN}[1/7] 检查系统环境...${NC}"
# 检查 Python 版本
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未安装 Python3${NC}"
    exit 1
fi

echo -e "${GREEN}[2/7] 创建日志目录...${NC}"
mkdir -p /var/log/unlock-vip
chmod 755 /var/log/unlock-vip

echo -e "${GREEN}[3/7] 安装 Python 依赖...${NC}"
cd $PROJECT_DIR

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install -r requirements.txt

echo -e "${GREEN}[4/7] 配置 Supervisor...${NC}"
# 复制 supervisor 配置文件
cp deploy/supervisor.conf /etc/supervisor/conf.d/unlock-vip.conf

# 重新加载 supervisor 配置
supervisorctl reread
supervisorctl update

echo -e "${GREEN}[5/7] 配置 Nginx...${NC}"
# 复制 nginx 配置文件
cp deploy/nginx.conf /etc/nginx/sites-available/unlock-vip

# 创建软链接
if [ ! -L /etc/nginx/sites-enabled/unlock-vip ]; then
    ln -s /etc/nginx/sites-available/unlock-vip /etc/nginx/sites-enabled/
fi

# 测试 nginx 配置
nginx -t

echo -e "${GREEN}[6/7] 启动服务...${NC}"
# 启动应用
supervisorctl start unlock-vip

# 重启 nginx
systemctl reload nginx

echo -e "${GREEN}[7/7] 检查服务状态...${NC}"
supervisorctl status unlock-vip

echo ""
echo -e "${GREEN}========================================"
echo "  部署完成！"
echo "========================================${NC}"
echo ""
echo "服务状态检查:"
echo "  - Supervisor: supervisorctl status unlock-vip"
echo "  - Nginx: systemctl status nginx"
echo "  - 日志: tail -f /var/log/unlock-vip/app.log"
echo ""
echo "常用命令:"
echo "  - 重启应用: supervisorctl restart unlock-vip"
echo "  - 停止应用: supervisorctl stop unlock-vip"
echo "  - 查看日志: tail -f /var/log/unlock-vip/app.log"
echo ""
echo "访问地址:"
echo "  - API文档: http://your_server_ip/docs"
echo "  - 健康检查: http://your_server_ip/health"
echo ""
