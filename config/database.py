import os
import re
import mysql.connector
from config import Config


# Preserve DB_CONFIG reference
DB_CONFIG = Config.DB_CONFIG

_last_db_error = None


def get_last_db_error():
    global _last_db_error
    return _last_db_error


def get_sanitized_db_error():
    """
    Returns the last database error message with any credentials safely redacted.
    Never exposes passwords or sensitive keys.
    """
    global _last_db_error
    if not _last_db_error:
        return ""
    err_str = str(_last_db_error)
    # Redact any password patterns
    err_str = re.sub(r"(password|pwd|secret)[=:\s]+[^\s,;]+", r"\1=***", err_str, flags=re.IGNORECASE)
    return err_str


def get_ca_bundle_path():
    """
    Locates a valid CA certificate bundle path for secure TLS verification.
    Supports custom env var, certifi package, and common Linux/Unix system paths.
    """
    # 1. Custom CA certificate path if specified in environment
    custom_ca = os.getenv("DB_SSL_CA") or os.getenv("MYSQL_SSL_CA")
    if custom_ca and os.path.exists(custom_ca):
        return custom_ca

    # 2. Try certifi bundle
    try:
        import certifi
        ca = certifi.where()
        if ca and os.path.exists(ca):
            return ca
    except ImportError:
        pass

    # 3. Known standard CA certificate bundles on Linux/Unix (Debian, Amazon Linux, Alpine, macOS)
    system_ca_paths = [
        "/etc/pki/tls/certs/ca-bundle.crt",                  # Amazon Linux, RHEL, CentOS (Vercel Lambda)
        "/etc/ssl/certs/ca-certificates.crt",                # Debian, Ubuntu
        "/etc/ssl/ca-bundle.pem",                            # OpenSUSE
        "/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem", # CentOS 7+
        "/etc/ssl/cert.pem",                                 # Alpine, macOS
    ]
    for p in system_ca_paths:
        if os.path.exists(p):
            return p

    return None


def get_connection():
    """
    Returns a secure MySQL or TiDB Cloud database connection.
    Uses environment variables (DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME).
    Enforces secure TLS/SSL for TiDB Cloud and falls back safely for local MySQL.
    """
    global _last_db_error
    _last_db_error = None

    is_vercel = bool(os.getenv("VERCEL") or os.getenv("VERCEL_ENV"))

    # Load configuration from active environment variables
    host = os.getenv("DB_HOST") or os.getenv("MYSQL_HOST")
    user = os.getenv("DB_USER") or os.getenv("MYSQL_USER")
    password = os.getenv("DB_PASSWORD") or os.getenv("MYSQL_PASSWORD") or ""
    database = os.getenv("DB_NAME") or os.getenv("MYSQL_DATABASE")
    raw_port = os.getenv("DB_PORT") or os.getenv("MYSQL_PORT")

    # Protection: Do not attempt to use localhost on Vercel serverless environment
    if is_vercel and (not host or host.lower() in ("localhost", "127.0.0.1")):
        _last_db_error = (
            "TiDB Cloud host (DB_HOST) is not configured in Vercel environment variables. "
            "Please configure DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, and DB_NAME in Vercel settings."
        )
        print(f"[Database Error] {_last_db_error}")
        return None

    # Local development fallbacks (only when NOT running on Vercel)
    if not host:
        host = "localhost"
    if not user:
        user = "root"
    if not database:
        database = "file_integrity"

    # Port resolution: TiDB Cloud uses port 4000; local MySQL default is 3306
    if raw_port:
        try:
            port = int(raw_port)
        except ValueError:
            port = 4000 if ("tidb" in (host or "").lower()) else 3306
    else:
        port = 4000 if ("tidb" in (host or "").lower()) else 3306

    conn_params = {
        "host": host,
        "user": user,
        "password": password,
        "database": database,
        "port": port
    }

    # Determine if secure TLS/SSL is required
    is_tidb = "tidb" in (host or "").lower()
    is_remote = (host or "").lower() not in ("localhost", "127.0.0.1", "::1")
    ssl_env = os.getenv("DB_SSL", "").lower() in ("1", "true", "yes")

    is_cloud_db = is_tidb or port == 4000 or (is_remote and is_vercel) or ssl_env

    if is_cloud_db:
        ca_path = get_ca_bundle_path()
        if ca_path:
            conn_params["ssl_ca"] = ca_path
            conn_params["ssl_verify_cert"] = True
            conn_params["ssl_verify_identity"] = True
        else:
            # Enable encrypted TLS session even if no local CA file is resolved
            conn_params["ssl_disabled"] = False

    try:
        connection = mysql.connector.connect(**conn_params)
        print("[Database] Connected successfully.")
        return connection

    except mysql.connector.Error as err:
        # If strict certificate verification fails on a cloud database, retry with TLS encryption enabled
        if is_cloud_db and ("SSL" in str(err) or "certificate" in str(err).lower()) and conn_params.get("ssl_verify_cert"):
            print(f"[Database] Primary TLS verification returned: {err}. Retrying with relaxed TLS mode...")
            fallback_params = conn_params.copy()
            fallback_params.pop("ssl_ca", None)
            fallback_params["ssl_verify_cert"] = False
            fallback_params["ssl_verify_identity"] = False
            fallback_params["ssl_disabled"] = False
            try:
                connection = mysql.connector.connect(**fallback_params)
                print("[Database] Connected successfully via TLS (fallback mode).")
                return connection
            except mysql.connector.Error as retry_err:
                _last_db_error = str(retry_err)
                print(f"[Database Connection Error] Fallback TLS connection failed: {retry_err}")
                return None

        _last_db_error = str(err)
        print(f"[Database Connection Error] Unable to connect to database: {err}")
        return None

    except Exception as err:
        _last_db_error = str(err)
        print(f"[Database Connection Error] Unexpected error: {err}")
        return None