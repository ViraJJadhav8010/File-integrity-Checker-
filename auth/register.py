import tkinter as tk
from tkinter import messagebox

from datetime import datetime

from config.database import get_connection


def registration_window(parent=None):

    if parent:
        parent.destroy()

    root = tk.Tk()
    root.title("Registration Page")
    root.geometry("600x500")
    root.resizable(False, False)

    # Background
    try:
        from PIL import Image, ImageTk

        bg_image = Image.open("assets/Cyber.jpg")
        bg_image = bg_image.resize(
            (600, 500),
            Image.Resampling.LANCZOS
        )

        bg_photo = ImageTk.PhotoImage(bg_image)

    except Exception:
        bg_photo = None

    canvas = tk.Canvas(
        root,
        width=600,
        height=500
    )

    canvas.pack()

    if bg_photo:
        canvas.create_image(
            0,
            0,
            anchor="nw",
            image=bg_photo
        )

    canvas.create_text(
        300,
        50,
        text="Register for File Integrity Checker",
        font=("Arial", 20, "bold"),
        fill="white"
    )

    # Registration frame
    frame = tk.Frame(
        root,
        bg="white",
        bd=2
    )

    frame.place(
        relx=0.5,
        rely=0.5,
        anchor="center"
    )

    # Full Name
    tk.Label(
        frame,
        text="Full Name",
        bg="white"
    ).grid(
        row=0,
        column=0,
        pady=10,
        padx=10
    )

    name_entry = tk.Entry(frame)

    name_entry.grid(
        row=0,
        column=1,
        pady=10,
        padx=10
    )

    # DOB
    tk.Label(
        frame,
        text="Date of Birth (YYYY-MM-DD)",
        bg="white"
    ).grid(
        row=1,
        column=0,
        pady=10,
        padx=10
    )

    dob_entry = tk.Entry(frame)

    dob_entry.grid(
        row=1,
        column=1,
        pady=10,
        padx=10
    )

    # Gender
    tk.Label(
        frame,
        text="Gender",
        bg="white"
    ).grid(
        row=2,
        column=0,
        pady=10,
        padx=10
    )

    gender_var = tk.StringVar()
    gender_var.set("Select Gender")

    gender_menu = tk.OptionMenu(
        frame,
        gender_var,
        "Male",
        "Female",
        "Other"
    )

    gender_menu.grid(
        row=2,
        column=1,
        pady=10,
        padx=10
    )

    # Age
    tk.Label(
        frame,
        text="Age (Optional)",
        bg="white"
    ).grid(
        row=3,
        column=0,
        pady=10,
        padx=10
    )

    age_entry = tk.Entry(frame)

    age_entry.grid(
        row=3,
        column=1,
        pady=10,
        padx=10
    )

    # Password
    tk.Label(
        frame,
        text="Password",
        bg="white"
    ).grid(
        row=4,
        column=0,
        pady=10,
        padx=10
    )

    password_entry = tk.Entry(
        frame,
        show="*"
    )

    password_entry.grid(
        row=4,
        column=1,
        pady=10,
        padx=10
    )

    def register():

        full_name = name_entry.get().strip()
        dob = dob_entry.get().strip()
        gender = gender_var.get()
        age = age_entry.get().strip()
        password = password_entry.get().strip()

        # Validation
        if (
            not full_name
            or not dob
            or gender == "Select Gender"
            or not password
        ):
            messagebox.showwarning(
                "Input Error",
                "Please fill in all required fields."
            )
            return

        # Validate DOB
        try:

            birth_date = datetime.strptime(
                dob,
                "%Y-%m-%d"
            )

            if not age:

                age = str(
                    (datetime.now() - birth_date).days // 365
                )

        except ValueError:

            messagebox.showwarning(
                "Date Error",
                "Invalid date format.\nUse YYYY-MM-DD."
            )

            return

        # Database
        conn = get_connection()

        if conn is None:
            return

        try:

            cursor = conn.cursor(buffered=True)
            query = """
            INSERT INTO register
            (full_name, dob, gender, age, password)
            VALUES (%s, %s, %s, %s, %s)
            """

            values = (
                full_name,
                dob,
                gender,
                age,
                password
            )

            cursor.execute(
                query,
                values
            )

            conn.commit()

            cursor.close()
            conn.close()

            messagebox.showinfo(
                "Registration Successful",
                "Registration completed successfully.\n"
                "You can now log in."
            )

            root.destroy()

            from auth.login import login_window
            login_window()

        except Exception as err:

            messagebox.showerror(
                "Database Error",
                f"Error: {err}"
            )

            conn.close()

    # Register button
    tk.Button(
        frame,
        text="Register",
        width=15,
        command=register
    ).grid(
        row=5,
        column=0,
        columnspan=2,
        pady=10
    )

    root.mainloop()