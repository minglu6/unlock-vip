# 阿里云 Docker 部署 - 快速摘要

## 📋 已准备的文件

### 1. 文档类 (3个)
- ✅ `ALIYUN_DEPLOYMENT.md` - 完整部署手册 (53KB, 1000+ 行)
- ✅ `docs/DOCKER_IMAGE_GUIDE.md` - 镜像构建指南 (12KB)
- ✅ `DEPLOYMENT_CHECKLIST.md` - 部署清单 (本文档)

### 2. 配置文件类 (4个)
- ✅ `.env.prod.example` - 环境变量模板
- ✅ `nginx/nginx.conf` - Nginx 主配置
- ✅ `nginx/conf.d/unlock-vip.conf` - 应用 Nginx 配置
- ✅ `mysql-conf.d/mysql.cnf` - MySQL 优化配置

### 3. Docker 编排 (已存在)
- ✅ `docker-compose.prod.yml` - 生产环境编排 (含 6 个服务)
- ✅ `Dockerfile` - 镜像构建文件

### 4. 脚本类 (2个)
- ✅ `deploy-aliyun.sh` - 一键部署脚本 (18KB, 450+ 行)
- ✅ `scripts/manage.sh` - 日常管理工具 (15KB, 400+ 行)

---

## 🚀 三种部署方式

### 方式一: 一键部署 ⭐ 推荐

```bash
# 1. 上传项目到服务器
scp -r unlock-vip root@your-server-ip:/opt/

# 2. 连接服务器
ssh root@your-server-ip

# 3. 执行部署脚本
cd /opt/unlock-vip
chmod +x deploy-aliyun.sh
./deploy-aliyun.sh

# 4. 修改 CSDN 配置
vim /opt/unlock-vip/.env.prod
# 修改 CSDN_USERNAME 和 CSDN_PASSWORD

# 5. 重启服务
docker-compose -f docker-compose.prod.yml restart
```

**优点**: 
- ✅ 全自动安装 Docker 环境
- ✅ 自动生成强密码
- ✅ 自动配置备份任务
- ✅ 完整的错误处理
- ✅ 友好的交互提示

### 方式二: 使用预构建镜像

如果你已经构建并推送了镜像到阿里云 ACR:

```bash
# 1. 服务器准备 (安装 Docker)
curl -fsSL https://get.docker.com | bash

# 2. 上传配置文件
scp docker-compose.prod.yml root@your-server-ip:/opt/unlock-vip/
scp .env.prod root@your-server-ip:/opt/unlock-vip/
scp -r nginx root@your-server-ip:/opt/unlock-vip/
scp -r mysql-conf.d root@your-server-ip:/opt/unlock-vip/

# 3. 创建数据目录
ssh root@your-server-ip
mkdir -p /data/unlock-vip/{mysql,redis,downloads,logs,ssl}

# 4. 启动服务
cd /opt/unlock-vip
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

**优点**:
- ✅ 跳过镜像构建步骤
- ✅ 部署速度更快
- ✅ 适合多服务器部署

### 方式三: 完全手动部署

适合需要自定义配置的场景，详细步骤见 `ALIYUN_DEPLOYMENT.md`

---

## 📦 镜像准备选项

### 选项 A: 使用公共镜像 (最简单)

如果你的镜像已发布到公共仓库:

```bash
# 修改 .env.prod
DOCKER_REGISTRY=your-public-registry
VERSION=1.0.0

# 直接使用
docker-compose -f docker-compose.prod.yml up -d
```

### 选项 B: 推送到阿里云 ACR (推荐)

```bash
# 1. 本地构建
docker build -t unlock-vip:1.0.0 .

# 2. 登录阿里云
docker login registry.cn-hangzhou.aliyuncs.com

# 3. 打标签并推送
docker tag unlock-vip:1.0.0 \
  registry.cn-hangzhou.aliyuncs.com/your-namespace/unlock-vip:1.0.0
docker push registry.cn-hangzhou.aliyuncs.com/your-namespace/unlock-vip:1.0.0
```

详细步骤: `docs/DOCKER_IMAGE_GUIDE.md`

### 选项 C: 服务器本地构建

```bash
# 在服务器上直接构建 (需要上传源码)
cd /opt/unlock-vip
docker build -t unlock-vip:1.0.0 .
```

---

## ⚙️ 配置要点

### 必须修改的配置 (在 .env.prod 中)

```bash
# 1. CSDN 账号 - 必须
CSDN_USERNAME=your_csdn_username
CSDN_PASSWORD=your_csdn_password

# 2. 镜像仓库 - 如果使用私有仓库
DOCKER_REGISTRY=registry.cn-hangzhou.aliyuncs.com/your-namespace

