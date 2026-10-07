import tkinter as tk
from tkinter import messagebox
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


def login_window():
    login_root = tk.Tk()
    login_root.title("File Integrity Checker - Operator Login")
    login_root.geometry("820x540")
    login_root.resizable(False, False)
    login_root.configure(bg=BG_DARK)
    center_window(login_root, 820, 540)

    # ---------------- Background Canvas ----------------
    canvas = tk.Canvas(login_root, width=820, height=540, bg=BG_DARK, highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)

    bg_photo = None
    if os.path.exists("assets/Cyber.jpg"):
        try:
            bg_image = Image.open("assets/Cyber.jpg")
            bg_image = bg_image.resize((820, 540), Image.Resampling.LANCZOS)
            bg_photo = ImageTk.PhotoImage(bg_image)
            canvas.create_image(0, 0, anchor="nw", image=bg_photo)
        except Exception:
            bg_photo = None

    # Dark translucent overlay rectangle on canvas
    canvas.create_rectangle(0, 0, 820, 540, fill="#050a14", stipple="gray50")

    # ---------------- Center Card ----------------
    card_border = tk.Frame(canvas, bg=CYAN_ACCENT, padx=1, pady=1)
    card_window = canvas.create_window(410, 270, window=card_border, anchor="center")

    card = tk.Frame(card_border, bg=BG_CARD, padx=35, pady=28)
    card.pack()

    # Icon / Logo
    logo_photo = None
    if os.path.exists("assets/shield_icon.png"):
        try:
            logo_img = Image.open("assets/shield_icon.png")
            logo_img = logo_img.resize((52, 52), Image.Resampling.LANCZOS)
            logo_photo = ImageTk.PhotoImage(logo_img)
            logo_label = tk.Label(card, image=logo_photo, bg=BG_CARD)
            logo_label.image = logo_photo
            logo_label.pack(pady=(0, 6))
        except Exception:
            logo_photo = None

    if not logo_photo:
        icon_fallback = tk.Label(card, text="🛡️", font=("Segoe UI", 26), bg=BG_CARD, fg=CYAN_ACCENT)
        icon_fallback.pack(pady=(0, 6))

    # Title & Subtitle
    tk.Label(
        card,
        text="FILE INTEGRITY CHECKER",
        font=FONT_TITLE_LARGE,
        bg=BG_CARD,
        fg=TEXT_WHITE
    ).pack()

    tk.Label(
        card,
        text="Digital Forensics & File Security",
        font=FONT_SUBTITLE,
        bg=BG_CARD,
        fg=CYAN_ACCENT
    ).pack(pady=(2, 14))

    # Inline Status / Error Message
    status_label = tk.Label(
        card,
        text="",
        font=FONT_SMALL,
        bg=BG_CARD,
        fg=RED_ALERT,
        wraplength=340
    )
    status_label.pack(pady=(0, 6))

    # Form Container
    form_frame = tk.Frame(card, bg=BG_CARD)
    form_frame.pack(fill=tk.X)

    # Username Field
    tk.Label(
        form_frame,
        text="Username / Full Name",
        font=FONT_BODY_BOLD,
        bg=BG_CARD,
        fg=TEXT_LIGHT
    ).pack(anchor="w", pady=(0, 4))

    u_border = tk.Frame(form_frame, bg=BORDER_SUBTLE, padx=1, pady=1)
    u_border.pack(fill=tk.X, pady=(0, 12))

    username_entry = tk.Entry(
        u_border,
        bg=BG_INPUT,
        fg=TEXT_WHITE,
        insertbackground=CYAN_ACCENT,
        font=FONT_BODY,
        relief=tk.FLAT,
        bd=6
    )
    username_entry.pack(fill=tk.X)

    # Focus effects
    username_entry.bind("<FocusIn>", lambda e: u_border.configure(bg=CYAN_ACCENT))
    username_entry.bind("<FocusOut>", lambda e: u_border.configure(bg=BORDER_SUBTLE))

    # Password Field
    tk.Label(
        form_frame,
        text="Password",
        font=FONT_BODY_BOLD,
        bg=BG_CARD,
        fg=TEXT_LIGHT
    ).pack(anchor="w", pady=(0, 4))

    p_border = tk.Frame(form_frame, bg=BORDER_SUBTLE, padx=1, pady=1)
    p_border.pack(fill=tk.X, pady=(0, 4))

    p_inner = tk.Frame(p_border, bg=BG_INPUT)
    p_inner.pack(fill=tk.X)

    password_entry = tk.Entry(
        p_inner,
        show="*",
        bg=BG_INPUT,
        fg=TEXT_WHITE,
        insertbackground=CYAN_ACCENT,
        font=FONT_BODY,
        relief=tk.FLAT,
        bd=6
    )
    password_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

    # Show/Hide Password Toggle
    show_password_var = tk.BooleanVar(value=False)

    def toggle_password():
        if show_password_var.get():
            password_entry.configure(show="*")
            show_password_var.set(False)
            eye_btn.configure(text="👁")
        else:
            password_entry.configure(show="")
            show_password_var.set(True)
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
        command=toggle_password
    )
    eye_btn.pack(side=tk.RIGHT, padx=8)

    password_entry.bind("<FocusIn>", lambda e: p_border.configure(bg=CYAN_ACCENT))
    password_entry.bind("<FocusOut>", lambda e: p_border.configure(bg=BORDER_SUBTLE))

    # ---------------- Login Function ----------------
    def perform_login():
        username = username_entry.get().strip()
        password = password_entry.get().strip()

        if not username or not password:
            status_label.configure(
                text="⚠ Please enter both username and password.",
                fg=RED_ALERT
            )
            return

        status_label.configure(text="Connecting to security database...", fg=CYAN_ACCENT)
        login_root.update_idletasks()

        conn = get_connection()
        if conn is None:
            status_label.configure(
                text="✕ Database connection failed. Ensure MySQL is running.",
                fg=RED_ALERT
            )
            return

        cursor = None
        try:
            # buffered=True fixes "Unread result found"
            cursor = conn.cursor(buffered=True)

            query = """
                SELECT id, full_name
                FROM register
                WHERE full_name = %s
                AND password = %s
                LIMIT 1
            """

            cursor.execute(query, (username, password))
            result = cursor.fetchone()

            if result:
                status_label.configure(
                    text="✓ Login verified. Initializing dashboard...",
                    fg=GREEN_SAFE
                )
                login_root.update_idletasks()

                cursor.close()
                conn.close()

                login_root.destroy()

                from checker.integrity_checker import FileIntegrityChecker
                FileIntegrityChecker(username=username)

            else:
                status_label.configure(
                    text="✕ Invalid username or password.",
                    fg=RED_ALERT
                )
                cursor.close()
                conn.close()

        except Exception as error:
            status_label.configure(text=f"Database Error: {error}", fg=RED_ALERT)
            try:
                if cursor:
                    cursor.close()
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass

    # Enter key triggers login
    username_entry.bind("<Return>", lambda e: perform_login())
    password_entry.bind("<Return>", lambda e: perform_login())

    # ---------------- Register Navigation ----------------
    def open_register():
        login_root.destroy()
        from auth.register import registration_window
        registration_window()

    # ---------------- Action Buttons ----------------
    btn_container = tk.Frame(card, bg=BG_CARD)
    btn_container.pack(fill=tk.X, pady=(16, 0))

    login_btn = CyberButton(
        btn_container,
        text="🔐 SECURE LOGIN",
        command=perform_login,
        bg=BLUE_PRIMARY,
        hover_bg=BLUE_HOVER,
        font=FONT_BODY_BOLD,
        pady=9
    )
    login_btn.pack(fill=tk.X, pady=(0, 8))

    reg_btn = CyberButton(
        btn_container,
        text="Create New Account (Register)",
        command=open_register,
        bg="#14213d",
        hover_bg="#1d2e52",
        fg=CYAN_ACCENT,
        font=FONT_SMALL,
        pady=7
    )
    reg_btn.pack(fill=tk.X)

    # Focus initial field
    username_entry.focus_set()

    login_root.mainloop()


if __name__ == "__main__":
    login_window()