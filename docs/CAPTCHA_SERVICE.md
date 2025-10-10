# 验证码识别服务使用指南

本项目支持接入第三方验证码识别服务来自动处理CSDN登录时的图形验证码。

## 支持的验证码服务

### 1. 超级鹰（Chaojiying）- 推荐国内用户

**优点：**
- 国内服务，速度快
- 支持多种验证码类型
- 价格实惠

**注册地址：** http://www.chaojiying.com/

**配置步骤：**

1. 注册超级鹰账号并充值
2. 获取软件ID（在用户中心创建）
3. 在 `.env` 文件中配置：

```env
CAPTCHA_SERVICE=chaojiying
CHAOJIYING_USERNAME=你的用户名
CHAOJIYING_PASSWORD=你的密码
CHAOJIYING_SOFT_ID=你的软件ID
```

**收费标准：**
- 点选验证码：约 1-2 分/题
- 最低充值：1元起

### 2. 2Captcha - 国际服务

**优点：**
- 国际知名服务
- 支持多种验证码类型
- 服务稳定

**注册地址：** https://2captcha.com/

**配置步骤：**

1. 注册账号并充值
2. 获取API Key
3. 在 `.env` 文件中配置：

```env
CAPTCHA_SERVICE=2captcha
TWOCAPTCHA_API_KEY=你的API密钥
```

**收费标准：**
- 点选验证码：约 $1-2 /1000题

### 3. Mock模式 - 测试用

用于测试和开发，返回固定坐标，不会真正识别验证码。

```env
CAPTCHA_SERVICE=mock
```

## 使用方法

### 方式1：在代码中使用

```python
from app.services.auth_service import AuthService

# 启用验证码自动识别
auth_service = AuthService(use_captcha_service=True)

# 登录（验证码会自动识别）
success = auth_service.login("username", "password")
```

### 方式2：运行测试脚本

```bash
# 使用自动验证码识别
python tests/test_login_with_captcha.py

# 手动完成验证码
python tests/test_login_selenium.py
```

## 验证码识别流程

1. 检测到验证码弹窗
2. 截取验证码图片
3. 调用第三方服务识别坐标
4. 自动点击识别出的坐标
5. 提交验证结果

## 注意事项

1. **识别准确率**
   - 点选验证码识别率通常在 80-90%
   - 识别失败会自动切换到手动模式

2. **成本控制**
   - 建议使用cookie持久化，减少登录次数
   - 只在必要时才进行登录操作

3. **安全性**
   - 请妥善保管验证码服务的API密钥
   - 不要将密钥提交到公开仓库

4. **合法合规**
   - 仅用于个人学习和研究
   - 遵守网站使用条款
   - 不要用于商业爬虫

## 故障排查

### 问题1：验证码识别失败

**解决方案：**
- 检查验证码服务配置是否正确
- 确认账户余额充足
- 查看日志了解具体错误信息
- 尝试切换到手动模式

### 问题2：识别后点击位置不准确

**解决方案：**
- 检查浏览器缩放比例（应为100%）
- 验证坐标偏移量计算是否正确
- 调整点击延迟时间

### 问题3：验证码服务响应慢

**解决方案：**
- 检查网络连接
- 尝试更换验证码服务
- 增加超时时间

## 成本估算

以超级鹰为例：

- 登录一次需识别1个验证码
- 成本：约 0.01-0.02 元/次
- 充值10元可登录 500-1000 次

## 开发扩展

如需接入其他验证码服务，可参考 `app/services/captcha_service.py` 中的实现：

```python
class CustomCaptchaService(CaptchaService):
    """自定义验证码识别服务"""

    def recognize(self, image_path: str) -> Optional[List[Tuple[int, int]]]:
        # 实现你的识别逻辑
        pass
```

## 相关文件

- `app/services/captcha_service.py` - 验证码服务实现
- `app/services/auth_service.py` - 集成验证码识别的登录服务
- `tests/test_login_with_captcha.py` - 带验证码识别的测试脚本
- `.env` - 配置文件

## 参考资料

- [超级鹰API文档](http://www.chaojiying.com/api.html)
- [2Captcha API文档](https://2captcha.com/2captcha-api)
- [Selenium文档](https://selenium-python.readthedocs.io/)