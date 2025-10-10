# MySQL 认证错误修复指南

## 错误信息
```
Access denied for user 'unlock_vip_user'@'...' (using password: YES)
```

## 问题原因
1. MySQL 容器的环境变量配置错误,使用了错误的密码变量
2. MySQL 用户只在容器**首次启动**时创建,修改环境变量后需要重新初始化

## 已修复的问题
✅ 修改 `docker-compose.prod.yml`:
- `MYSQL_ROOT_PASSWORD: ${DATABASE_PASSWORD}` → `${DATABASE_ROOT_PASSWORD}`
- 健康检查命令也使用正确的 root 密码

## 修复步骤

### 方法 1: 使用 PowerShell 脚本(推荐)

```powershell
# 运行修复脚本
.\fix-mysql.ps1
```

### 方法 2: 手动执行

#### 1. 停止所有容器
```powershell
docker-compose -f docker-compose.prod.yml down
```

#### 2. 删除 MySQL 数据卷
⚠️ **警告: 这会删除所有数据库数据!**

```powershell
# 查看当前数据卷
docker volume ls | Select-String "mysql"

# 删除 MySQL 数据卷
docker volume rm unlock-vip_mysql_data
```

#### 3. 验证 .env.prod 配置
确保 `.env.prod` 包含:
```bash
DATABASE_ROOT_PASSWORD=Root2025103         # Root 密码(去掉@符号)
DATABASE_NAME=unlock_vip
DATABASE_USER=unlock_vip_user
DATABASE_PASSWORD=User2025103              # 用户密码(去掉@符号)
```

#### 4. 重新启动 MySQL
```powershell
# 只启动 MySQL 和 Redis
docker-compose -f docker-compose.prod.yml up -d mysql redis

# 查看 MySQL 日志,确认启动成功
docker-compose -f docker-compose.prod.yml logs -f mysql
```

等待看到以下日志:
```
[Server] /usr/sbin/mysqld: ready for connections
```

#### 5. 验证 MySQL 用户
```powershell
# 进入 MySQL 容器
docker exec -it unlock-vip-mysql-prod mysql -uroot -p

# 输入 root 密码: Root2025103
# 然后执行以下 SQL:
```

```sql
-- 查看所有用户
SELECT user, host FROM mysql.user;

-- 应该看到:
-- +------------------+-----------+
-- | user             | host      |
-- +------------------+-----------+
-- | unlock_vip_user  | %         |
-- | root             | localhost |
-- +------------------+-----------+

-- 查看用户权限
SHOW GRANTS FOR 'unlock_vip_user'@'%';

-- 退出
exit;
```

#### 6. 测试连接
```powershell
# 从 web 容器测试连接(先启动 web 容器)
docker-compose -f docker-compose.prod.yml up -d web

# 进入 web 容器
docker exec -it unlock-vip-api-prod python

# 在 Python 中测试
```

```python
import pymysql
conn = pymysql.connect(
    host='mysql',
    user='unlock_vip_user',
    password='User2025103',
    database='unlock_vip'
)
print("连接成功!")
conn.close()
exit()
```

#### 7. 启动所有服务
```powershell
docker-compose -f docker-compose.prod.yml up -d
```

#### 8. 查看服务状态
```powershell
# 查看所有容器状态
docker-compose -f docker-compose.prod.yml ps

# 查看 web 服务日志
docker-compose -f docker-compose.prod.yml logs -f web
```

## 方法 3: 保留数据的修复(高级)

如果已有重要数据,不想删除数据卷:

### 1. 连接到 MySQL 容器手动创建用户
```powershell
# 进入 MySQL 容器
docker exec -it unlock-vip-mysql-prod mysql -uroot -p
```

```sql
-- 创建用户(如果不存在)
CREATE USER IF NOT EXISTS 'unlock_vip_user'@'%' IDENTIFIED BY 'User2025103';

-- 授予权限
GRANT ALL PRIVILEGES ON unlock_vip.* TO 'unlock_vip_user'@'%';

-- 刷新权限
FLUSH PRIVILEGES;

-- 验证
SHOW GRANTS FOR 'unlock_vip_user'@'%';

exit;
```

### 2. 重启 web 服务
```powershell
docker-compose -f docker-compose.prod.yml restart web
```

## 常见问题排查

### Q1: 数据卷删除失败
```powershell
# 错误: volume is in use
# 解决: 确保所有容器已停止
docker-compose -f docker-compose.prod.yml down
docker ps -a | Select-String "unlock-vip"

# 如果还有容器,强制删除
docker rm -f unlock-vip-mysql-prod
```

### Q2: 容器启动后立即退出
```powershell
# 查看详细日志
docker-compose -f docker-compose.prod.yml logs mysql

# 常见原因:
# - 环境变量未正确加载
# - 端口冲突
# - 数据卷权限问题
```

### Q3: 仍然认证失败
```powershell
# 检查实际使用的环境变量
docker exec unlock-vip-mysql-prod env | Select-String "MYSQL"

# 应该看到:
# MYSQL_ROOT_PASSWORD=Root2025103
# MYSQL_DATABASE=unlock_vip
# MYSQL_USER=unlock_vip_user
# MYSQL_PASSWORD=User2025103
```

### Q4: 如何备份现有数据
```powershell
# 在删除数据卷前备份
docker exec unlock-vip-mysql-prod mysqldump -uroot -p unlock_vip > backup.sql

# 恢复数据
docker exec -i unlock-vip-mysql-prod mysql -uroot -p unlock_vip < backup.sql
```

## 验证修复成功

修复后应该看到:
1. ✅ MySQL 容器健康检查通过
2. ✅ Web 服务成功连接数据库
3. ✅ 数据库表自动创建
4. ✅ 没有认证错误日志

```powershell
# 快速验证
docker-compose -f docker-compose.prod.yml ps

# 所有服务应该显示 "healthy" 或 "running"
```

## 预防措施

1. **使用正确的环境变量名称**
   - Root 密码: `DATABASE_ROOT_PASSWORD`
   - 用户密码: `DATABASE_PASSWORD`

2. **避免密码中使用特殊字符**
   - ❌ 避免: `@`, `:`, `/`, `#` 等
   - ✅ 推荐: 字母、数字、下划线

3. **在修改环境变量后重新初始化**
   - MySQL 用户配置只在首次启动时生效
   - 修改后需要删除数据卷重新创建

4. **定期备份数据**
   ```powershell
   # 定期运行备份
   docker exec unlock-vip-mysql-prod mysqldump -uroot -p unlock_vip > "backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').sql"
   ```
