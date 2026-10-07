import os
import sys

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import Config
from config.database import get_connection

def init_db():
    """Initializes and migrates MySQL database tables for the web application."""
    conn = get_connection()
    if conn is None:
        print("[Database] Warning: Could not connect to MySQL during init_db()")
        return False

    cursor = conn.cursor(buffered=True)
    try:
        # 1. Initialize register table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS register (
                id INT AUTO_INCREMENT PRIMARY KEY,
                full_name VARCHAR(100) NOT NULL,
                username VARCHAR(100),
                email VARCHAR(150),
                dob DATE NULL,
                gender VARCHAR(20) NULL,
                age INT NULL,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Check existing columns in register table
        cursor.execute("DESCRIBE register")
        existing_reg_cols = [row[0] for row in cursor.fetchall()]

        if "username" not in existing_reg_cols:
            cursor.execute("ALTER TABLE register ADD COLUMN username VARCHAR(100)")
            print("[Database Migration] Added 'username' column to register table.")

        if "email" not in existing_reg_cols:
            cursor.execute("ALTER TABLE register ADD COLUMN email VARCHAR(150)")
            print("[Database Migration] Added 'email' column to register table.")

        cursor.execute("ALTER TABLE register MODIFY COLUMN password VARCHAR(255) NOT NULL")
        try:
            cursor.execute("ALTER TABLE register MODIFY COLUMN dob DATE NULL DEFAULT NULL")
            cursor.execute("ALTER TABLE register MODIFY COLUMN gender VARCHAR(20) NULL DEFAULT NULL")
            cursor.execute("ALTER TABLE register MODIFY COLUMN age INT NULL DEFAULT NULL")
        except Exception as alter_err:
            print("[Database Migration Note]", alter_err)

        # Backfill username and email for any existing rows that lack them
        cursor.execute("""
            UPDATE register 
            SET username = full_name 
            WHERE username IS NULL OR username = ''
        """)
        cursor.execute("""
            UPDATE register 
            SET email = CONCAT(REPLACE(LOWER(full_name), ' ', '_'), id, '@forensics.local') 
            WHERE email IS NULL OR email = ''
        """)

        # 2. Initialize file_hashes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS file_hashes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                file_name VARCHAR(255) NOT NULL,
                file_hash VARCHAR(32) NOT NULL,
                file_size VARCHAR(50) DEFAULT NULL,
                file_type VARCHAR(50) DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("DESCRIBE file_hashes")
        existing_fh_cols = [row[0] for row in cursor.fetchall()]

        if "file_size" not in existing_fh_cols:
            cursor.execute("ALTER TABLE file_hashes ADD COLUMN file_size VARCHAR(50) DEFAULT NULL")
            print("[Database Migration] Added 'file_size' column to file_hashes.")

        if "file_type" not in existing_fh_cols:
            cursor.execute("ALTER TABLE file_hashes ADD COLUMN file_type VARCHAR(50) DEFAULT NULL")
            print("[Database Migration] Added 'file_type' column to file_hashes.")

        # 3. Initialize audit_logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                file_name VARCHAR(255) NOT NULL,
                baseline_hash VARCHAR(32) DEFAULT NULL,
                current_hash VARCHAR(32) NOT NULL,
                status VARCHAR(50) NOT NULL,
                checked_by VARCHAR(100) DEFAULT 'Analyst',
                checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        print("[Database] Schema initialization and migration completed successfully.")
        return True

    except Exception as err:
        print(f"[Database Error] Migration error: {err}")
        return False
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    init_db()
