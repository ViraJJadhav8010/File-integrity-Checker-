import tkinter as tk
from tkinter import messagebox

from config.database import get_connection


def login_window():

    login_root = tk.Tk()

    login_root.title("Login Page")
    login_root.geometry("500x400")
    login_root.resizable(False, False)

    # ---------------- Background Image ----------------

    try:
        from PIL import Image, ImageTk

        bg_image = Image.open("assets/Cyber.jpg")

        bg_image = bg_image.resize(
            (500, 400),
            Image.Resampling.LANCZOS
        )

        bg_photo = ImageTk.PhotoImage(bg_image)

    except Exception:
        bg_photo = None

    canvas = tk.Canvas(
        login_root,
        width=500,
        height=400
    )

    canvas.pack()

    if bg_photo:
        canvas.create_image(
            0,
            0,
            anchor="nw",
            image=bg_photo
        )

    # ---------------- Title ----------------

    canvas.create_text(
        250,
        50,
        text="Welcome to File Integrity Checker",
        font=("Arial", 20, "bold"),
        fill="white"
    )

    # ---------------- Login Frame ----------------

    login_frame = tk.Frame(
        login_root,
        bg="white",
        bd=2
    )

    login_frame.place(
        relx=0.5,
        rely=0.5,
        anchor="center"
    )

    # Username

    tk.Label(
        login_frame,
        text="Username (Full Name)",
        bg="white"
    ).grid(
        row=0,
        column=0,
        pady=10,
        padx=10
    )

    username_entry = tk.Entry(
        login_frame
    )

    username_entry.grid(
        row=0,
        column=1,
        pady=10,
        padx=10
    )

    # Password

    tk.Label(
        login_frame,
        text="Password",
        bg="white"
    ).grid(
        row=1,
        column=0,
        pady=10,
        padx=10
    )

    password_entry = tk.Entry(
        login_frame,
        show="*"
    )

    password_entry.grid(
        row=1,
        column=1,
        pady=10,
        padx=10
    )

    # ---------------- Login Function ----------------

    def perform_login():

        username = username_entry.get().strip()
        password = password_entry.get().strip()

        if not username or not password:

            messagebox.showwarning(
                "Input Error",
                "Please enter both username and password."
            )

            return

        conn = get_connection()

        if conn is None:
            return

        cursor = None

        try:

            # IMPORTANT:
            # buffered=True fixes "Unread result found"
            cursor = conn.cursor(buffered=True)

            query = """
                SELECT id, full_name
                FROM register
                WHERE full_name = %s
                AND password = %s
                LIMIT 1
            """

            cursor.execute(
                query,
                (username, password)
            )

            result = cursor.fetchone()

            if result:

                messagebox.showinfo(
                    "Login Successful",
                    f"Welcome, {username}!"
                )

                # Close database resources before opening
                # the next window
                cursor.close()
                conn.close()

                login_root.destroy()

                from checker.integrity_checker import FileIntegrityChecker

                FileIntegrityChecker()

            else:

                messagebox.showerror(
                    "Login Failed",
                    "Invalid username or password."
                )

                cursor.close()
                conn.close()

        except Exception as error:

            messagebox.showerror(
                "Database Error",
                f"Error: {error}"
            )

            try:
                if cursor:
                    cursor.close()
            except:
                pass

            try:
                conn.close()
            except:
                pass

    # ---------------- Register Function ----------------

    def open_register():

        login_root.destroy()

        from auth.register import registration_window

        registration_window()

    # ---------------- Buttons ----------------

    tk.Button(
        login_frame,
        text="Login",
        width=15,
        command=perform_login
    ).grid(
        row=2,
        column=0,
        pady=10,
        padx=5
    )

    tk.Button(
        login_frame,
        text="Register",
        width=15,
        command=open_register
    ).grid(
        row=2,
        column=1,
        pady=10,
        padx=5
    )

    login_root.mainloop()