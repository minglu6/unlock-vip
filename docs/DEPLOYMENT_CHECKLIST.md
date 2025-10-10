# Unlock VIP 部署清单

本目录包含阿里云部署所需的所有文件和文档。

## 📁 文件结构

```
unlock-vip/
├── 部署文档
│   ├── ALIYUN_DEPLOYMENT.md        # 完整部署手册
│   └── docs/DOCKER_IMAGE_GUIDE.md  # 镜像构建指南
│
├── Docker 配置
│   ├── docker-compose.prod.yml     # 生产环境编排
│   ├── Dockerfile                  # 镜像构建文件
│   ├── .env.prod.example           # 环境变量模板
│   └── .dockerignore               # 构建排除文件
│
├── Nginx 配置
│   ├── nginx/nginx.conf            # Nginx 主配置
│   └── nginx/conf.d/
│       └── unlock-vip.conf         # 应用配置
│
├── MySQL 配置
│   └── mysql-conf.d/
│       └── mysql.cnf               # 数据库优化配置
│
├── 部署脚本
│   ├── deploy-aliyun.sh            # 一键部署脚本
│   └── scripts/
│       └── manage.sh               # 日常管理工具
│
└── 应用代码
    ├── app/                        # 应用源码
    ├── requirements.txt            # Python 依赖
    └── manage_db.py                # 数据库管理
```

## 🚀 部署流程

### 准备阶段

**1. 准备服务器**
- [ ] 购买阿里云 ECS (推荐 4核8GB)
- [ ] 配置安全组 (开放 22, 80, 443 端口)
- [ ] 获取服务器公网 IP
- [ ] (可选) 准备域名并解析

**2. 准备账号信息**
- [ ] CSDN 账号和密码
- [ ] (可选) 超级鹰验证码服务
- [ ] 阿里云容器镜像服务账号

**3. 准备配置**
- [ ] 决定使用的镜像仓库
- [ ] 生成强密码 (数据库、Redis、Admin Key)
- [ ] 确定文件清理策略 (默认 7 天)

### 部署步骤

#### 方式一: 一键部署 (推荐)

```bash
# 1. 下载部署脚本
wget https://your-repo.com/deploy-aliyun.sh
chmod +x deploy-aliyun.sh

# 2. 执行部署
./deploy-aliyun.sh

# 3. 按提示修改配置
vim /opt/unlock-vip/.env.prod

# 4. 完成部署
```

部署脚本会自动完成：
- ✅ 安装 Docker 和 Docker Compose
- ✅ 创建目录结构
- ✅ 生成配置文件和密码
- ✅ 拉取和启动服务
- ✅ 初始化数据库
- ✅ 配置防火墙和备份

#### 方式二: 手动部署

详细步骤请参考 [ALIYUN_DEPLOYMENT.md](ALIYUN_DEPLOYMENT.md)

1. **安装 Docker 环境** (第 122-166 行)
2. **准备项目文件** (第 168-253 行)
3. **构建推送镜像** (第 255-286 行)
4. **配置 SSL 证书** (第 288-331 行)
5. **启动服务** (第 333-380 行)
6. **初始化数据** (第 382-407 行)
7. **配置防火墙** (第 409-431 行)

### 部署后检查

**1. 服务状态**
```bash
docker-compose -f /opt/unlock-vip/docker-compose.prod.yml ps
```

预期输出：所有服务显示 `Up` 状态

**2. 健康检查**
```bash
curl http://localhost/health
# 应返回: {"status":"healthy"}
```

**3. 数据库连接**
```bash
docker exec unlock-vip-mysql-prod mysql -uunlock_vip_user -p -e "SELECT 1;"
```

**4. API 文档**
访问: `http://your-server-ip/docs`

**5. Celery 监控**
访问: `http://your-server-ip:5555`

## 🔧 配置说明

### 必须修改的配置

在 `.env.prod` 文件中：

```bash
# 1. 镜像仓库地址 (如果使用私有仓库)
DOCKER_REGISTRY=registry.cn-hangzhou.aliyuncs.com/your-namespace

# 2. CSDN 账号 (必须)
CSDN_USERNAME=your_username
CSDN_PASSWORD=your_password

# 3. 验证码服务 (推荐使用 chaojiying)
CAPTCHA_SERVICE=chaojiying
CHAOJIYING_USERNAME=your_username
CHAOJIYING_PASSWORD=your_password
CHAOJIYING_SOFT_ID=your_soft_id
```

