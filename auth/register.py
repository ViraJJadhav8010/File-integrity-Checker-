import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime
import os
from PIL import Image, ImageTk

from config.database import get_connection
from utils.ui_theme import (
    BG_DARK, BG_CARD, BG_INPUT, BORDER_SUBTLE, BORDER_ACTIVE,
    TEXT_WHITE, TEXT_LIGHT, TEXT_MUTED, CYAN_ACCENT,
    BLUE_PRIMARY, BLUE_HOVER, GREEN_SAFE, RED_ALERT,
    FONT_TITLE_LARGE, FONT_SUBTITLE, FONT_BODY_BOLD, FONT_BODY, FONT_SMALL,
    CyberButton, center_window
)


def registration_window(parent=None):
    if parent:
        parent.destroy()

    root = tk.Tk()
    root.title("File Integrity Checker - Operator Registration")
    root.geometry("860x640")
    root.resizable(False, False)
    root.configure(bg=BG_DARK)
    center_window(root, 860, 640)

    # ---------------- Background Canvas ----------------
    canvas = tk.Canvas(root, width=860, height=640, bg=BG_DARK, highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)

    bg_photo = None
    if os.path.exists("assets/Cyber.jpg"):
        try:
            bg_image = Image.open("assets/Cyber.jpg")
            bg_image = bg_image.resize((860, 640), Image.Resampling.LANCZOS)
            bg_photo = ImageTk.PhotoImage(bg_image)
            canvas.create_image(0, 0, anchor="nw", image=bg_photo)
        except Exception:
            bg_photo = None

    canvas.create_rectangle(0, 0, 860, 640, fill="#050a14", stipple="gray50")

    # ---------------- Center Card ----------------
    card_border = tk.Frame(canvas, bg=CYAN_ACCENT, padx=1, pady=1)
    canvas.create_window(430, 320, window=card_border, anchor="center")

    card = tk.Frame(card_border, bg=BG_CARD, padx=35, pady=24)
    card.pack()

    # Icon / Logo
    logo_photo = None
    if os.path.exists("assets/shield_icon.png"):
        try:
            logo_img = Image.open("assets/shield_icon.png")
            logo_img = logo_img.resize((46, 46), Image.Resampling.LANCZOS)
            logo_photo = ImageTk.PhotoImage(logo_img)
            logo_label = tk.Label(card, image=logo_photo, bg=BG_CARD)
            logo_label.image = logo_photo
            logo_label.pack(pady=(0, 4))
        except Exception:
            logo_photo = None

    if not logo_photo:
        icon_fallback = tk.Label(card, text="🛡️", font=("Segoe UI", 24), bg=BG_CARD, fg=CYAN_ACCENT)
        icon_fallback.pack(pady=(0, 4))

    tk.Label(
        card,
        text="OPERATOR REGISTRATION",
        font=FONT_TITLE_LARGE,
        bg=BG_CARD,
        fg=TEXT_WHITE
    ).pack()

    tk.Label(
        card,
        text="Digital Forensics & File Security Access",
        font=FONT_SUBTITLE,
        bg=BG_CARD,
        fg=CYAN_ACCENT
    ).pack(pady=(2, 10))

    # Inline Status / Error Message
    status_label = tk.Label(
        card,
        text="",
        font=FONT_SMALL,
        bg=BG_CARD,
        fg=RED_ALERT,
        wraplength=420
    )
    status_label.pack(pady=(0, 8))

    # Form Grid
    form_frame = tk.Frame(card, bg=BG_CARD)
    form_frame.pack(fill=tk.X)

    def create_field_entry(parent, row, label_text, is_pass=False, placeholder=""):
        tk.Label(
            parent,
            text=label_text,
            font=FONT_BODY_BOLD,
            bg=BG_CARD,
            fg=TEXT_LIGHT
        ).grid(row=row, column=0, sticky="w", pady=(4, 2))

        bdr = tk.Frame(parent, bg=BORDER_SUBTLE, padx=1, pady=1)
        bdr.grid(row=row+1, column=0, sticky="ew", pady=(0, 8))

        inner = tk.Frame(bdr, bg=BG_INPUT)
        inner.pack(fill=tk.X)

        entry = tk.Entry(
            inner,
            show="*" if is_pass else "",
            bg=BG_INPUT,
            fg=TEXT_WHITE,
            insertbackground=CYAN_ACCENT,
            font=FONT_BODY,
            relief=tk.FLAT,
            bd=5
        )
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        entry.bind("<FocusIn>", lambda e: bdr.configure(bg=CYAN_ACCENT))
        entry.bind("<FocusOut>", lambda e: bdr.configure(bg=BORDER_SUBTLE))

        return entry, inner

    # 1. Full Name
    name_entry, _ = create_field_entry(form_frame, 0, "Full Name *")

    # 2. Date of Birth & Gender in columns
    two_col = tk.Frame(form_frame, bg=BG_CARD)
    two_col.grid(row=2, column=0, sticky="ew", pady=0)
    two_col.columnconfigure(0, weight=1)
    two_col.columnconfigure(1, weight=1)

    # DOB
    tk.Label(
        two_col,
        text="Date of Birth (YYYY-MM-DD) *",
        font=FONT_BODY_BOLD,
        bg=BG_CARD,
        fg=TEXT_LIGHT
    ).grid(row=0, column=0, sticky="w", pady=(4, 2), padx=(0, 8))

    dob_bdr = tk.Frame(two_col, bg=BORDER_SUBTLE, padx=1, pady=1)
    dob_bdr.grid(row=1, column=0, sticky="ew", pady=(0, 8), padx=(0, 8))

    dob_entry = tk.Entry(
        dob_bdr,
        bg=BG_INPUT,
        fg=TEXT_WHITE,
        insertbackground=CYAN_ACCENT,
        font=FONT_BODY,
        relief=tk.FLAT,
        bd=5
    )
    dob_entry.pack(fill=tk.X)
    dob_entry.bind("<FocusIn>", lambda e: dob_bdr.configure(bg=CYAN_ACCENT))
    dob_entry.bind("<FocusOut>", lambda e: dob_bdr.configure(bg=BORDER_SUBTLE))

    # Gender
    tk.Label(
        two_col,
        text="Gender *",
        font=FONT_BODY_BOLD,
        bg=BG_CARD,
        fg=TEXT_LIGHT
    ).grid(row=0, column=1, sticky="w", pady=(4, 2), padx=(8, 0))

    gender_bdr = tk.Frame(two_col, bg=BORDER_SUBTLE, padx=1, pady=1)
    gender_bdr.grid(row=1, column=1, sticky="ew", pady=(0, 8), padx=(8, 0))

    gender_var = tk.StringVar(value="Select Gender")
    gender_menu = tk.OptionMenu(
        gender_bdr,
        gender_var,
        "Male",
        "Female",
        "Other"
    )
    gender_menu.configure(
        bg=BG_INPUT,
        fg=TEXT_WHITE,
        activebackground=BG_CARD,
        activeforeground=CYAN_ACCENT,
        relief=tk.FLAT,
        bd=0,
        highlightthickness=0,
        font=FONT_BODY
    )
    gender_menu["menu"].configure(
        bg=BG_CARD,
        fg=TEXT_WHITE,
        activebackground=BLUE_PRIMARY,
        activeforeground=TEXT_WHITE
    )
    gender_menu.pack(fill=tk.X)

    # 3. Age (Optional)
    tk.Label(
        form_frame,
        text="Age (Optional - auto calculated from DOB if blank)",
        font=FONT_BODY_BOLD,
        bg=BG_CARD,
        fg=TEXT_LIGHT
    ).grid(row=3, column=0, sticky="w", pady=(4, 2))

    age_bdr = tk.Frame(form_frame, bg=BORDER_SUBTLE, padx=1, pady=1)
    age_bdr.grid(row=4, column=0, sticky="ew", pady=(0, 8))

    age_entry = tk.Entry(
        age_bdr,
        bg=BG_INPUT,
        fg=TEXT_WHITE,
        insertbackground=CYAN_ACCENT,
        font=FONT_BODY,
        relief=tk.FLAT,
        bd=5
    )
    age_entry.pack(fill=tk.X)
    age_entry.bind("<FocusIn>", lambda e: age_bdr.configure(bg=CYAN_ACCENT))
    age_entry.bind("<FocusOut>", lambda e: age_bdr.configure(bg=BORDER_SUBTLE))

    # 4. Password with Show/Hide
    password_entry, p_inner = create_field_entry(form_frame, 5, "Password *", is_pass=True)

    show_pass_var = tk.BooleanVar(value=False)

    def toggle_pass():
        if show_pass_var.get():
            password_entry.configure(show="*")
            show_pass_var.set(False)
            eye_btn.configure(text="👁")
        else:
            password_entry.configure(show="")
            show_pass_var.set(True)
            eye_btn.configure(text="🔒")

    eye_btn = tk.Button(
        p_inner,
        text="👁",
        font=("Segoe UI", 9),
        bg=BG_INPUT,
        fg=TEXT_MUTED,
        activebackground=BG_INPUT,
        activeforeground=CYAN_ACCENT,
        bd=0,
        relief=tk.FLAT,
        cursor="hand2",
        command=toggle_pass
    )
    eye_btn.pack(side=tk.RIGHT, padx=8)

    # ---------------- Register Function ----------------
    def register():
        full_name = name_entry.get().strip()
        dob = dob_entry.get().strip()
        gender = gender_var.get()
        age = age_entry.get().strip()
        password = password_entry.get().strip()

        # Validation
        if not full_name or not dob or gender == "Select Gender" or not password:
            status_label.configure(
                text="⚠ Please fill in all required fields marked with *",
                fg=RED_ALERT
            )
            return

        # Validate DOB
        try:
            birth_date = datetime.strptime(dob, "%Y-%m-%d")
            if not age:
                age = str((datetime.now() - birth_date).days // 365)
        except ValueError:
            status_label.configure(
                text="✕ Invalid date format. Please use YYYY-MM-DD (e.g. 2005-10-16).",
                fg=RED_ALERT
            )
            return

        # Database
        conn = get_connection()
        if conn is None:
            status_label.configure(
                text="✕ Database connection failed. Verify MySQL service.",
                fg=RED_ALERT
            )
            return

        try:
            cursor = conn.cursor(buffered=True)
            query = """
            INSERT INTO register
            (full_name, dob, gender, age, password)
            VALUES (%s, %s, %s, %s, %s)
            """
            values = (full_name, dob, gender, age, password)

            cursor.execute(query, values)
            conn.commit()

            cursor.close()
            conn.close()

            messagebox.showinfo(
                "Registration Successful",
                f"Account created successfully for {full_name}!\nYou can now log in."
            )

            root.destroy()
            from auth.login import login_window
            login_window()

        except Exception as err:
            status_label.configure(text=f"Database Error: {err}", fg=RED_ALERT)
            try:
                conn.close()
            except Exception:
                pass

    def back_to_login():
        root.destroy()
        from auth.login import login_window
        login_window()

    # Action Buttons
    btn_box = tk.Frame(card, bg=BG_CARD)
    btn_box.pack(fill=tk.X, pady=(12, 0))

    reg_btn = CyberButton(
        btn_box,
        text="🛡️ CREATE OPERATOR ACCOUNT",
        command=register,
        bg=BLUE_PRIMARY,
        hover_bg=BLUE_HOVER,
        font=FONT_BODY_BOLD,
        pady=9
    )
    reg_btn.pack(fill=tk.X, pady=(0, 6))

    back_btn = CyberButton(
        btn_box,
        text="← Back to Login",
        command=back_to_login,
        bg="#14213d",
        hover_bg="#1d2e52",
        fg=CYAN_ACCENT,
        font=FONT_SMALL,
        pady=6
    )
    back_btn.pack(fill=tk.X)

    name_entry.focus_set()
    root.mainloop()


if __name__ == "__main__":
    registration_window()