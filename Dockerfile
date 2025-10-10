# Docker 部署配置

FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV TZ=Asia/Shanghai
ENV PYTHONPATH=/app
ENV HOME=/app

# 使用清华源加速 apt 和 pip                                                                                                                        
RUN set -eux; \
    codename="$(. /etc/os-release && echo "$VERSION_CODENAME")"; \
    rm -f /etc/apt/sources.list.d/debian.sources; \
    printf 'deb https://mirrors.tuna.tsinghua.edu.cn/debian %s main contrib non-free non-free-firmware\n' "$codename" > /etc/apt/sources.list; \
    printf 'deb https://mirrors.tuna.tsinghua.edu.cn/debian %s-updates main contrib non-free non-free-firmware\n' "$codename" >> /etc/apt/sources.list; \
    printf 'deb https://mirrors.tuna.tsinghua.edu.cn/debian-security %s-security main contrib non-free non-free-firmware\n' "$codename" >> /etc/apt/sources.list; \
    apt-get update


# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
  gcc \
  default-libmysqlclient-dev \
  pkg-config \
  curl \
  ca-certificates \
  fonts-liberation \
  fonts-noto-color-emoji \
  fonts-unifont \
  fonts-ubuntu \
  libasound2 \
  libatk-bridge2.0-0 \
  libatk1.0-0 \
  libatspi2.0-0 \
  libcairo2 \
  libcups2 \
  libdbus-1-3 \
  libdrm2 \
  libexpat1 \
  libfontconfig1 \
  libgbm1 \
  libglib2.0-0 \
  libgtk-3-0 \
  libnspr4 \
  libnss3 \
  libpango-1.0-0 \
  libpangocairo-1.0-0 \
  libstdc++6 \
  libx11-6 \
  libx11-xcb1 \
  libxcb1 \
  libxcb-dri3-0 \
  libxcomposite1 \
  libxcursor1 \
  libxdamage1 \
  libxext6 \
  libxfixes3 \
  libxi6 \
  libxrandr2 \
  libxshmfence1 \
  libxss1 \
  libxtst6 \
  xdg-utils \
  && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple \
 && pip install --no-cache-dir -r requirements.txt \
 && python -m playwright install chromium

# 复制应用代码
COPY app/ ./app/
COPY run.py .
COPY scripts/ ./scripts/
COPY scripts/manage_db.py ./manage_db.py
COPY celery_worker.py .

# 复制配置文件（如果存在）
COPY .env* ./

# 创建必要的目录
RUN mkdir -p downloads logs

# 设置文件权限
RUN chmod +x run.py manage_db.py celery_worker.py

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# 默认命令（可被 docker-compose 覆盖）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