### 自动生成的配置

这些配置由部署脚本自动生成，通常不需要修改：

- `DATABASE_ROOT_PASSWORD`: MySQL root 密码
- `DATABASE_PASSWORD`: 应用数据库密码
- `REDIS_PASSWORD`: Redis 密码
- `ADMIN_MASTER_KEY`: 管理员认证密钥
- `FLOWER_PASSWORD`: Flower 监控密码

**重要**: 所有密码保存在 `/root/.unlock-vip-credentials`

### 可选配置

```bash
# 文件清理策略
CLEANUP_RETENTION_DAYS=7    # 保留天数
CLEANUP_ENABLED=true        # 是否启用自动清理

# 应用端口
PORT=8000                   # 内部端口，通常不需要修改
```

## 🗂️ 镜像管理

### 构建镜像

```bash
# 1. 进入项目目录
cd /opt/unlock-vip

# 2. 构建镜像
docker build -t unlock-vip:1.0.0 .

# 3. 打标签
docker tag unlock-vip:1.0.0 \
  registry.cn-hangzhou.aliyuncs.com/your-namespace/unlock-vip:1.0.0

# 4. 推送到阿里云
docker login registry.cn-hangzhou.aliyuncs.com
docker push registry.cn-hangzhou.aliyuncs.com/your-namespace/unlock-vip:1.0.0
```

详细说明: [docs/DOCKER_IMAGE_GUIDE.md](docs/DOCKER_IMAGE_GUIDE.md)

### 使用预构建镜像

如果已有公开镜像，可以直接使用：

```bash
# 修改 .env.prod
DOCKER_REGISTRY=your-public-registry
VERSION=1.0.0

# 拉取镜像
docker-compose -f docker-compose.prod.yml pull

# 启动服务
docker-compose -f docker-compose.prod.yml up -d
```

## 🛠️ 日常运维

### 使用管理工具

```bash
# 进入管理工具
/opt/unlock-vip/scripts/manage.sh
```

管理工具提供：
- 📦 容器管理 (启动/停止/重启)
- 🔄 更新和回滚
- 🔍 监控和日志查看
- 💾 数据库备份恢复
- 🛠️ 清理和维护

### 常用命令

```bash
# 查看服务状态
docker-compose -f /opt/unlock-vip/docker-compose.prod.yml ps

# 查看日志
docker-compose -f /opt/unlock-vip/docker-compose.prod.yml logs -f

# 重启服务
docker-compose -f /opt/unlock-vip/docker-compose.prod.yml restart

# 更新服务
docker-compose -f /opt/unlock-vip/docker-compose.prod.yml pull
docker-compose -f /opt/unlock-vip/docker-compose.prod.yml up -d
```

### 备份策略

**自动备份** (每天凌晨 2 点)
```bash
# 查看备份任务
crontab -l

# 查看备份文件
ls -lh /data/backups/mysql/
```

**手动备份**
```bash
/opt/scripts/backup-mysql.sh
```

**恢复数据库**
```bash
gunzip -c backup.sql.gz | \
  docker exec -i unlock-vip-mysql-prod mysql -uroot -p
```

## 📊 监控

### 容器健康状态

```bash
# 查看健康状态
docker ps --format "table {{.Names}}\t{{.Status}}"

# API 健康检查
curl http://localhost/health
```

### 资源使用

```bash
# 实时资源使用
docker stats

# 磁盘使用
df -h /data/unlock-vip
du -sh /data/unlock-vip/*
```

### Flower 监控

访问: `http://your-server-ip:5555`
- 用户名: `admin`
- 密码: 查看 `.env.prod` 中的 `FLOWER_PASSWORD`

**功能**:
- Celery Worker 状态
- 任务执行历史
- 任务队列监控
- 性能指标

## 🔒 安全建议

### 服务器安全

- [ ] 修改 SSH 默认端口
- [ ] 使用密钥登录，禁用密码登录
- [ ] 安装 fail2ban 防止暴力破解
- [ ] 定期更新系统和软件包

### 应用安全

- [ ] 使用强密码 (至少 16 位)
- [ ] 启用 HTTPS (配置 SSL 证书)
- [ ] 限制管理接口访问 IP
- [ ] 定期更新镜像版本

### 数据安全

- [ ] 每天自动备份数据库
- [ ] 备份文件异地存储
- [ ] 加密敏感配置文件
- [ ] 定期检查审计日志

