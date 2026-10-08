import os

# Safely load environment variables from .env if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

class Config:
    """
    Central Flask and Database configuration.
    Safely loads all settings from environment variables without hardcoded secrets.
    """
    SECRET_KEY = os.getenv("SECRET_KEY", "forensics-integrity-secret-key-change-in-production")
    
    IS_VERCEL = bool(os.getenv("VERCEL") or os.getenv("VERCEL_ENV"))

    # Database Settings: Support both DB_* (TiDB/Vercel standard) and legacy MYSQL_* variables
    DB_HOST = os.getenv("DB_HOST") or os.getenv("MYSQL_HOST")
    DB_USER = os.getenv("DB_USER") or os.getenv("MYSQL_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD") or os.getenv("MYSQL_PASSWORD") or ""
    DB_NAME = os.getenv("DB_NAME") or os.getenv("MYSQL_DATABASE")

    # Local fallback only if NOT running in Vercel serverless environment
    if not DB_HOST:
        DB_HOST = "localhost" if not IS_VERCEL else ""
    if not DB_USER:
        DB_USER = "root" if not IS_VERCEL else ""
    if not DB_NAME:
        DB_NAME = "file_integrity"

    # Port resolution: TiDB Cloud default is 4000; local MySQL default is 3306
    _raw_port = os.getenv("DB_PORT") or os.getenv("MYSQL_PORT")
    if _raw_port:
        try:
            DB_PORT = int(_raw_port)
        except ValueError:
            DB_PORT = 4000 if ("tidb" in (DB_HOST or "").lower()) else 3306
    else:
        DB_PORT = 4000 if ("tidb" in (DB_HOST or "").lower()) else 3306

    # Legacy alias properties for backwards compatibility
    MYSQL_HOST = DB_HOST
    MYSQL_USER = DB_USER
    MYSQL_PASSWORD = DB_PASSWORD
    MYSQL_DATABASE = DB_NAME
    MYSQL_PORT = DB_PORT

    # Dictionary format for mysql.connector.connect(**DB_CONFIG)
    DB_CONFIG = {
        "host": DB_HOST,
        "user": DB_USER,
        "password": DB_PASSWORD,
        "database": DB_NAME,
        "port": DB_PORT
    }

    # Uploads Configuration
    # Uses environment variable if set, otherwise defaults to local uploads directory
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", os.path.join(BASE_DIR, "uploads"))
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 64 * 1024 * 1024)) # 64MB default

# Ensure upload directory exists if filesystem allows
try:
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
except Exception:
    pass

__all__ = ["Config"]