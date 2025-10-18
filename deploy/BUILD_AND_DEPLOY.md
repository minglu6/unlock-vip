# 本地构建并部署到服务器指南

本指南说明如何在本地构建 Docker 镜像，然后上传到服务器运行。

## 方案优势

- ✅ 本地构建速度快，可以看到详细日志
- ✅ 避免服务器构建占用资源
- ✅ 可以在本地测试镜像
- ✅ 部署更快速

---

## 步骤一：本地构建镜像

### Windows 用户

在项目根目录双击运行：
```
build-local.bat
```

或在 PowerShell/CMD 中执行：
```powershell
cd D:\Projects\Personal\unlock-vip
.\build-local.bat
```

### Linux/Mac 用户

```bash
cd /path/to/unlock-vip

# 给脚本执行权限
chmod +x build-local.sh

# 运行构建脚本
./build-local.sh
```

### 手动构建（所有平台）

```bash
# 1. 构建镜像
docker build -t unlock-vip:latest .

# 2. 导出镜像
docker save unlock-vip:latest | gzip > unlock-vip-image.tar.gz

# 3. 查看文件大小
ls -lh unlock-vip-image.tar.gz  # Linux/Mac
dir unlock-vip-image.tar.gz     # Windows
```

构建完成后，会生成 `unlock-vip-image.tar.gz` 文件（约 100-200MB）。

---

## 步骤二：上传镜像到服务器

### 方法1：使用 SCP 上传

```bash
scp unlock-vip-image.tar.gz root@175.24.164.85:/opt/unlock-vip/
```

### 方法2：使用 SFTP 工具上传

使用 WinSCP、FileZilla 等工具，将文件上传到服务器的 `/opt/unlock-vip/` 目录。

### 方法3：使用一键上传脚本（推荐）

创建 `upload.bat`（Windows）或 `upload.sh`（Linux/Mac）:

**Windows (upload.bat):**
```batch
@echo off
echo 正在上传镜像到服务器...
scp unlock-vip-image.tar.gz root@175.24.164.85:/opt/unlock-vip/
echo 上传完成！
pause
```

**Linux/Mac (upload.sh):**
```bash
#!/bin/bash
echo "正在上传镜像到服务器..."
scp unlock-vip-image.tar.gz root@175.24.164.85:/opt/unlock-vip/
echo "上传完成！"
```

---

## 步骤三：在服务器上部署

SSH 连接到服务器：
```bash
ssh root@175.24.164.85
```

然后执行：

```bash
# 1. 进入项目目录
cd /opt/unlock-vip

# 2. 停止旧容器
docker-compose down

# 3. 加载镜像
docker load < unlock-vip-image.tar.gz

# 4. 验证镜像
docker images | grep unlock-vip

# 5. 启动服务
docker-compose up -d

# 6. 查看日志
docker-compose logs -f

# 7. 测试服务
curl http://localhost/health
```

---

## 一键部署脚本（服务器端）

在服务器上创建 `load-and-run.sh`:

```bash
#!/bin/bash
# 服务器端：加载镜像并启动服务

set -e

echo "========================================"
echo "  加载镜像并启动服务"
echo "========================================"

cd /opt/unlock-vip

echo "[1/5] 停止旧容器..."
docker-compose down 2>/dev/null || true

echo "[2/5] 加载新镜像..."
if [ -f "unlock-vip-image.tar.gz" ]; then
    docker load < unlock-vip-image.tar.gz
else
    echo "错误: 未找到镜像文件 unlock-vip-image.tar.gz"
    exit 1
fi

echo "[3/5] 清理旧镜像..."
docker image prune -f

echo "[4/5] 启动服务..."
docker-compose up -d

echo "[5/5] 等待服务启动..."
sleep 5

echo ""
echo "容器状态:"
docker-compose ps

echo ""
echo "测试服务:"
curl -s http://localhost/health

echo ""
echo "========================================"
echo "  部署完成！"
echo "========================================"
echo ""
echo "访问地址:"
echo "  - API文档: http://175.24.164.85/docs"
echo "  - 健康检查: http://175.24.164.85/health"
echo ""
echo "查看日志: docker-compose logs -f"
echo ""
```

