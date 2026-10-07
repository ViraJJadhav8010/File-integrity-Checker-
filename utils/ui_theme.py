"""
UI Theme and Modern Component Library for File Integrity Checker
Cybersecurity / Digital Forensics Dark Theme
"""

import os
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

# -------------------------------------------------------------
# Color Palette - Professional Digital Forensics / Cyber Dark
# -------------------------------------------------------------
BG_DARK = "#090d16"         # Deepest navy background
BG_SIDEBAR = "#0c1424"      # Sidebar navy
BG_HEADER = "#0d172c"       # Header navy
BG_CARD = "#111d35"         # Elevated card surface
BG_CARD_HOVER = "#152442"   # Elevated card surface on hover
BG_INPUT = "#0b1528"        # Input background
BORDER_SUBTLE = "#1d3154"   # Card & divider borders
BORDER_ACTIVE = "#00e5ff"   # Cyber cyan focus border

TEXT_WHITE = "#f8fafc"      # Primary bright text
TEXT_LIGHT = "#e2e8f0"      # Standard text
TEXT_MUTED = "#94a3b8"      # Secondary descriptions
TEXT_DIM = "#64748b"        # Low-emphasis text

CYAN_ACCENT = "#00e5ff"     # Primary cyber cyan
BLUE_PRIMARY = "#2563eb"    # Action blue
BLUE_HOVER = "#1d4ed8"      # Blue hover
GREEN_SAFE = "#10b981"      # Forensic Safe / Verified
GREEN_HOVER = "#059669"     # Green hover
RED_ALERT = "#ef4444"       # Tamper / Modified / Danger
RED_HOVER = "#dc2626"       # Red hover
ORANGE_WARN = "#f59e0b"     # Warning / Attention
PURPLE_ACCENT = "#8b5cf6"   # Secondary accent

# -------------------------------------------------------------
# Fonts
# -------------------------------------------------------------
FONT_TITLE_LARGE = ("Segoe UI", 18, "bold")
FONT_TITLE = ("Segoe UI", 14, "bold")
FONT_SUBTITLE = ("Segoe UI", 10)
FONT_SECTION = ("Segoe UI", 12, "bold")
FONT_BODY = ("Segoe UI", 10)
FONT_BODY_BOLD = ("Segoe UI", 10, "bold")
FONT_SMALL = ("Segoe UI", 9)
FONT_CODE = ("Consolas", 10)
FONT_CODE_BOLD = ("Consolas", 10, "bold")
FONT_STAT_NUM = ("Segoe UI", 22, "bold")