# 3. 验证码服务 - 推荐配置
CAPTCHA_SERVICE=chaojiying
CHAOJIYING_USERNAME=your_username
CHAOJIYING_PASSWORD=your_password
CHAOJIYING_SOFT_ID=your_soft_id
```

### 自动生成的配置 (通常不需要修改)

由 `deploy-aliyun.sh` 自动生成:
- `DATABASE_ROOT_PASSWORD` - 强随机密码
- `DATABASE_PASSWORD` - 强随机密码
- `REDIS_PASSWORD` - 强随机密码
- `ADMIN_MASTER_KEY` - 安全密钥
- `FLOWER_PASSWORD` - 随机密码

**密码保存位置**: `/root/.unlock-vip-credentials`

---

## 🔍 部署验证

部署完成后，执行以下检查:

```bash
# 1. 容器状态
docker ps

# 预期: 6 个容器全部 Up
# - unlock-vip-mysql-prod
# - unlock-vip-redis-prod
# - unlock-vip-api
# - unlock-vip-celery
# - unlock-vip-beat
# - unlock-vip-nginx
# - unlock-vip-flower (可选)

# 2. 健康检查
curl http://localhost/health
# 预期: {"status":"healthy"}

# 3. API 文档
curl http://localhost/docs
# 预期: 返回 HTML 页面

# 4. 数据库连接
docker exec unlock-vip-api python -c "
from app.core.config import settings
from sqlalchemy import create_engine
create_engine(settings.DATABASE_URL).connect()
print('数据库连接成功')
"

# 5. Redis 连接
docker exec unlock-vip-redis-prod redis-cli -a $(grep REDIS_PASSWORD /opt/unlock-vip/.env.prod | cut -d'=' -f2) ping
# 预期: PONG
```

---

## 🛠️ 日常管理

### 使用管理工具

```bash
# 进入交互式菜单
/opt/unlock-vip/scripts/manage.sh
```

提供 19 个常用功能:
1. 启动/停止/重启服务
2. 查看状态和日志
3. 更新和回滚
4. 监控和诊断
5. 备份和恢复
6. 清理和维护

### 常用命令速查

```bash
# 查看服务状态
docker-compose -f /opt/unlock-vip/docker-compose.prod.yml ps

# 查看实时日志
docker-compose -f /opt/unlock-vip/docker-compose.prod.yml logs -f

# 重启服务
docker-compose -f /opt/unlock-vip/docker-compose.prod.yml restart

# 更新服务
docker-compose -f /opt/unlock-vip/docker-compose.prod.yml pull
docker-compose -f /opt/unlock-vip/docker-compose.prod.yml up -d

# 进入容器
docker exec -it unlock-vip-api bash

# 查看资源使用
docker stats

# 备份数据库
/opt/scripts/backup-mysql.sh
```

---

## 📊 服务架构

```
Internet
   │
   ▼
┌─────────────────┐
│  Nginx (443)    │ ◄── SSL 证书
│  反向代理        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  FastAPI (8000) │
│  4 Workers      │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────┐
│ MySQL  │ │ Redis  │
│ 8.0    │ │ 7      │
└────────┘ └────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌─────────┐ ┌────────┐
│ Celery  │ │ Beat   │
│ Worker  │ │ 定时器  │
└─────────┘ └────────┘
```

**端口映射**:
- 80 → Nginx HTTP
- 443 → Nginx HTTPS
- 8000 → FastAPI (内部)
- 3306 → MySQL (内部)
- 6379 → Redis (内部)
- 5555 → Flower (可选，监控)

---

## 🎯 快速开始流程

### 第一步: 服务器准备 (5分钟)

```bash
# 1. 购买阿里云 ECS
# 2. 配置安全组 (开放 80, 443 端口)
# 3. 连接服务器
ssh root@your-server-ip
```

### 第二步: 上传项目 (2分钟)

```bash
# 本地执行: 打包项目
cd /path/to/unlock-vip
tar -czf unlock-vip.tar.gz \
    app/ \
    docker-compose.prod.yml \
    Dockerfile \
    .env.prod.example \
    deploy-aliyun.sh \
    scripts/ \
    nginx/ \
    mysql-conf.d/ \
    requirements.txt \
    manage_db.py

# 上传到服务器
scp unlock-vip.tar.gz root@your-server-ip:/opt/

# 服务器执行: 解压
ssh root@your-server-ip
cd /opt
tar -xzf unlock-vip.tar.gz
cd unlock-vip
```

### 第三步: 执行部署 (10分钟)

```bash
# 运行部署脚本
chmod +x deploy-aliyun.sh
./deploy-aliyun.sh

# 等待提示后，修改配置
vim .env.prod
# 修改: CSDN_USERNAME, CSDN_PASSWORD

# 按 y 继续部署
```

### 第四步: 验证和测试 (3分钟)

```bash
# 查看服务状态
docker ps

# 测试 API
curl http://localhost/health
curl http://localhost/docs

# 查看密码
cat /root/.unlock-vip-credentials
```

### 第五步: 配置域名和 SSL (可选, 10分钟)

```bash
# 1. 域名解析到服务器 IP

# 2. 申请 SSL 证书
certbot certonly --standalone -d your-domain.com

