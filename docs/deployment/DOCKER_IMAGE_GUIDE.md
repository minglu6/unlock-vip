# Unlock VIP 镜像构建和发布指南

## 📦 镜像说明

### 镜像信息
- **基础镜像**: python:3.11-slim
- **应用框架**: FastAPI + Celery
- **构建方式**: 多阶段构建
- **大小**: ~150MB (压缩后)

---

## 🏗️ 构建镜像

### 1. 本地构建

```bash
# 进入项目目录
cd /path/to/unlock-vip

# 构建镜像
docker build -t unlock-vip:1.0.0 .

# 查看镜像
docker images unlock-vip
```

### 2. 多架构构建

```bash
# 创建 buildx builder
docker buildx create --name mybuilder --use

# 构建多架构镜像
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t unlock-vip:1.0.0 \
  --push \
  .
```

### 3. 使用构建参数

```bash
# 指定 Python 版本
docker build \
  --build-arg PYTHON_VERSION=3.11 \
  -t unlock-vip:1.0.0 \
  .

# 指定清华源加速
docker build \
  --build-arg PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
  -t unlock-vip:1.0.0 \
  .
```

---

## 📤 推送镜像

### 方式一: 阿里云容器镜像服务 (ACR)

#### 1. 开通服务

1. 登录阿里云控制台
2. 搜索 **容器镜像服务**
3. 选择 **个人版** (免费)
4. 创建命名空间: `unlock-vip`

#### 2. 配置访问凭证

```bash
# 设置密码 (在控制台设置)
# 访问控制 -> 访问凭证 -> 设置固定密码

# 登录镜像仓库
docker login \
  --username=your-aliyun-username \
  registry.cn-hangzhou.aliyuncs.com
```

#### 3. 推送镜像

```bash
# 打标签
docker tag unlock-vip:1.0.0 \
  registry.cn-hangzhou.aliyuncs.com/unlock-vip/unlock-vip:1.0.0

docker tag unlock-vip:1.0.0 \
  registry.cn-hangzhou.aliyuncs.com/unlock-vip/unlock-vip:latest

# 推送
docker push registry.cn-hangzhou.aliyuncs.com/unlock-vip/unlock-vip:1.0.0
docker push registry.cn-hangzhou.aliyuncs.com/unlock-vip/unlock-vip:latest
```

#### 4. 设置公开访问 (可选)

在阿里云控制台:
1. 进入 **容器镜像服务**
2. 选择 **镜像仓库**
3. 选择仓库 `unlock-vip`
4. 设置为 **公开**

#### 5. 拉取镜像

```bash
# 公开仓库无需登录
docker pull registry.cn-hangzhou.aliyuncs.com/unlock-vip/unlock-vip:latest

# 私有仓库需要先登录
docker login registry.cn-hangzhou.aliyuncs.com
docker pull registry.cn-hangzhou.aliyuncs.com/unlock-vip/unlock-vip:latest
```

### 方式二: Docker Hub

#### 1. 注册账号

访问 https://hub.docker.com 注册账号

#### 2. 登录

```bash
docker login
```

#### 3. 推送镜像

```bash
# 打标签
docker tag unlock-vip:1.0.0 your-dockerhub-username/unlock-vip:1.0.0
docker tag unlock-vip:1.0.0 your-dockerhub-username/unlock-vip:latest

# 推送
docker push your-dockerhub-username/unlock-vip:1.0.0
docker push your-dockerhub-username/unlock-vip:latest
```

### 方式三: 私有镜像仓库

使用 Harbor 或其他私有仓库:

```bash
# 登录
docker login your-registry.com

# 打标签
docker tag unlock-vip:1.0.0 your-registry.com/unlock-vip/unlock-vip:1.0.0

# 推送
docker push your-registry.com/unlock-vip/unlock-vip:1.0.0
```

---

## 🚀 自动化构建

### GitHub Actions

创建 `.github/workflows/docker-build.yml`:

```yaml
name: Docker Build and Push

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Login to Aliyun Container Registry
        uses: docker/login-action@v2
        with:
          registry: registry.cn-hangzhou.aliyuncs.com
          username: ${{ secrets.ALIYUN_USERNAME }}
          password: ${{ secrets.ALIYUN_PASSWORD }}
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: registry.cn-hangzhou.aliyuncs.com/unlock-vip/unlock-vip
          tags: |
            type=ref,event=branch
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
      
      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

### GitLab CI/CD

创建 `.gitlab-ci.yml`:

```yaml
variables:
  DOCKER_REGISTRY: registry.cn-hangzhou.aliyuncs.com
  IMAGE_NAME: unlock-vip/unlock-vip

stages:
  - build
  - push

build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t $IMAGE_NAME:$CI_COMMIT_SHA .
    - docker tag $IMAGE_NAME:$CI_COMMIT_SHA $IMAGE_NAME:latest
  only:
    - main
    - tags

