# 🎯 项目规范

unlock-vip项目的代码和文档组织规范。

## 📁 目录结构规范

### 根目录

根目录只保留核心配置文件和启动脚本，不应有散落的文档或工具脚本。

**允许的文件类型**:
- ✅ 配置文件: `.env`, `.gitignore`, `requirements.txt`
- ✅ Docker文件: `Dockerfile`, `docker-compose.yml`
- ✅ 启动脚本: `run.py`, `celery_worker.py`
- ✅ 数据库初始化: `init-db.sql`
- ✅ 主文档: `README.md`
- ✅ 部署脚本: `deploy.sh`, `deploy-aliyun.sh`, `setup-ssl.sh`
- ✅ Cookies配置: `cookies.json`

**不允许的文件**:
- ❌ 散落的Markdown文档（应放入`docs/`）
- ❌ 工具脚本（应放入`scripts/`）
- ❌ 测试文件（应放入`tests/`）
- ❌ 临时HTML文件
- ❌ 临时测试脚本

### `app/` - 应用代码

```
app/
├── api/              # API路由（按功能模块划分）
├── core/             # 核心配置
├── db/               # 数据库模型和连接
├── middleware/       # 中间件
├── models/           # Pydantic数据模型
├── services/         # 业务逻辑服务
├── tasks/            # Celery异步任务
└── main.py           # FastAPI应用入口
```

**规范**:
- 一个文件只包含一类功能
- 服务层（services）不依赖API层
- 数据模型分离（db.models vs models.schemas）

### `docs/` - 项目文档

```
docs/
├── README.md                        # 📚 文档索引（必需）
├── QUICK_START.md                   # 快速入门
├── API_*.md                         # API相关文档
├── DOCKER_*.md                      # Docker相关文档
├── DEPLOYMENT_*.md                  # 部署相关文档
└── [功能名]_[类型].md                # 其他功能文档
```

**命名规范**:
- 全大写：`README.md`, `QUICK_START.md`
- 主题_类型：`API_AUTHENTICATION.md`, `DOCKER_DEPLOYMENT.md`
- 使用下划线分隔：`FILE_CLEANUP_IMPLEMENTATION.md`

**文档分类**:
1. **快速开始**: QUICK_START, DOCKER_QUICKSTART
2. **API文档**: API_AUTHENTICATION, API_QUICK_REFERENCE
3. **部署文档**: DEPLOYMENT, DOCKER_DEPLOYMENT, ALIYUN_DEPLOYMENT
4. **功能文档**: FILE_CLEANUP, CELERY_BEAT_GUIDE
5. **总结文档**: COMPLETION_SUMMARY, INTEGRATION_SUMMARY

### `scripts/` - 工具脚本

```
scripts/
├── README.md                # 🛠️ 脚本说明（必需）
├── generate_*.py            # 生成类工具
├── list_*.py                # 查询类工具
├── manage_*.py              # 管理类工具
└── *.sh                     # Shell脚本
```

**命名规范**:
- 动词开头：`generate_`, `list_`, `manage_`, `create_`
- 描述功能：`generate_admin_key.py`, `list_api_keys.py`
- Shell脚本：`manage.sh`, `deploy.sh`

**脚本要求**:
- 必须包含docstring说明
- 必须处理异常
- 必须输出清晰的日志
- 建议使用argparse处理参数

### `tests/` - 测试代码

```
tests/
├── __init__.py
├── test_[模块名].py         # 单元测试
└── test_[功能]_[场景].py    # 集成测试
```

**命名规范**:
- 以`test_`开头
- 描述测试对象：`test_admin_auth.py`, `test_wenku_download.py`
- 描述场景：`test_complete_flow.py`, `test_cleanup_direct.py`

**测试要求**:
- 可独立运行
- 包含清晰的断言
- 输出详细的测试结果
- 临时测试完成后及时清理

### `downloads/` - 下载文件

```
downloads/
└── .gitkeep              # 保持目录结构
```

**规范**:
- 只存放下载的文章文件
- 不提交到Git（.gitignore已配置）
- 定期清理（Celery定时任务）

## 📝 文档编写规范

### Markdown格式

1. **标题层级**
   ```markdown
   # 一级标题（文档标题，每个文件只有一个）
   ## 二级标题（主要章节）
   ### 三级标题（子章节）
   #### 四级标题（细节说明）
   ```

2. **代码块**
   ```markdown
   &#96;&#96;&#96;python
   # Python代码
   def example():
       pass
   &#96;&#96;&#96;
   
   &#96;&#96;&#96;bash
   # Shell命令
   python run.py
   &#96;&#96;&#96;
   ```

3. **链接**
   - 文档内链接：`[快速开始](QUICK_START.md)`
   - 相对路径：`[脚本说明](../scripts/README.md)`
   - 外部链接：`[FastAPI](https://fastapi.tiangolo.com/)`

4. **列表**
   ```markdown
   - ✅ 已完成项
   - ⚠️ 警告项
   - ❌ 错误项
   - 📝 说明项
   ```

### 文档必需章节

每个功能文档应包含：

