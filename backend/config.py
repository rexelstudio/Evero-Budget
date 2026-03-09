import os

SECRET_KEY = os.getenv("SECRET_KEY", "evero-budget-super-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////tmp/evero.db" if os.getenv("VERCEL") else "sqlite:///./evero.db")
