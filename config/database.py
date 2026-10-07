import mysql.connector
from config import Config

# Preserve DB_CONFIG reference using centralized Config
DB_CONFIG = Config.DB_CONFIG

def get_connection():
    """
    Returns a MySQL database connection using central Config settings.
    Logs errors cleanly and prevents Tkinter crashes in headless/web environments.
    """
    try:
        connection = mysql.connector.connect(**Config.DB_CONFIG)
        return connection
    except mysql.connector.Error as err:
        print(f"[Database Connection Error] Unable to connect to MySQL: {err}")
        # Optional Tkinter dialog for desktop compatibility if running in a desktop GUI context
        try:
            import tkinter as tk
            from tkinter import messagebox
            # Only display messagebox if a Tk root exists to avoid crashing headless servers
            if tk._default_root is not None:
                messagebox.showerror(
                    "Database Connection Error",
                    f"Unable to connect to MySQL.\n\nError: {err}"
                )
        except Exception:
            pass
        return None