1. **标题和简介** - 说明文档目的
2. **前置条件** - 需要的环境和依赖
3. **配置说明** - 配置项和示例
4. **使用方法** - 详细的使用步骤
5. **示例** - 实际操作示例
6. **注意事项** - 常见问题和警告
7. **相关链接** - 关联文档链接

## 💻 代码规范

### Python代码

1. **导入顺序**
   ```python
   # 标准库
   import os
   import sys
   
   # 第三方库
   import requests
   from fastapi import FastAPI
   
   # 本地模块
   from app.core import config
   from app.services import article_service
   ```

2. **函数文档**
   ```python
   def download_article(url: str) -> Dict:
       """
       下载CSDN文章
       
       Args:
           url: 文章URL
           
       Returns:
           包含文章内容的字典
           
       Raises:
           ValueError: URL格式错误
           RequestException: 网络请求失败
       """
       pass
   ```

3. **类型注解**
   ```python
   from typing import Dict, List, Optional
   
   def process(data: Dict[str, str]) -> Optional[List[str]]:
       pass
   ```

### 服务层规范

```python
class ArticleService:
    """文章下载服务"""
    
    def __init__(self):
        """初始化服务"""
        pass
    
    def download(self, url: str) -> Dict:
        """
        下载文章
        
        业务逻辑应该在这里实现，不依赖API层
        """
        pass
```

## 🗂️ 文件命名规范

### Python文件
- 小写+下划线：`article_service.py`
- 描述功能：`wenku_service.py`, `auth_service.py`
- 任务文件：`article_tasks.py`, `cleanup_tasks.py`

### 配置文件
- `.env` - 环境变量
- `.env.example` - 环境变量示例
- `.env.docker` - Docker环境变量
- `.gitignore` - Git忽略规则

### Docker文件
- `Dockerfile` - Docker镜像构建
- `docker-compose.yml` - 开发环境
- `docker-compose.prod.yml` - 生产环境

## 🔄 开发流程规范

### 添加新功能

1. **代码实现**
   ```
   app/services/new_service.py     # 业务逻辑
   app/api/new_api.py              # API接口
   app/tasks/new_tasks.py          # 异步任务（如需要）
   ```

2. **编写测试**
   ```
   tests/test_new_service.py       # 单元测试
   tests/test_new_flow.py          # 集成测试
   ```

3. **编写文档**
   ```
   docs/NEW_FEATURE.md             # 功能文档
   ```

4. **更新主文档**
   - 更新 `README.md` 添加功能说明
   - 更新 `docs/README.md` 添加文档链接
   - 更新 `requirements.txt` 添加新依赖

### 提交代码

```bash
# 1. 运行测试
python -m pytest tests/

# 2. 检查代码格式
flake8 app/ scripts/ tests/

# 3. 提交代码
git add .
git commit -m "feat: 添加新功能"
git push origin main
```

### 代码审查清单

- [ ] 代码符合项目结构规范
- [ ] 包含完整的类型注解
- [ ] 包含详细的文档字符串
- [ ] 有对应的单元测试
- [ ] 更新了相关文档
- [ ] 没有临时文件提交
- [ ] 环境变量已添加到.env.example

## 📊 Git提交规范

### 提交消息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 类型（type）

- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建/工具相关

### 示例

```
feat(wenku): 添加文库文章Markdown渲染功能

- 集成python-markdown库
- 添加代码语法高亮
- 优化HTML输出格式

Closes #123
```

## 🧹 代码清理规范

### 定期清理

**每周清理**:
- [ ] 检查根目录是否有新的临时文件
- [ ] 检查tests/目录是否有临时测试脚本
- [ ] 检查downloads/目录大小

**每月清理**:
- [ ] 审查未使用的依赖
- [ ] 审查过时的文档
- [ ] 优化数据库查询
- [ ] 更新依赖版本

### 清理命令

```bash
# 删除Python缓存
find . -type d -name "__pycache__" -exec rm -r {} +
find . -type f -name "*.pyc" -delete

# 删除临时HTML文件
find . -name "*.html" -not -path "./downloads/*" -not -path "./nginx/*" -delete

# 清理downloads目录
python scripts/cleanup_old_files.py
```

## 📌 最佳实践

### DO ✅

- ✅ 文档和代码一起维护
- ✅ 使用类型注解
- ✅ 编写单元测试
- ✅ 遵循命名规范
- ✅ 及时清理临时文件
- ✅ 环境变量用.env管理
- ✅ 敏感信息不提交到Git

### DON'T ❌

- ❌ 不要在根目录堆积文件
- ❌ 不要提交临时测试文件
- ❌ 不要硬编码配置
- ❌ 不要省略文档字符串
- ❌ 不要忽略类型检查
- ❌ 不要提交.env文件
- ❌ 不要保留注释掉的代码

## 🔗 相关文档

- [项目README](../README.md)
- [文档中心](../docs/README.md)
- [脚本说明](../scripts/README.md)
- [快速入门](../docs/QUICK_START.md)

---

**最后更新**: 2025-10-03  
**维护者**: 项目团队