使用方法：
```bash
chmod +x load-and-run.sh
./load-and-run.sh
```

---

## 完整工作流程示例

### 本地（Windows）

```powershell
# 1. 构建镜像
cd D:\Projects\Personal\unlock-vip
.\build-local.bat

# 2. 上传到服务器
scp unlock-vip-image.tar.gz root@175.24.164.85:/opt/unlock-vip/
```

### 服务器端

```bash
# 3. SSH 连接
ssh root@175.24.164.85

# 4. 部署
cd /opt/unlock-vip
docker load < unlock-vip-image.tar.gz
docker-compose down
docker-compose up -d

# 5. 验证
docker-compose ps
curl http://localhost/health
```

### 浏览器验证

访问 http://175.24.164.85/docs

---

## 本地测试镜像（可选）

在上传到服务器前，可以先在本地测试：

```bash
# 1. 启动容器测试
docker run -p 8001:8001 \
  -v $(pwd)/cookies.json:/app/cookies.json:ro \
  unlock-vip:latest

# 2. 测试访问
curl http://localhost:8001/health

# 3. 停止测试
# Ctrl+C
```

---

## 故障排查

### 镜像构建失败

```bash
# 查看详细构建日志
docker build --progress=plain --no-cache -t unlock-vip:latest .
```

### 上传速度慢

```bash
# 使用压缩上传（已经压缩过了）
# 或使用更快的网络/VPN
```

### 服务器加载镜像失败

```bash
# 检查文件完整性
ls -lh unlock-vip-image.tar.gz

# 重新下载或上传
# 确保文件大小正确
```

### 容器启动失败

```bash
# 查看详细日志
docker-compose logs

# 检查配置文件
cat docker-compose.yml

# 检查 cookies.json
cat cookies.json
```

---

## 更新部署流程

每次代码更新后：

1. **本地拉取代码**
   ```bash
   git pull
   ```

2. **重新构建镜像**
   ```bash
   ./build-local.bat  # Windows
   ./build-local.sh   # Linux/Mac
   ```

3. **上传新镜像**
   ```bash
   scp unlock-vip-image.tar.gz root@175.24.164.85:/opt/unlock-vip/
   ```

4. **服务器重新部署**
   ```bash
   ssh root@175.24.164.85
   cd /opt/unlock-vip
   docker-compose down
   docker load < unlock-vip-image.tar.gz
   docker-compose up -d
   ```

---

## 清理资源

### 本地清理

```bash
# 删除镜像文件
rm unlock-vip-image.tar.gz

# 清理 Docker 缓存
docker system prune -a
```

### 服务器清理

```bash
# 清理旧镜像
docker image prune -a

# 清理容器
docker container prune
```

---

## 进阶：使用 Docker Registry

如果频繁部署，建议使用 Docker Registry：

### 使用 Docker Hub

```bash
# 1. 登录 Docker Hub
docker login

# 2. 标记镜像
docker tag unlock-vip:latest yourusername/unlock-vip:latest

# 3. 推送镜像
docker push yourusername/unlock-vip:latest

# 4. 服务器拉取
ssh root@175.24.164.85
docker pull yourusername/unlock-vip:latest
docker-compose up -d
```

### 使用阿里云容器镜像服务

```bash
# 1. 登录阿里云
docker login --username=your_username registry.cn-hangzhou.aliyuncs.com

# 2. 标记并推送
docker tag unlock-vip:latest registry.cn-hangzhou.aliyuncs.com/your_namespace/unlock-vip:latest
docker push registry.cn-hangzhou.aliyuncs.com/your_namespace/unlock-vip:latest

# 3. 服务器拉取
docker pull registry.cn-hangzhou.aliyuncs.com/your_namespace/unlock-vip:latest
```