push:
  stage: push
  image: docker:latest
  services:
    - docker:dind
  before_script:
    - docker login -u $ALIYUN_USERNAME -p $ALIYUN_PASSWORD $DOCKER_REGISTRY
  script:
    - docker push $DOCKER_REGISTRY/$IMAGE_NAME:$CI_COMMIT_SHA
    - docker push $DOCKER_REGISTRY/$IMAGE_NAME:latest
  only:
    - main
    - tags
```

---

## 🔍 镜像优化

### 1. 减小镜像大小

#### 使用 .dockerignore

创建 `.dockerignore` 文件:
```
.git
.gitignore
.env*
*.md
tests/
docs/
downloads/
logs/
*.pyc
__pycache__
.pytest_cache
.vscode
.idea
*.log
```

#### 多阶段构建

优化 Dockerfile:
```dockerfile
# 构建阶段
FROM python:3.11-slim AS builder

WORKDIR /build

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# 运行阶段
FROM python:3.11-slim

WORKDIR /app

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 从构建阶段复制依赖
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# 复制应用代码
COPY . .

# 运行应用
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 清理不必要文件

```dockerfile
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /tmp/* && \
    rm -rf /root/.cache
```

### 2. 使用镜像缓存

```bash
# 使用 buildkit 缓存
export DOCKER_BUILDKIT=1
docker build --cache-from unlock-vip:latest -t unlock-vip:1.0.0 .

# 使用外部缓存
docker build \
  --cache-from type=registry,ref=registry.example.com/unlock-vip:cache \
  --cache-to type=registry,ref=registry.example.com/unlock-vip:cache,mode=max \
  -t unlock-vip:1.0.0 .
```

### 3. 压缩镜像

```bash
# 导出镜像
docker save unlock-vip:1.0.0 | gzip > unlock-vip-1.0.0.tar.gz

# 导入镜像
gunzip -c unlock-vip-1.0.0.tar.gz | docker load
```

---

## 📊 镜像管理

### 版本管理

采用语义化版本 (Semantic Versioning):

```bash
# 主版本.次版本.修订号
docker build -t unlock-vip:1.0.0 .    # 正式版本
docker build -t unlock-vip:1.0.1 .    # Bug 修复
docker build -t unlock-vip:1.1.0 .    # 新功能
docker build -t unlock-vip:2.0.0 .    # 重大变更

# 开发版本
docker build -t unlock-vip:1.0.0-beta .
docker build -t unlock-vip:1.0.0-rc1 .

# 特殊标签
docker build -t unlock-vip:latest .   # 最新稳定版
docker build -t unlock-vip:dev .      # 开发版本
```

### 镜像清理

```bash
# 删除未使用的镜像
docker image prune -a

# 删除特定镜像
docker rmi unlock-vip:1.0.0

# 删除悬空镜像
docker image prune

# 查看镜像大小
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
```

### 镜像扫描

使用 Trivy 扫描漏洞:

```bash
# 安装 Trivy
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh

# 扫描镜像
trivy image unlock-vip:1.0.0

# 输出为 JSON
trivy image -f json -o results.json unlock-vip:1.0.0

# 仅显示高危漏洞
trivy image --severity HIGH,CRITICAL unlock-vip:1.0.0
```

---

## 🧪 镜像测试

### 本地测试

```bash
# 运行测试容器
docker run --rm \
  -e DATABASE_HOST=localhost \
  -e REDIS_HOST=localhost \
  unlock-vip:1.0.0 \
  python -m pytest tests/

# 交互式测试
docker run -it --rm unlock-vip:1.0.0 bash

# 健康检查测试
docker run -d --name test unlock-vip:1.0.0
docker exec test curl -f http://localhost:8000/health
docker rm -f test
```

### 集成测试

使用 docker-compose 进行完整测试:

```bash
# 启动测试环境
docker-compose -f docker-compose.test.yml up -d

# 运行测试
docker-compose -f docker-compose.test.yml exec web pytest

# 清理
docker-compose -f docker-compose.test.yml down -v
```

---

## 📚 最佳实践

### 1. 安全性

- ✅ 使用官方基础镜像
- ✅ 定期更新镜像
- ✅ 扫描安全漏洞
- ✅ 不在镜像中包含敏感信息
- ✅ 使用非 root 用户运行

### 2. 性能

- ✅ 使用多阶段构建减小大小
- ✅ 合理使用缓存层
- ✅ 清理不必要的文件
- ✅ 使用 .dockerignore

### 3. 可维护性

- ✅ 明确的版本标签
- ✅ 详细的构建文档
- ✅ 自动化构建流程
- ✅ 健康检查配置

---

## 🔗 相关资源

- [Dockerfile 参考](../Dockerfile)
- [Docker Compose 配置](../docker-compose.prod.yml)
- [部署手册](../ALIYUN_DEPLOYMENT.md)
- [Docker 官方文档](https://docs.docker.com/)
- [阿里云容器镜像服务](https://cr.console.aliyun.com/)
