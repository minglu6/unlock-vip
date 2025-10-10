# 🔧 快速修复指南

## 当前问题
```
Access denied for user 'unlock_vip_user' (using password: YES)
```

## 原因
MySQL 容器环境变量配置错误,用户未正确创建。

## 快速修复(3 步)

### 1️⃣ 停止并删除 MySQL 数据
```powershell
docker-compose -f docker-compose.prod.yml down
docker volume rm unlock-vip_mysql_data
```

### 2️⃣ 确认 .env.prod 配置正确
```bash
# 密码中不要包含 @ 符号
DATABASE_ROOT_PASSWORD=Root2025103
DATABASE_USER=unlock_vip_user
DATABASE_PASSWORD=User2025103
DATABASE_NAME=unlock_vip
```

### 3️⃣ 重新启动
```powershell
docker-compose -f docker-compose.prod.yml up -d
```

### 4️⃣ 验证
```powershell
# 查看日志
docker-compose -f docker-compose.prod.yml logs web

# 应该看到 "数据库初始化成功" 而不是认证错误
```

## 详细文档
参见: `docs/MYSQL_AUTH_FIX.md`

## 修改的文件
- ✅ `docker-compose.prod.yml` - 修复 MySQL 环境变量
- ✅ `app/core/config.py` - 自动编码密码特殊字符