# 3. 复制证书
cp /etc/letsencrypt/live/your-domain.com/*.pem /data/unlock-vip/ssl/

# 4. 修改 Nginx 配置
vim nginx/conf.d/unlock-vip.conf
# 修改 server_name 为你的域名

# 5. 重启 Nginx
docker exec unlock-vip-nginx nginx -s reload
```

**总耗时: ~30分钟** (包含下载和安装时间)

---

## 📚 文档导航

### 快速参考
- **本文档** - 快速摘要和流程
- `API_QUICK_REFERENCE.md` - API 使用说明

### 详细文档
- `ALIYUN_DEPLOYMENT.md` - 完整部署手册 (1000+ 行)
  - 第 1 部分: 服务器要求和架构
  - 第 2 部分: 详细部署步骤 (8个步骤)
  - 第 3 部分: 镜像管理
  - 第 4 部分: 监控运维
  - 第 5 部分: 故障排查
  - 第 6 部分: 安全加固

- `docs/DOCKER_IMAGE_GUIDE.md` - 镜像管理指南
  - 构建镜像
  - 推送到阿里云 ACR
  - 版本管理
  - 镜像优化

### 功能文档
- `FILE_CLEANUP.md` - 文件自动清理
- `CELERY_BEAT_GUIDE.md` - 定时任务
- `ADMIN_SECURITY.md` - 管理员认证

---

## ❓ 常见问题

### Q1: 我应该选择哪种部署方式？

**推荐**: 使用一键部署脚本 (`deploy-aliyun.sh`)
- ✅ 适合新手
- ✅ 全自动化
- ✅ 错误处理完善

### Q2: 镜像应该推送到哪里？

**推荐**: 阿里云容器镜像服务 (ACR)
- ✅ 免费个人版
- ✅ 国内访问速度快
- ✅ 与 ECS 同区域免流量费

### Q3: 需要配置域名吗？

**可选但推荐**:
- 使用 IP: 可以工作，但需要 HTTP
- 使用域名: 可以配置 HTTPS，更安全专业

### Q4: 如何查看密码？

```bash
# 所有密码都保存在这个文件
cat /root/.unlock-vip-credentials

# 或者查看 .env.prod
cat /opt/unlock-vip/.env.prod | grep PASSWORD
```

### Q5: 如何更新服务？

```bash
# 方法1: 使用管理工具
/opt/unlock-vip/scripts/manage.sh
# 选择: 7. 更新并重启服务

# 方法2: 手动执行
cd /opt/unlock-vip
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

### Q6: 如何备份数据？

自动备份: 每天凌晨 2 点自动执行

手动备份:
```bash
/opt/scripts/backup-mysql.sh
```

备份文件位置:
```bash
ls -lh /data/backups/mysql/
```

### Q7: 服务启动失败怎么办？

```bash
# 1. 查看日志
docker-compose -f /opt/unlock-vip/docker-compose.prod.yml logs

# 2. 检查配置
docker-compose -f /opt/unlock-vip/docker-compose.prod.yml config

# 3. 查看具体服务日志
docker logs unlock-vip-api
docker logs unlock-vip-mysql-prod

# 4. 参考故障排查文档
# 见 ALIYUN_DEPLOYMENT.md 的"故障排查"章节
```

---

## ✅ 部署检查清单

### 部署前
- [ ] 准备阿里云 ECS (4核8GB 推荐)
- [ ] 配置安全组 (80, 443 端口)
- [ ] 准备 CSDN 账号
- [ ] (可选) 准备域名
- [ ] (可选) 注册超级鹰账号

### 部署中
- [ ] 上传项目文件到服务器
- [ ] 执行部署脚本
- [ ] 修改 .env.prod 配置
- [ ] 等待服务启动

### 部署后
- [ ] 验证所有容器正常运行
- [ ] 测试 API 健康检查
- [ ] 访问 API 文档页面
- [ ] 保存密码文件
- [ ] (可选) 配置域名和 SSL
- [ ] (可选) 设置监控告警

### 运维
- [ ] 定期查看服务状态
- [ ] 检查磁盘空间
- [ ] 验证自动备份正常
- [ ] 定期更新镜像
- [ ] 查看 Flower 监控

---

## 🎉 总结

你现在拥有：

1. **完整的部署文档** (3个文档, 70KB+)
   - 完整部署手册
   - 镜像构建指南
   - 部署清单

2. **生产级配置** (4个配置文件)
   - Docker Compose
   - Nginx
   - MySQL
   - 环境变量

3. **自动化脚本** (2个脚本)
   - 一键部署脚本 (450+ 行)
   - 日常管理工具 (400+ 行)

4. **完整的服务栈**
   - FastAPI Web 服务
   - MySQL 数据库
   - Redis 缓存
   - Celery 异步任务
   - Celery Beat 定时任务
   - Nginx 反向代理
   - Flower 监控

**下一步**: 

选择你喜欢的部署方式，开始部署吧！

推荐从 `deploy-aliyun.sh` 开始，只需 30 分钟！🚀

---

**需要帮助？**
- 📖 查看 `ALIYUN_DEPLOYMENT.md` 详细手册
- 🐛 查看故障排查章节
- 💬 提交 GitHub Issue
