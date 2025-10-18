import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PORT: int = int(os.getenv("PORT", 8000))
    CSDN_USERNAME: str = os.getenv("CSDN_USERNAME", "")
    CSDN_PASSWORD: str = os.getenv("CSDN_PASSWORD", "")

    # 验证码识别服务配置
    CAPTCHA_SERVICE: str = os.getenv("CAPTCHA_SERVICE", "mock")

    # 超级鹰配置
    CHAOJIYING_USERNAME: str = os.getenv("CHAOJIYING_USERNAME", "")
    CHAOJIYING_PASSWORD: str = os.getenv("CHAOJIYING_PASSWORD", "")
    CHAOJIYING_SOFT_ID: str = os.getenv("CHAOJIYING_SOFT_ID", "")

    # 2Captcha配置
    TWOCAPTCHA_API_KEY: str = os.getenv("TWOCAPTCHA_API_KEY", "")

    # Redis配置（用于Celery）
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB: int = int(os.getenv("REDIS_DB", 0))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")

    # 文件清理配置
    CLEANUP_RETENTION_DAYS: int = int(os.getenv("CLEANUP_RETENTION_DAYS", 7))  # 文件保留天数
    CLEANUP_ENABLED: bool = os.getenv("CLEANUP_ENABLED", "true").lower() == "true"  # 是否启用自动清理

settings = Settings()