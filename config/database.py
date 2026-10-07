import mysql.connector
from tkinter import messagebox


DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "8010",
    "database": "file_integrity"
}


def get_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection

    except mysql.connector.Error as err:
        messagebox.showerror(
            "Database Connection Error",
            f"Unable to connect to MySQL.\n\nError: {err}"
        )
        return None