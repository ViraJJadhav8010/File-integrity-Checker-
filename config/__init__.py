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
    
    # MySQL Database Settings (supports both MYSQL_* and legacy DB_* environment variables)
    MYSQL_HOST = os.getenv("MYSQL_HOST") or os.getenv("DB_HOST", "localhost")
    MYSQL_USER = os.getenv("MYSQL_USER") or os.getenv("DB_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD") or os.getenv("DB_PASSWORD", "")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE") or os.getenv("DB_NAME", "file_integrity")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT") or os.getenv("DB_PORT", "3306"))
    
    # Dictionary format for mysql.connector.connect(**DB_CONFIG)
    DB_CONFIG = {
        "host": MYSQL_HOST,
        "user": MYSQL_USER,
        "password": MYSQL_PASSWORD,
        "database": MYSQL_DATABASE,
        "port": MYSQL_PORT
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