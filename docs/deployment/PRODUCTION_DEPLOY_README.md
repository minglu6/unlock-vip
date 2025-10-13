# 🚀 生产环境部署指南

## 📋 快速导航

- [部署前准备](#部署前准备)
- [快速部署](#快速部署)
- [详细文档](#详细文档)
- [常见问题](#常见问题)

---

## 部署前准备

### 1. 运行检查脚本

```bash
# 在本地运行，检查所有必需文件
bash pre-deploy-check.sh
```

### 2. 准备必需文件

✅ **cookies.json** - CSDN登录状态
- 从浏览器导出CSDN cookies
- 确保包含 `UserToken` 等关键字段

✅ **.env.prod** - 生产环境配置
```bash
cp .env.prod.example .env.prod
# 编辑修改所有密码和密钥
nano .env.prod
```

**必须修改的配置**:
- `MYSQL_ROOT_PASSWORD` - MySQL root密码
- `MYSQL_PASSWORD` - 应用数据库密码
- `REDIS_PASSWORD` - Redis密码
- `SECRET_KEY` - 应用密钥（使用 `openssl rand -hex 32` 生成）
- `ADMIN_KEY` - 管理员密钥

### 3. 检查清单

- [ ] cookies.json 文件已准备
- [ ] .env.prod 所有密码已修改
- [ ] 服务器满足最低配置（2GB内存，2核CPU）
- [ ] 服务器已安装Docker和Docker Compose
- [ ] 防火墙已开放必要端口（80, 443, 8000）
- [ ] 域名DNS已解析（如使用域名）

---

## 快速部署

### 方式一：一键部署脚本（推荐）

```bash
# 1. 连接服务器
ssh root@your-server-ip

# 2. 下载项目
cd /opt
git clone https://github.com/your-username/unlock-vip.git
cd unlock-vip

# 3. 运行一键部署脚本
bash deploy-production.sh
```

脚本会自动：
- ✅ 安装Docker和Docker Compose
- ✅ 配置环境变量
- ✅ 配置防火墙
- ✅ 启动所有服务
- ✅ 配置Nginx反向代理（可选）
- ✅ 配置SSL证书（可选）
- ✅ 配置自动备份（可选）

### 方式二：手动部署

详见: [完整部署文档](docs/ALIYUN_PRODUCTION_DEPLOY.md)

---

## 部署验证

### 1. 检查容器状态

```bash
docker-compose -f docker-compose.prod.yml ps
```

所有容器状态应为 `Up (healthy)`

### 2. 测试API

```bash
# 健康检查
curl http://localhost:8000/health

# 文件服务检查
curl -H "X-API-Key: your-key" http://localhost:8000/api/file/health
```

### 3. 查看日志

```bash
# 查看应用日志
docker-compose -f docker-compose.prod.yml logs -f app

# 查看Celery日志
docker-compose -f docker-compose.prod.yml logs -f celery
```

---

## 详细文档

### 部署文档
- 📘 [阿里云生产环境部署指南](docs/ALIYUN_PRODUCTION_DEPLOY.md) - 完整的生产部署文档
- 📗 [Docker快速部署](docs/DOCKER_QUICKSTART.md) - Docker部署快速指南
- 📙 [部署检查清单](docs/DEPLOYMENT_CHECKLIST.md) - 上线前检查项

### 配置文档
- ⚙️ [环境变量配置](.env.prod.example) - 所有环境变量说明
- 🔧 [线程池配置](docs/THREAD_POOL_CONFIG.md) - 性能调优配置
- 🔒 [安全配置](docs/ADMIN_SECURITY.md) - 安全最佳实践

### API文档
- 📚 [API完整文档](docs/API_QUICK_REFERENCE.md) - 所有API端点
- 📦 [文件下载API](docs/FILE_DOWNLOAD_API.md) - 文件下载服务文档
- 📮 [Postman Collection](docs/POSTMAN_COLLECTION.json) - API测试集合

### 运维文档
- 🔄 [Celery任务](docs/CELERY_BEAT_GUIDE.md) - 定时任务配置
- 🗑️ [文件清理](docs/FILE_CLEANUP.md) - 自动清理机制
- 📊 [监控和日志](#监控和日志) - 监控配置指南

---

## 服务管理

### 启动服务

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 停止服务

```bash
docker-compose -f docker-compose.prod.yml down
```

### 重启服务

```bash
docker-compose -f docker-compose.prod.yml restart
```

### 更新部署

```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

### 查看日志

```bash
# 所有服务日志
docker-compose -f docker-compose.prod.yml logs -f

# 特定服务日志
docker-compose -f docker-compose.prod.yml logs -f app
docker-compose -f docker-compose.prod.yml logs -f celery
docker-compose -f docker-compose.prod.yml logs -f mysql
```

---

## 监控和日志

### 日志位置

- **应用日志**: `/var/log/unlock-vip/app.log`
- **Nginx日志**: `/var/log/nginx/`
- **Docker日志**: 使用 `docker logs` 命令查看

### 监控指标

关键监控项:
- CPU使用率
- 内存使用率
- 磁盘空间
- 数据库连接数
- Redis内存使用
- API响应时间

### 告警配置

建议配置以下告警:
- 磁盘空间 < 10%
- 内存使用 > 80%
- API错误率 > 5%
- 服务不可用

---

## 备份和恢复

### 自动备份

部署脚本会配置每日自动备份（凌晨2点）

手动备份:
```bash
# 运行备份脚本
/opt/backup_unlock_vip.sh
```

### 数据库备份

```bash
# 备份
docker exec unlock-vip-mysql mysqldump -u root -p unlock_vip > backup.sql

# 恢复
docker exec -i unlock-vip-mysql mysql -u root -p unlock_vip < backup.sql
```

### 备份位置

- 自动备份: `/opt/backups/`
- 保留策略: 最近7天

---

## 性能优化

### 1. 增加工作进程

修改 `docker-compose.prod.yml`:
```yaml
command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 8
```

### 2. 调整线程池

修改 `app/services/file_service.py`:
```python
max_workers=8  # 增加到8个线程
```

### 3. 配置Nginx缓存

参考 [部署文档](docs/ALIYUN_PRODUCTION_DEPLOY.md#性能优化)

### 4. 数据库优化

- 定期清理日志表
- 添加索引
- 调整连接池大小

---

## 安全建议

### 必做项

✅ 修改所有默认密码
✅ 限制管理接口访问（IP白名单）
✅ 配置SSL证书
✅ 启用防火墙
✅ 定期更新系统和依赖

### 推荐项

- 配置fail2ban防止暴力破解
- 使用非root用户运行服务
- 定期审计日志
- 配置自动安全更新
- 使用密钥登录SSH（禁用密码登录）

---

## 常见问题

### 1. 容器无法启动

**问题**: 容器启动后立即退出

**排查**:
```bash
# 查看容器日志
docker-compose -f docker-compose.prod.yml logs app

# 检查配置文件
docker-compose -f docker-compose.prod.yml config
```

**解决**: 检查环境变量配置，确保数据库连接信息正确

### 2. 数据库连接失败

**问题**: API报错 "Database connection failed"

**排查**:
```bash
# 检查MySQL状态
docker-compose -f docker-compose.prod.yml ps mysql

# 测试连接
docker exec -it unlock-vip-mysql mysql -u root -p
```

**解决**: 检查 .env.prod 中的数据库配置

### 3. 端口被占用

**问题**: 启动时提示端口冲突

**排查**:
```bash
# 查看端口占用
netstat -tlnp | grep 8000
```

**解决**: 
- 修改docker-compose.yml中的端口映射
- 或停止占用端口的服务

### 4. cookies过期

**问题**: 文件下载返回 "请登录后操作"

**解决**:
1. 重新导出cookies.json
2. 上传到服务器
3. 重启服务

### 5. 磁盘空间不足

**问题**: 日志或下载文件占满磁盘

**解决**:
```bash
# 清理Docker无用镜像
docker system prune -a

# 清理下载文件
find /opt/unlock-vip/downloads -mtime +7 -delete

# 清理日志
find /var/log -name "*.log" -mtime +30 -delete
```

---

## 技术支持

### 获取帮助

1. 📖 查看文档: [docs/README.md](docs/README.md)
2. 🔍 搜索Issue: [GitHub Issues](https://github.com/your-username/unlock-vip/issues)
3. 💬 提交新Issue: 描述问题、环境、复现步骤
4. 📧 联系维护者

### 问题报告模板

```markdown
## 环境信息
- 系统: Ubuntu 20.04
- Docker版本: 20.10.x
- 部署方式: Docker Compose

## 问题描述
[详细描述问题]

## 复现步骤
1. ...
2. ...
3. ...

## 错误日志
```
[粘贴相关日志]
```

## 已尝试的解决方法
- [x] 重启服务
- [ ] 检查配置文件
- [ ] ...
```

---

## 更新日志

### v2.0.0 (2025-10-03)
- ✨ 新增文件下载服务
- ✨ 添加线程池并发处理
- 📝 完善生产环境部署文档
- 🔧 优化Docker配置
- 🔒 增强安全配置

### v1.0.0
- 🎉 首次发布
- ✨ 基础文章下载功能
- ✨ Celery异步任务
- 📝 基础文档

---

## 许可证

[MIT License](LICENSE)

---

**最后更新**: 2025-10-03
**维护者**: Your Name
**项目主页**: https://github.com/your-username/unlock-vip