def center_window(window, width, height):
    """Center a Tkinter window on the primary screen."""
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = max(0, (screen_width - width) // 2)
    y = max(0, (screen_height - height) // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")


def get_shield_photo(size=(48, 48)):
    """Loads and returns ImageTk for shield icon if available."""
    icon_path = os.path.join("assets", "shield_icon.png")
    if os.path.exists(icon_path):
        try:
            img = Image.open(icon_path)
            img = img.resize(size, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception:
            return None
    return None


class CyberButton(tk.Button):
    """Modern flat button with hover transitions and hand cursor."""
    def __init__(self, parent, text, command=None, bg=BLUE_PRIMARY, fg=TEXT_WHITE,
                 hover_bg=BLUE_HOVER, hover_fg=TEXT_WHITE, font=FONT_BODY_BOLD,
                 padx=16, pady=8, width=None, **kwargs):
        self.normal_bg = bg
        self.normal_fg = fg
        self.hover_bg = hover_bg
        self.hover_fg = hover_fg

        btn_kwargs = {
            "text": text,
            "command": command,
            "bg": bg,
            "fg": fg,
            "font": font,
            "activebackground": hover_bg,
            "activeforeground": hover_fg,
            "relief": tk.FLAT,
            "bd": 0,
            "cursor": "hand2",
            "padx": padx,
            "pady": pady,
        }
        if width is not None:
            btn_kwargs["width"] = width
        btn_kwargs.update(kwargs)

        super().__init__(parent, **btn_kwargs)

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, _event):
        self.configure(bg=self.hover_bg, fg=self.hover_fg)

    def _on_leave(self, _event):
        self.configure(bg=self.normal_bg, fg=self.normal_fg)


class CyberCard(tk.Frame):
    """Container frame styled as an elevated dark card with border."""
    def __init__(self, parent, bg=BG_CARD, border_color=BORDER_SUBTLE,
                 accent_top=None, padx=16, pady=16, **kwargs):
        super().__init__(parent, bg=border_color, padx=1, pady=1, **kwargs)
        self.inner = tk.Frame(self, bg=bg, padx=padx, pady=pady)
        self.inner.pack(fill=tk.BOTH, expand=True)

        if accent_top:
            self.accent_bar = tk.Frame(self.inner, bg=accent_top, height=3)
            self.accent_bar.pack(fill=tk.X, side=tk.TOP, pady=(0, 10))


class NotificationBanner(tk.Frame):
    """In-window notification banner for immediate user feedback."""
    def __init__(self, parent):
        super().__init__(parent, bg=BG_CARD, padx=14, pady=8)
        self.icon_label = tk.Label(
            self, text="ℹ", font=("Segoe UI", 12, "bold"),
            bg=BG_CARD, fg=CYAN_ACCENT
        )
        self.icon_label.pack(side=tk.LEFT, padx=(0, 8))

        self.msg_label = tk.Label(
            self, text="", font=FONT_BODY,
            bg=BG_CARD, fg=TEXT_LIGHT, justify=tk.LEFT, wraplength=700
        )
        self.msg_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.close_btn = tk.Button(
            self, text="✕", font=("Segoe UI", 9),
            bg=BG_CARD, fg=TEXT_MUTED, bd=0, relief=tk.FLAT,
            cursor="hand2", command=self.hide
        )
        self.close_btn.pack(side=tk.RIGHT, padx=(8, 0))
        self._timer = None

    def show(self, message, msg_type="info", auto_dismiss_ms=4500):
        if self._timer:
            self.after_cancel(self._timer)

        type_styles = {
            "success": (GREEN_SAFE, "✓", "#0c281e"),
            "error": (RED_ALERT, "✕", "#2d1217"),
            "warning": (ORANGE_WARN, "⚠", "#2d200d"),
            "info": (CYAN_ACCENT, "ℹ", "#0c223a"),
        }
        color, symbol, bg_tint = type_styles.get(msg_type, (CYAN_ACCENT, "ℹ", BG_CARD))

        self.configure(bg=color, padx=1, pady=1)
        self.icon_label.configure(bg=bg_tint, fg=color, text=symbol)
        self.msg_label.configure(bg=bg_tint, fg=TEXT_WHITE, text=message)
        self.close_btn.configure(bg=bg_tint, fg=TEXT_MUTED)

        # Repack into parent safely
        try:
            self.pack_forget()
            self.pack(fill=tk.X, side=tk.TOP, pady=(0, 10))
        except Exception:
            pass

        if auto_dismiss_ms:
            self._timer = self.after(auto_dismiss_ms, self.hide)

    def hide(self):
        try:
            self.pack_forget()
        except Exception:
            pass


def apply_treeview_cyber_style():
    """Configures ttk Treeview to match the cybersecurity dark theme."""
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except Exception:
        pass

    style.configure(
        "Cyber.Treeview",
        background=BG_CARD,
        foreground=TEXT_LIGHT,
        fieldbackground=BG_CARD,
        rowheight=32,
        font=FONT_BODY,
        borderwidth=0
    )
    style.configure(
        "Cyber.Treeview.Heading",
        background=BG_CARD_ALT if "BG_CARD_ALT" in globals() else "#162544",
        foreground=CYAN_ACCENT,
        font=FONT_BODY_BOLD,
        borderwidth=1,
        relief="flat"
    )
    style.map(
        "Cyber.Treeview.Heading",
        background=[("active", "#1e3560")]
    )
    style.map(
        "Cyber.Treeview",
        background=[("selected", "#1e3a6a")],
        foreground=[("selected", TEXT_WHITE)]
    )

    # Scrollbar
    style.configure(
        "Cyber.Vertical.TScrollbar",
        background=BG_SIDEBAR,
        troughcolor=BG_DARK,
        borderwidth=0,
        arrowsize=12
    )
