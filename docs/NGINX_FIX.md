# Nginx 容器启动问题修复说明

## 问题描述
Nginx 容器在启动时报错: `host not found in upstream "web:8000"` 和 `host not found in upstream "flower:5555"`

## 根本原因
1. Nginx 在启动时就尝试解析配置文件中定义的 upstream 服务器名称
2. 如果此时 web 和 flower 服务还未完全启动,DNS 解析会失败
3. Nginx 启动失败,进入重启循环

## 解决方案

### 1. 修改 nginx 配置(已完成)
- **新配置文件**: `nginx-prod.conf`
- **关键改动**:
  - 添加 Docker 内置 DNS resolver: `resolver 127.0.0.11 valid=30s;`
  - 移除 upstream 块定义
  - 在 location 中使用变量: `set $backend_web web:8000;`
  - 使用变量代理: `proxy_pass http://$backend_web;`

### 2. 修改 docker-compose.prod.yml(已完成)
- 将 nginx 的 depends_on 改为健康检查条件依赖
- 确保 web 服务启动并健康后才启动 nginx
- 为 flower 添加健康检查

### 3. 部署步骤

#### 停止现有容器
```powershell
docker-compose -f docker-compose.prod.yml down
```

#### 清理旧容器(可选)
```powershell
docker-compose -f docker-compose.prod.yml rm -f nginx
```

#### 重新构建和启动
```powershell
docker-compose -f docker-compose.prod.yml up -d --build
```

#### 查看启动日志
```powershell
# 查看所有服务日志
docker-compose -f docker-compose.prod.yml logs -f

# 只查看 nginx 日志
docker-compose -f docker-compose.prod.yml logs -f nginx

# 查看 web 服务日志
docker-compose -f docker-compose.prod.yml logs -f web
```

#### 检查服务状态
```powershell
docker-compose -f docker-compose.prod.yml ps
```

### 4. 验证服务

#### 检查健康状态
```powershell
# 检查 web 服务
docker exec unlock-vip-api-prod curl -f http://localhost:8000/health

# 检查 nginx 配置
docker exec unlock-vip-nginx nginx -t

# 检查 nginx 是否能访问 web
docker exec unlock-vip-nginx wget -O- http://web:8000/health
```

#### 从宿主机测试
```powershell
# 测试 HTTP
curl http://localhost/health

# 如果配置了 SSL,测试 HTTPS
curl https://your-domain.com/health
```

### 5. 技术细节

#### DNS Resolver 说明
- `127.0.0.11` 是 Docker 内置 DNS 服务器地址
- `valid=30s` 表示 DNS 缓存有效期 30 秒
- `ipv6=off` 禁用 IPv6 解析(可选)

#### 变量代理的优势
使用变量 (`set $backend_web web:8000`) 代替直接的 upstream 定义有以下优势:
1. **延迟 DNS 解析**: 在请求时才解析,而不是启动时
2. **自动重试**: 如果服务暂时不可用,下次请求会重新解析
3. **更灵活**: 可以动态修改后端地址

#### 健康检查依赖
```yaml
depends_on:
  web:
    condition: service_healthy  # 等待 web 服务健康检查通过
  flower:
    condition: service_started  # 等待 flower 服务启动
```

### 6. 故障排查

#### 如果 nginx 仍然无法启动
```powershell
# 1. 检查 nginx 配置语法
docker run --rm -v ${PWD}/nginx-prod.conf:/etc/nginx/conf.d/default.conf:ro nginx:alpine nginx -t

# 2. 查看详细错误日志
docker-compose -f docker-compose.prod.yml logs nginx | Select-String "error"

# 3. 进入 nginx 容器调试
docker exec -it unlock-vip-nginx sh
# 在容器内执行
nslookup web
nslookup flower
```

#### 如果 web 服务健康检查失败
```powershell
# 查看 web 服务日志
docker-compose -f docker-compose.prod.yml logs web

# 检查 web 服务端口
docker exec unlock-vip-api-prod netstat -tlnp | Select-String "8000"

# 手动测试健康检查端点
docker exec unlock-vip-api-prod curl -v http://localhost:8000/health
```

#### 如果 DNS 解析失败
```powershell
# 检查 Docker 网络
docker network inspect unlock-vip_unlock-vip-network

# 测试容器间通信
docker exec unlock-vip-nginx ping -c 3 web
docker exec unlock-vip-nginx ping -c 3 flower
```

### 7. 生产环境注意事项

1. **SSL 证书**: 首次部署时,需要先获取 SSL 证书
2. **域名配置**: 修改 nginx-prod.conf 中的 `your-domain.com` 为实际域名
3. **环境变量**: 确保 .env.prod 文件配置正确
4. **防火墙**: 确保端口 80 和 443 已开放
5. **资源限制**: 根据服务器配置调整 deploy.resources 限制

### 8. 回滚方案
如果新配置有问题,可以快速回滚:
```powershell
# 恢复到开发环境配置
docker-compose down
docker-compose up -d

# 或使用旧的 nginx.conf
# 在 docker-compose.prod.yml 中改回:
# - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
```

## 文件清单
- ✅ `nginx-prod.conf` - 新的生产环境 nginx 配置(使用变量代理)
- ✅ `docker-compose.prod.yml` - 更新的 docker-compose 配置(健康检查依赖)
- ✅ `wait-for-services.sh` - 服务等待脚本(备用方案)
- 📝 `nginx.conf` - 原配置文件(保留作为备份)

## 总结
通过以上修改,nginx 容器将能够正确启动:
1. 使用 Docker DNS resolver 动态解析服务名称
2. 通过变量延迟 DNS 解析到请求时
3. 通过健康检查确保依赖服务就绪
4. 添加错误处理和重试机制

这样可以避免因服务启动顺序导致的 DNS 解析失败问题。
