import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PORT: int = int(os.getenv("PORT", 8080))

    # 线程池配置
    THREAD_POOL_WORKERS: int = int(os.getenv("THREAD_POOL_WORKERS", 4))

settings = Settings()
