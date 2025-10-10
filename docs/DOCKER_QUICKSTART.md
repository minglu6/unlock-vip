# 🚀 Docker 快速参考

## 开发环境部署

```bash
# 1. 配置环境变量
cp .env.docker .env
# 编辑 .env 文件

# 2. 启动服务
docker-compose up -d

# 3. 初始化数据库
docker-compose exec web python manage_db.py init

# 4. 创建 API Key
docker-compose exec web python manage_db.py create "测试密钥"

# 5. 查看日志
docker-compose logs -f
```

## 生产环境部署

```bash
# 1. 使用生产配置
cp .env.docker .env
# 编辑 .env，设置强密码

# 2. 申请 SSL 证书
./setup-ssl.sh your-domain.com your-email@example.com

# 3. 更新 nginx.conf 域名配置

# 4. 启动服务
docker-compose -f docker-compose.prod.yml up -d

# 5. 初始化数据库
docker-compose -f docker-compose.prod.yml exec web python manage_db.py init
```

## 常用命令

### 服务管理
```bash
docker-compose up -d              # 启动
docker-compose down               # 停止
docker-compose restart            # 重启
docker-compose ps                 # 状态
docker-compose logs -f            # 日志
```

### 数据库管理
```bash
docker-compose exec web python manage_db.py init         # 初始化
docker-compose exec web python manage_db.py create "名称" # 创建密钥
docker-compose exec web python manage_db.py list         # 列出密钥
docker-compose exec web python manage_db.py stats        # 统计
```

### 容器操作
```bash
docker-compose exec web bash      # 进入容器
docker-compose exec mysql mysql -u root -p  # MySQL
docker-compose build --no-cache   # 重新构建
docker system prune -a            # 清理
```

### 备份恢复
```bash
# 备份数据库
docker-compose exec mysql mysqldump -u unlock_vip -p unlock_vip > backup.sql

# 恢复数据库
docker-compose exec -T mysql mysql -u unlock_vip -p unlock_vip < backup.sql
```

## 服务端口

- **8000** - API 服务
- **3306** - MySQL
- **6379** - Redis
- **5555** - Flower 监控
- **80/443** - Nginx (生产环境)

## 访问地址

- API: <http://localhost:8000>
- 文档: <http://localhost:8000/docs>
- Flower: <http://localhost:5555>

## 目录结构

```
unlock-vip/
├── docker-compose.yml       # 开发环境
├── docker-compose.prod.yml  # 生产环境
├── Dockerfile               # 镜像定义
├── nginx.conf              # Nginx 配置
├── .env                    # 环境变量
├── downloads/              # 下载目录
├── logs/                   # 日志目录
└── certbot/               # SSL 证书
```

## 故障排查

```bash
# 查看服务状态
docker-compose ps

# 查看详细日志
docker-compose logs web
docker-compose logs celery

# 检查健康状态
docker inspect unlock-vip-api | grep Health

# 重启特定服务
docker-compose restart web

# 查看资源使用
docker stats
```

## 环境变量

必须配置：
- `DATABASE_PASSWORD`
- `CSDN_USERNAME`
- `CSDN_PASSWORD`

建议配置：
- `REDIS_PASSWORD`
- `FLOWER_PASSWORD`

## 性能优化

```yaml
# docker-compose.yml 中添加
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
```

## 安全建议

1. 修改所有默认密码
2. 使用 HTTPS (生产环境)
3. 限制端口暴露
4. 定期备份数据
5. 监控日志异常

## 更新部署

```bash
git pull
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 完全清理

```bash
docker-compose down -v        # 删除所有数据
docker system prune -a        # 清理镜像
rm -rf downloads/* logs/*     # 清理文件
```

## 获取帮助

- 查看完整文档: `docs/DOCKER_DEPLOYMENT.md`
- 检查日志: `docker-compose logs -f`
- 验证配置: `docker-compose config`
