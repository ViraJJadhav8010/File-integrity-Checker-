import tkinter as tk
from tkinter import messagebox, filedialog

import os
import threading
import time

from config.database import get_connection
from utils.hash_utils import compute_md5


class FileIntegrityChecker:

    def __init__(self):

        self.conn = get_connection()

        if self.conn is None:
            return

        self.cursor = self.conn.cursor(
            buffered=True
        )

        self.initialize_database()

        self.setup_ui()

    # ------------------------------------------------
    # Create file_hashes table
    # ------------------------------------------------

    def initialize_database(self):

        try:

            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS file_hashes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    file_name VARCHAR(255),
                    file_hash VARCHAR(32),
                    created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            self.conn.commit()

        except Exception as error:

            messagebox.showerror(
                "Database Error",
                f"Unable to initialize database.\n\n{error}"
            )

    # ------------------------------------------------
    # Main UI
    # ------------------------------------------------

    def setup_ui(self):

        self.root = tk.Tk()

        self.root.title(
            "File Integrity Checker"
        )

        self.root.geometry(
            "800x500"
        )

        self.root.configure(
            bg="#f0f0f0"
        )

        # Header
        header = tk.Frame(
            self.root,
            bg="#333",
            height=80
        )

        header.pack(
            fill=tk.X
        )

        tk.Label(
            header,
            text="File Integrity Checker",
            font=("Arial", 20, "bold"),
            bg="#333",
            fg="white"
        ).pack(
            pady=20,
            padx=20,
            anchor="w"
        )

        # Content
        content = tk.Frame(
            self.root,
            bg="#f0f0f0",
            padx=20,
            pady=20
        )

        content.pack(
            expand=True,
            fill=tk.BOTH
        )

        # ------------------------------------------------
        # File selection
        # ------------------------------------------------

        file_frame = tk.Frame(
            content,
            bg="#f0f0f0"
        )

        file_frame.pack(
            pady=10
        )

        tk.Label(
            file_frame,
            text="Select File:",
            font=("Arial", 12),
            bg="#f0f0f0"
        ).pack(
            side=tk.LEFT
        )

        self.file_entry = tk.Entry(
            file_frame,
            width=50,
            font=("Arial", 12)
        )

        self.file_entry.pack(
            side=tk.LEFT,
            padx=5
        )

        tk.Button(
            file_frame,
            text="Browse",
            command=self.browse_file
        ).pack(
            side=tk.LEFT
        )

        # ------------------------------------------------
        # Main buttons
        # ------------------------------------------------

        button_frame = tk.Frame(
            content,
            bg="#f0f0f0"
        )

        button_frame.pack(
            pady=20
        )

        tk.Button(
            button_frame,
            text="Store Hash",
            font=("Arial", 12),
            bg="#4CAF50",
            fg="white",
            command=self.store_file_hash
        ).pack(
            side=tk.LEFT,
            padx=10
        )

        tk.Button(
            button_frame,
            text="Check Integrity",
            font=("Arial", 12),
            bg="#2196F3",
            fg="white",
            command=self.check_file_integrity
        ).pack(
            side=tk.LEFT,
            padx=10
        )

        # ------------------------------------------------
        # Scheduler
        # ------------------------------------------------

        scheduler_frame = tk.LabelFrame(
            content,
            text="Schedule Integrity Checks",
            bg="#f0f0f0",
            font=("Arial", 12, "bold")
        )

        scheduler_frame.pack(
            fill=tk.X,
            pady=20
        )

        # Scheduled file
        sched_file_frame = tk.Frame(
            scheduler_frame,
            bg="#f0f0f0"
        )

        sched_file_frame.pack(
            pady=5
        )

        tk.Label(
            sched_file_frame,
            text="File:",
            font=("Arial", 11),
            bg="#f0f0f0"
        ).pack(
            side=tk.LEFT
        )

        self.sched_file_entry = tk.Entry(
            sched_file_frame,
            width=40,
            font=("Arial", 11)
        )

        self.sched_file_entry.pack(
            side=tk.LEFT,
            padx=5
        )

        tk.Button(
            sched_file_frame,
            text="Browse",
            command=self.browse_scheduled_file
        ).pack(
            side=tk.LEFT
        )

        # Interval
        interval_frame = tk.Frame(
            scheduler_frame,
            bg="#f0f0f0"
        )

        interval_frame.pack(
            pady=5
        )

        tk.Label(
            interval_frame,
            text="Interval (minutes):",
            font=("Arial", 11),
            bg="#f0f0f0"
        ).pack(
            side=tk.LEFT
        )

        self.interval_entry = tk.Entry(
            interval_frame,
            width=10,
            font=("Arial", 11)
        )

        self.interval_entry.pack(
            side=tk.LEFT,
            padx=5
        )

        # Start scheduler
        tk.Button(
            scheduler_frame,
            text="Start Scheduled Checks",
            font=("Arial", 12),
            bg="#FF9800",
            fg="white",
            command=self.schedule_integrity_check
        ).pack(
            pady=10
        )

        # About
        tk.Button(
            content,
            text="About / Ethical Hacking",
            font=("Arial", 11),
            bg="#607D8B",
            fg="white",
            command=self.show_about_info
        ).pack(
            pady=10
        )

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.on_close
        )

        self.root.mainloop()

    # ------------------------------------------------
    # Store Hash
    # ------------------------------------------------

    def store_file_hash(self):

        file_path = self.file_entry.get().strip()

        if not file_path:

            messagebox.showerror(
                "Error",
                "Please select a file."
            )

            return

        if not os.path.isfile(file_path):

            messagebox.showerror(
                "Error",
                "Selected file does not exist."
            )

            return

        file_hash = compute_md5(
            file_path
        )

        if file_hash is None:

            messagebox.showerror(
                "Error",
                "Unable to calculate file hash."
            )

            return

        file_name = os.path.basename(
            file_path
        )

        try:

            self.cursor.execute(
                """
                SELECT *
                FROM file_hashes
                WHERE file_name = %s
                """,
                (file_name,)
            )

            result = self.cursor.fetchone()

            if result:

                self.cursor.execute(
                    """
                    UPDATE file_hashes
                    SET file_hash = %s
                    WHERE file_name = %s
                    """,
                    (
                        file_hash,
                        file_name
                    )
                )

                messagebox.showinfo(
                    "Updated",
                    f"Hash updated for {file_name}"
                )

            else:

                self.cursor.execute(
                    """
                    INSERT INTO file_hashes
                    (file_name, file_hash)
                    VALUES (%s, %s)
                    """,
                    (
                        file_name,
                        file_hash
                    )
                )

                messagebox.showinfo(
                    "Stored",
                    f"Hash stored for {file_name}"
                )

            self.conn.commit()

        except Exception as error:

            messagebox.showerror(
                "Database Error",
                str(error)
            )

    # ------------------------------------------------
    # Check Integrity
    # ------------------------------------------------

    def check_file_integrity(self):

        file_path = self.file_entry.get().strip()

        if not file_path:

            messagebox.showerror(
                "Error",
                "Please select a file."
            )

            return

        if not os.path.isfile(file_path):

            messagebox.showerror(
                "Error",
                "File does not exist."
            )

            return

        current_hash = compute_md5(
            file_path
        )

        if current_hash is None:
            return

        file_name = os.path.basename(
            file_path
        )

        try:

            self.cursor.execute(
                """
                SELECT file_hash
                FROM file_hashes
                WHERE file_name = %s
                """,
                (file_name,)
            )

            stored_hash = self.cursor.fetchone()

            if stored_hash:

                if current_hash == stored_hash[0]:

                    messagebox.showinfo(
                        "Integrity OK",
                        "File integrity verified.\n\n"
                        "The file has NOT been modified."
                    )

                else:

                    messagebox.showwarning(
                        "Integrity Alert",
                        "File has been MODIFIED!"
                    )

            else:

                messagebox.showerror(
                    "Missing",
                    "File not found in database.\n"
                    "Please store the hash first."
                )

        except Exception as error:

            messagebox.showerror(
                "Database Error",
                str(error)
            )

    # ------------------------------------------------
    # Scheduled Integrity Check
    # ------------------------------------------------

    def schedule_integrity_check(self):

        file_path = self.sched_file_entry.get().strip()

        interval = self.interval_entry.get().strip()

        if not file_path:

            messagebox.showerror(
                "Input Error",
                "Please select a file."
            )

            return

        if not os.path.isfile(file_path):

            messagebox.showerror(
                "Input Error",
                "Selected file does not exist."
            )

            return

        if not interval.isdigit():

            messagebox.showerror(
                "Input Error",
                "Enter a valid interval."
            )

            return

        interval_minutes = int(interval)

        if interval_minutes <= 0:

            messagebox.showerror(
                "Input Error",
                "Interval must be greater than 0."
            )

            return

        interval_seconds = (
            interval_minutes * 60
        )

        file_name = os.path.basename(
            file_path
        )

        messagebox.showinfo(
            "Scheduled Check",
            f"Periodic checks started for:\n\n"
            f"{file_name}\n\n"
            f"Every {interval_minutes} minute(s)."
        )

        def periodic_check():

            while True:

                if not os.path.isfile(file_path):

                    self.root.after(
                        0,
                        lambda: messagebox.showerror(
                            "Error",
                            f"{file_name} no longer exists."
                        )
                    )

                    break

                current_hash = compute_md5(
                    file_path
                )

                if current_hash is None:
                    break

                try:

                    self.cursor.execute(
                        """
                        SELECT file_hash
                        FROM file_hashes
                        WHERE file_name = %s
                        """,
                        (file_name,)
                    )

                    stored_hash = (
                        self.cursor.fetchone()
                    )

                    if stored_hash:

                        if current_hash != stored_hash[0]:

                            self.root.after(
                                0,
                                lambda: messagebox.showwarning(
                                    "Integrity Alert",
                                    f"{file_name} "
                                    "has been MODIFIED!"
                                )
                            )

                        else:

                            self.root.after(
                                0,
                                lambda: messagebox.showinfo(
                                    "Integrity Check",
                                    f"{file_name} "
                                    "has NOT been modified."
                                )
                            )

                    else:

                        self.root.after(
                            0,
                            lambda: messagebox.showerror(
                                "Error",
                                f"No stored hash found "
                                f"for {file_name}."
                            )
                        )

                except Exception as error:

                    print(
                        f"Scheduled check error: {error}"
                    )

                    break

                time.sleep(
                    interval_seconds
                )

        thread = threading.Thread(
            target=periodic_check,
            daemon=True
        )

        thread.start()

    # ------------------------------------------------
    # Browse File
    # ------------------------------------------------

    def browse_file(self):

        path = filedialog.askopenfilename()

        if path:

            self.file_entry.delete(
                0,
                tk.END
            )

            self.file_entry.insert(
                0,
                path
            )

    # ------------------------------------------------
    # Browse Scheduled File
    # ------------------------------------------------

    def browse_scheduled_file(self):

        path = filedialog.askopenfilename()

        if path:

            self.sched_file_entry.delete(
                0,
                tk.END
            )

            self.sched_file_entry.insert(
                0,
                path
            )

    # ------------------------------------------------
    # About
    # ------------------------------------------------

    def show_about_info(self):

        messagebox.showinfo(
            "Ethical Hacking",
            "File Integrity Checker\n\n"
            "• Detects unauthorized file changes\n"
            "• Uses MD5 file hashing\n"
            "• Stores hashes in MySQL\n"
            "• Performs scheduled integrity checks\n"
            "• Useful for file monitoring\n\n"
            "Built by:\n"
            "Viraj Jadhav\n"
            "Pawar Neha\n"
            "Bhosale Shivneri"
        )

    # ------------------------------------------------
    # Close Application
    # ------------------------------------------------

    def on_close(self):

        try:

            if self.cursor:
                self.cursor.close()

            if self.conn:
                self.conn.close()

        except Exception:
            pass

        self.root.destroy()