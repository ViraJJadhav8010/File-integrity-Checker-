import mysql.connector
from config import Config


# Preserve DB_CONFIG reference
DB_CONFIG = Config.DB_CONFIG


def get_connection():
    """
    Returns a secure MySQL/TiDB Cloud database connection.
    Uses environment variables from Vercel or local .env.
    """
    try:
        db_config = Config.DB_CONFIG.copy()

        # TiDB Cloud uses port 4000 and requires SSL/TLS
        if db_config.get("port") == 4000:
            db_config.update({
                "ssl_verify_cert": True,
                "ssl_verify_identity": True
            })

        connection = mysql.connector.connect(**db_config)

        print("[Database] Connected successfully.")
        return connection

    except mysql.connector.Error as err:
        print(f"[Database Connection Error] Unable to connect to database: {err}")
        return None