import os
from urllib.parse import quote_plus
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

    # MySQL数据库配置
    DATABASE_HOST: str = os.getenv("DATABASE_HOST", "localhost")
    DATABASE_PORT: int = int(os.getenv("DATABASE_PORT", 3306))
    DATABASE_USER: str = os.getenv("DATABASE_USER", "root")
    DATABASE_PASSWORD: str = os.getenv("DATABASE_PASSWORD", "")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "unlock_vip")
    
    # 管理员主密钥（用于管理API接口认证）
    ADMIN_MASTER_KEY: str = os.getenv("ADMIN_MASTER_KEY", "")
    
    # 文件清理配置
    CLEANUP_RETENTION_DAYS: int = int(os.getenv("CLEANUP_RETENTION_DAYS", 7))  # 文件保留天数
    CLEANUP_ENABLED: bool = os.getenv("CLEANUP_ENABLED", "true").lower() == "true"  # 是否启用自动清理
    
    @property
    def DATABASE_URL(self) -> str:
        """生成数据库连接URL,自动编码密码中的特殊字符"""
        # URL编码用户名和密码,防止特殊字符导致解析错误
        encoded_user = quote_plus(self.DATABASE_USER)
        encoded_password = quote_plus(self.DATABASE_PASSWORD)
        return f"mysql+pymysql://{encoded_user}:{encoded_password}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}?charset=utf8mb4"

settings = Settings()