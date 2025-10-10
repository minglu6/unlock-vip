# 🛠️ 工具脚本

项目管理和维护工具脚本集合。

## 📜 脚本列表

### 数据库管理

#### `manage_db.py`
数据库管理工具，支持创建表、清空数据等操作。

```bash
python scripts/manage_db.py
```

**功能:**
- 创建数据库表结构
- 清空数据
- 数据库状态检查
- 数据迁移

#### `list_api_keys.py`
查看数据库中的所有API密钥。

```bash
python scripts/list_api_keys.py
```

**输出信息:**
- API密钥ID
- 密钥值
- 密钥名称
- 状态（启用/禁用）
- 速率限制
- 创建时间

### 密钥生成

#### `generate_admin_key.py`
生成管理员API密钥。

```bash
python scripts/generate_admin_key.py
```

**特性:**
- 生成高强度加密密钥
- 自动保存到数据库
- 无速率限制
- 管理员权限

#### `generate_test_key.py`
生成测试用API密钥。

```bash
python scripts/generate_test_key.py
```

**特性:**
- 用于测试环境
- 可设置速率限制
- 可设置过期时间

### 部署脚本

#### `manage.sh`
Linux/Mac环境的管理脚本。

```bash
./scripts/manage.sh [command]
```

**命令:**
- `start` - 启动服务
- `stop` - 停止服务
- `restart` - 重启服务
- `logs` - 查看日志
- `status` - 检查状态

## 🔧 使用示例

### 初始化数据库

```bash
# 1. 创建数据库表
python scripts/manage_db.py

# 2. 生成管理员密钥
python scripts/generate_admin_key.py

# 3. 查看密钥
python scripts/list_api_keys.py
```

### 密钥管理

```bash
# 生成测试密钥
python scripts/generate_test_key.py

# 查看所有密钥
python scripts/list_api_keys.py

# 在代码中禁用密钥
python -c "from app.db.database import SessionLocal; from app.db.models import APIKey; \
db = SessionLocal(); key = db.query(APIKey).filter_by(id=1).first(); \
key.is_active = False; db.commit(); print('密钥已禁用')"
```

## ⚙️ 配置要求

所有脚本需要以下环境变量（在`.env`文件中配置）:

```env
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/unlock_vip
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=unlock_vip
```

## 📝 注意事项

1. **数据库连接**: 确保数据库服务正在运行
2. **权限管理**: 管理员密钥权限很高，妥善保管
3. **测试密钥**: 测试密钥应该在生产环境禁用
4. **日志记录**: 所有操作都会记录到日志

## 🔐 安全建议

- ⚠️ **不要提交密钥到Git仓库**
- ⚠️ **定期更换管理员密钥**
- ⚠️ **限制脚本执行权限**
- ⚠️ **记录所有密钥操作**

## 📞 支持

如有问题，请查看[文档中心](../docs/README.md)或提交Issue。