## 🐛 故障排查

### 容器无法启动

```bash
# 查看错误日志
docker-compose -f /opt/unlock-vip/docker-compose.prod.yml logs

# 检查配置
docker-compose -f /opt/unlock-vip/docker-compose.prod.yml config
```

### 数据库连接失败

```bash
# 检查 MySQL 状态
docker ps | grep mysql

# 测试连接
docker exec unlock-vip-api python -c "
from app.core.config import settings
from sqlalchemy import create_engine
print(create_engine(settings.DATABASE_URL).connect())
"
```

### 502 错误

```bash
# 检查 Nginx 配置
docker exec unlock-vip-nginx nginx -t

# 查看 Nginx 日志
docker logs unlock-vip-nginx

# 检查后端服务
curl http://web:8000/health
```

更多故障排查: [ALIYUN_DEPLOYMENT.md#故障排查](ALIYUN_DEPLOYMENT.md#故障排查)

## 📚 相关文档

### 核心文档

- **[ALIYUN_DEPLOYMENT.md](ALIYUN_DEPLOYMENT.md)** - 完整部署手册
  - 服务器要求和配置
  - 详细部署步骤
  - 监控运维指南
  - 故障排查方法
  - 安全加固措施

- **[docs/DOCKER_IMAGE_GUIDE.md](docs/DOCKER_IMAGE_GUIDE.md)** - 镜像管理
  - 镜像构建流程
  - 推送到阿里云 ACR
  - 版本管理策略
  - 镜像优化技巧

### 功能文档

- **[API_QUICK_REFERENCE.md](API_QUICK_REFERENCE.md)** - API 使用说明
- **[ADMIN_SECURITY.md](ADMIN_SECURITY.md)** - 管理员认证
- **[FILE_CLEANUP.md](FILE_CLEANUP.md)** - 文件清理系统
- **[CELERY_BEAT_GUIDE.md](CELERY_BEAT_GUIDE.md)** - 定时任务

### 配置文件

- `docker-compose.prod.yml` - 生产环境编排
- `.env.prod.example` - 环境变量模板
- `nginx/nginx.conf` - Nginx 主配置
- `mysql-conf.d/mysql.cnf` - MySQL 配置

## 🆘 获取帮助

### 检查清单

部署前：
- [ ] 服务器配置满足要求
- [ ] 准备好 CSDN 账号
- [ ] (可选) 准备域名和 SSL 证书
- [ ] 了解基本的 Docker 命令

部署后：
- [ ] 所有容器正常运行
- [ ] API 健康检查通过
- [ ] 数据库连接成功
- [ ] 能够访问 API 文档
- [ ] 修改了默认密码

### 常见问题

**Q: 如何修改已部署服务的配置？**

A: 修改 `.env.prod` 后重启服务:
```bash
docker-compose -f /opt/unlock-vip/docker-compose.prod.yml restart
```

**Q: 如何更新到新版本？**

A: 使用管理工具或手动执行:
```bash
docker-compose -f /opt/unlock-vip/docker-compose.prod.yml pull
docker-compose -f /opt/unlock-vip/docker-compose.prod.yml up -d
```

**Q: 如何查看服务日志？**

A: 
```bash
# 所有服务
docker-compose -f /opt/unlock-vip/docker-compose.prod.yml logs -f

# 特定服务
docker-compose -f /opt/unlock-vip/docker-compose.prod.yml logs -f web
```

**Q: 如何备份数据？**

A: 自动备份每天执行，也可以手动运行:
```bash
/opt/scripts/backup-mysql.sh
```

### 技术支持

遇到问题：
1. 查看本文档和相关文档
2. 检查容器日志
3. 参考故障排查部分
4. 提交 GitHub Issue
5. 联系技术支持

---

## 🎉 部署成功

完成部署后，你将拥有：

- ✅ 完整的 CSDN VIP 文章解锁服务
- ✅ RESTful API 接口
- ✅ 异步任务处理 (Celery)
- ✅ 定时清理机制 (Celery Beat)
- ✅ 完善的监控系统 (Flower)
- ✅ 自动数据备份
- ✅ 管理工具和脚本

**访问 API 文档**: `http://your-server-ip/docs`

**开始使用**: 参考 [API_QUICK_REFERENCE.md](API_QUICK_REFERENCE.md)

祝你使用愉快！🚀
