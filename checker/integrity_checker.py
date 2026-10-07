"""
File Integrity Checker - Digital Forensics Dashboard
Modern Cybersecurity & Digital Forensics Monitoring System
"""

import os
import sys
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

from config.database import get_connection
from utils.hash_utils import compute_md5
from utils.ui_theme import (
    BG_DARK, BG_SIDEBAR, BG_HEADER, BG_CARD, BG_CARD_HOVER, BG_INPUT,
    BORDER_SUBTLE, BORDER_ACTIVE, TEXT_WHITE, TEXT_LIGHT, TEXT_MUTED, TEXT_DIM,
    CYAN_ACCENT, BLUE_PRIMARY, BLUE_HOVER, GREEN_SAFE, GREEN_HOVER,
    RED_ALERT, RED_HOVER, ORANGE_WARN, PURPLE_ACCENT,
    FONT_TITLE_LARGE, FONT_TITLE, FONT_SUBTITLE, FONT_SECTION,
    FONT_BODY, FONT_BODY_BOLD, FONT_SMALL, FONT_CODE, FONT_CODE_BOLD, FONT_STAT_NUM,
    CyberButton, CyberCard, NotificationBanner, center_window, apply_treeview_cyber_style,
    get_shield_photo
)


class FileIntegrityChecker:

    def __init__(self, username="Forensic Analyst"):
        self.username = username or "Forensic Analyst"

        self.conn = get_connection()
        if self.conn is None:
            return

        self.cursor = self.conn.cursor(buffered=True)

        # Session Metrics & Audit History
        self.session_checks = 0
        self.session_verified = 0
        self.session_modified = 0
        self.audit_history = []
        self.scheduler_running = False
        self.scheduled_target = None
        self.selected_file_info = {}

        self.initialize_database()
        self.setup_ui()

    # ------------------------------------------------
    # Database Initialization (Preserved)
    # ------------------------------------------------
    def initialize_database(self):
        try:
            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS file_hashes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    file_name VARCHAR(255),
                    file_hash VARCHAR(32),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    # UI Setup & Main Layout
    # ------------------------------------------------
    def setup_ui(self):
        self.root = tk.Tk()
        self.root.title("File Integrity Checker - Digital Forensics Monitoring System")
        self.root.geometry("1120x720")
        self.root.minsize(980, 620)
        self.root.configure(bg=BG_DARK)
        center_window(self.root, 1120, 720)

        apply_treeview_cyber_style()

        # Shared File Path Variables
        self.file_path_var = tk.StringVar()
        self.sched_file_path_var = tk.StringVar()

        # Layout Containers
        self._build_header()
        self._build_body()

        # Default Active Navigation Tab: Dashboard
        self.switch_nav("dashboard")
        self.refresh_database_records()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()

    # ------------------------------------------------
    # Header Bar
    # ------------------------------------------------
    def _build_header(self):
        self.header_frame = tk.Frame(self.root, bg=BG_HEADER, height=64, padx=20, pady=10)
        self.header_frame.pack(side=tk.TOP, fill=tk.X)

        # Left: Logo & Application Title
        left_box = tk.Frame(self.header_frame, bg=BG_HEADER)
        left_box.pack(side=tk.LEFT, fill=tk.Y)

        self.shield_photo = get_shield_photo(size=(38, 38))
        if self.shield_photo:
            logo_lbl = tk.Label(left_box, image=self.shield_photo, bg=BG_HEADER)
            logo_lbl.pack(side=tk.LEFT, padx=(0, 12))
        else:
            logo_lbl = tk.Label(left_box, text="🛡️", font=("Segoe UI", 20), bg=BG_HEADER, fg=CYAN_ACCENT)
            logo_lbl.pack(side=tk.LEFT, padx=(0, 12))

        title_box = tk.Frame(left_box, bg=BG_HEADER)
        title_box.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(
            title_box,
            text="FILE INTEGRITY CHECKER",
            font=FONT_TITLE,
            bg=BG_HEADER,
            fg=TEXT_WHITE
        ).pack(anchor="w")

        tk.Label(
            title_box,
            text="Digital Forensics & File Monitoring System",
            font=FONT_SMALL,
            bg=BG_HEADER,
            fg=CYAN_ACCENT
        ).pack(anchor="w")

        # Right: User Profile Badge & Logout Button
        right_box = tk.Frame(self.header_frame, bg=BG_HEADER)
        right_box.pack(side=tk.RIGHT, fill=tk.Y)

        user_badge = tk.Frame(right_box, bg="#111f38", padx=12, pady=5, bd=1, relief=tk.SOLID)
        user_badge.pack(side=tk.LEFT, padx=(0, 14))

        tk.Label(
            user_badge,
            text="● ONLINE",
            font=("Segoe UI", 8, "bold"),
            bg="#111f38",
            fg=GREEN_SAFE
        ).pack(side=tk.LEFT, padx=(0, 6))

        tk.Label(
            user_badge,
            text=f"Analyst: {self.username}",
            font=FONT_BODY_BOLD,
            bg="#111f38",
            fg=TEXT_WHITE
        ).pack(side=tk.LEFT)

        CyberButton(
            right_box,
            text="🚪 Logout",
            command=self.logout,
            bg="#2c141d",
            hover_bg=RED_HOVER,
            fg="#f87171",
            font=FONT_SMALL,
            padx=12,
            pady=5
        ).pack(side=tk.LEFT)

        # Header subtle divider
        div = tk.Frame(self.root, bg=BORDER_SUBTLE, height=1)
        div.pack(side=tk.TOP, fill=tk.X)

    # ------------------------------------------------
    # Body (Sidebar + Content View Area)
    # ------------------------------------------------
    def _build_body(self):
        body_container = tk.Frame(self.root, bg=BG_DARK)
        body_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Left Sidebar
        self.sidebar_frame = tk.Frame(body_container, bg=BG_SIDEBAR, width=220)
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar_frame.pack_propagate(False)

        # Sidebar Header Label
        tk.Label(
            self.sidebar_frame,
            text="NAVIGATION MENU",
            font=("Segoe UI", 8, "bold"),
            bg=BG_SIDEBAR,
            fg=TEXT_DIM
        ).pack(anchor="w", padx=18, pady=(16, 10))

        # Nav Buttons list
        self.nav_buttons = {}
        nav_items = [
            ("dashboard", "🏠  Dashboard"),
            ("browse", "📁  Browse File"),
            ("store", "🔐  Store Hash"),
            ("check", "🔍  Check Integrity"),
            ("reports", "📊  Reports / History"),
            ("settings", "⚙️  Settings & Scheduler"),
        ]

        for key, text in nav_items:
            btn = tk.Button(
                self.sidebar_frame,
                text=text,
                font=FONT_BODY_BOLD,
                bg=BG_SIDEBAR,
                fg=TEXT_LIGHT,
                activebackground="#152545",
                activeforeground=CYAN_ACCENT,
                bd=0,
                relief=tk.FLAT,
                anchor="w",
                padx=18,
                pady=11,
                cursor="hand2",
                command=lambda k=key: self.switch_nav(k)
            )
            btn.pack(fill=tk.X, pady=1)
            self.nav_buttons[key] = btn

        # Sidebar Bottom System Info
        side_footer = tk.Frame(self.sidebar_frame, bg=BG_SIDEBAR, padx=16, pady=16)
        side_footer.pack(side=tk.BOTTOM, fill=tk.X)

        tk.Label(
            side_footer,
            text="SYSTEM STATUS",
            font=("Segoe UI", 8, "bold"),
            bg=BG_SIDEBAR,
            fg=TEXT_DIM
        ).pack(anchor="w")

        tk.Label(
            side_footer,
            text="MySQL: Connected\nEngine: MD5 Forensics",
            font=("Segoe UI", 8),
            bg=BG_SIDEBAR,
            fg=TEXT_MUTED,
            justify=tk.LEFT
        ).pack(anchor="w", pady=(3, 10))

        CyberButton(
            side_footer,
            text="🚪 Sign Out",
            command=self.logout,
            bg="#18233a",
            hover_bg="#223254",
            fg=TEXT_LIGHT,
            font=FONT_SMALL,
            pady=5
        ).pack(fill=tk.X)

        # Vertical Divider
        v_div = tk.Frame(body_container, bg=BORDER_SUBTLE, width=1)
        v_div.pack(side=tk.LEFT, fill=tk.Y)

        # Right Content Container
        self.content_area = tk.Frame(body_container, bg=BG_DARK, padx=22, pady=18)
        self.content_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Reusable Notification Banner at the top of content area
        self.notif_box = tk.Frame(self.content_area, bg=BG_DARK)
        self.notif_box.pack(side=tk.TOP, fill=tk.X)
        self.notification = NotificationBanner(self.notif_box)

        # View Pages Container
        self.views_container = tk.Frame(self.content_area, bg=BG_DARK)
        self.views_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Initialize View Frames
        self.view_frames = {
            "dashboard": tk.Frame(self.views_container, bg=BG_DARK),
            "browse": tk.Frame(self.views_container, bg=BG_DARK),
            "store": tk.Frame(self.views_container, bg=BG_DARK),
            "check": tk.Frame(self.views_container, bg=BG_DARK),
            "reports": tk.Frame(self.views_container, bg=BG_DARK),
            "settings": tk.Frame(self.views_container, bg=BG_DARK),
        }

        # Build individual views
        self._build_dashboard_view(self.view_frames["dashboard"])
        self._build_browse_view(self.view_frames["browse"])
        self._build_store_view(self.view_frames["store"])
        self._build_check_view(self.view_frames["check"])
        self._build_reports_view(self.view_frames["reports"])
        self._build_settings_view(self.view_frames["settings"])

    # ------------------------------------------------
    # Navigation Switcher
    # ------------------------------------------------
    def switch_nav(self, target_key):
        # Update sidebar button states
        for key, btn in self.nav_buttons.items():
            if key == target_key:
                btn.configure(bg="#16294a", fg=CYAN_ACCENT)
            else:
                btn.configure(bg=BG_SIDEBAR, fg=TEXT_LIGHT)

        # Switch visible view frame
        for key, frame in self.view_frames.items():
            if key == target_key:
                frame.pack(fill=tk.BOTH, expand=True)
            else:
                frame.pack_forget()

        # View-specific refresh
        if target_key == "dashboard":
            self.refresh_database_records()
        elif target_key == "reports":
            self.refresh_reports_table()

    # =========================================================
    # VIEW 1: DASHBOARD
    # =========================================================
    def _build_dashboard_view(self, parent):
        # Header Title
        title_box = tk.Frame(parent, bg=BG_DARK)
        title_box.pack(fill=tk.X, pady=(0, 14))

        tk.Label(
            title_box,
            text="Forensics Overview & File Monitoring",
            font=FONT_TITLE,
            bg=BG_DARK,
            fg=TEXT_WHITE
        ).pack(side=tk.LEFT)

        CyberButton(
            title_box,
            text="🔄 Refresh Data",
            command=self.refresh_database_records,
            bg="#182846",
            hover_bg="#223a63",
            fg=CYAN_ACCENT,
            font=FONT_SMALL,
            pady=4
        ).pack(side=tk.RIGHT)

        # ---------------- Summary Metric Cards ----------------
        cards_grid = tk.Frame(parent, bg=BG_DARK)
        cards_grid.pack(fill=tk.X, pady=(0, 16))
        for i in range(4):
            cards_grid.columnconfigure(i, weight=1)

        self.stat_cards = {}
        card_configs = [
            ("total_files", "Total Monitored", "0", CYAN_ACCENT, "📁", 0),
            ("verified_files", "Verified Safe", "0", GREEN_SAFE, "🟢", 1),
            ("modified_files", "Tamper Violations", "0", RED_ALERT, "🔴", 2),
            ("total_checks", "Integrity Audits", "0", ORANGE_WARN, "🔍", 3),
        ]

        for key, label_text, default_val, accent_color, icon_sym, col in card_configs:
            c_outer = tk.Frame(cards_grid, bg=BORDER_SUBTLE, padx=1, pady=1)
            c_outer.grid(row=0, column=col, sticky="nsew", padx=5)

            c_inner = tk.Frame(c_outer, bg=BG_CARD, padx=14, pady=12)
            c_inner.pack(fill=tk.BOTH, expand=True)

            top_row = tk.Frame(c_inner, bg=BG_CARD)
            top_row.pack(fill=tk.X)

            tk.Label(
                top_row,
                text=label_text.upper(),
                font=("Segoe UI", 8, "bold"),
                bg=BG_CARD,
                fg=TEXT_MUTED
            ).pack(side=tk.LEFT)

            tk.Label(
                top_row,
                text=icon_sym,
                font=("Segoe UI", 11),
                bg=BG_CARD,
                fg=accent_color
            ).pack(side=tk.RIGHT)

            val_lbl = tk.Label(
                c_inner,
                text=default_val,
                font=FONT_STAT_NUM,
                bg=BG_CARD,
                fg=TEXT_WHITE
            )
            val_lbl.pack(anchor="w", pady=(4, 0))

            self.stat_cards[key] = val_lbl

        # ---------------- File Integrity Table ----------------
        table_card = tk.Frame(parent, bg=BORDER_SUBTLE, padx=1, pady=1)
        table_card.pack(fill=tk.BOTH, expand=True)

        table_inner = tk.Frame(table_card, bg=BG_CARD, padx=16, pady=14)
        table_inner.pack(fill=tk.BOTH, expand=True)

        # Table Control Bar (Search + Actions)
        t_header = tk.Frame(table_inner, bg=BG_CARD)
        t_header.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            t_header,
            text="CRYPTOGRAPHIC BASELINE REGISTRY",
            font=FONT_SECTION,
            bg=BG_CARD,
            fg=TEXT_WHITE
        ).pack(side=tk.LEFT)

        # Search Box
        search_box = tk.Frame(t_header, bg=BG_CARD)
        search_box.pack(side=tk.RIGHT)

        tk.Label(
            search_box,
            text="Filter:",
            font=FONT_SMALL,
            bg=BG_CARD,
            fg=TEXT_MUTED
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.table_search_var = tk.StringVar()
        self.table_search_var.trace("w", lambda *args: self.filter_dashboard_table())

        search_entry = tk.Entry(
            search_box,
            textvariable=self.table_search_var,
            bg=BG_INPUT,
            fg=TEXT_WHITE,
            insertbackground=CYAN_ACCENT,
            font=FONT_BODY,
            bd=3,
            relief=tk.FLAT,
            width=20
        )
        search_entry.pack(side=tk.LEFT)

        # Treeview Table
        tree_frame = tk.Frame(table_inner, bg=BG_CARD)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("name", "hash", "status", "last_checked")
        self.file_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            style="Cyber.Treeview",
            selectmode="browse"
        )

        self.file_tree.heading("name", text="File Name")
        self.file_tree.heading("hash", text="Cryptographic MD5 Hash")
        self.file_tree.heading("status", text="Integrity Status")
        self.file_tree.heading("last_checked", text="Last Audit Time")

        self.file_tree.column("name", width=220, anchor="w")
        self.file_tree.column("hash", width=290, anchor="w")
        self.file_tree.column("status", width=160, anchor="center")
        self.file_tree.column("last_checked", width=160, anchor="center")

        tree_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=tree_scroll.set)

        self.file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Double click to inspect
        self.file_tree.bind("<Double-1>", lambda e: self.view_selected_file_details())

        # Table Action Buttons Bar
        action_bar = tk.Frame(table_inner, bg=BG_CARD)
        action_bar.pack(fill=tk.X, pady=(12, 0))

        CyberButton(
            action_bar,
            text="🔍 Verify Selected",
            command=self.check_selected_table_file,
            bg=BLUE_PRIMARY,
            hover_bg=BLUE_HOVER,
            font=FONT_SMALL,
            pady=6
        ).pack(side=tk.LEFT, padx=(0, 8))

        CyberButton(
            action_bar,
            text="📋 View Details",
            command=self.view_selected_file_details,
            bg="#182c4d",
            hover_bg="#223d6b",
            fg=CYAN_ACCENT,
            font=FONT_SMALL,
            pady=6
        ).pack(side=tk.LEFT, padx=(0, 8))

        CyberButton(
            action_bar,
            text="🗑️ Delete Baseline",
            command=self.delete_selected_file_hash,
            bg="#2d161a",
            hover_bg=RED_HOVER,
            fg="#f87171",
            font=FONT_SMALL,
            pady=6
        ).pack(side=tk.LEFT, padx=(0, 8))

        CyberButton(
            action_bar,
            text="➕ Add New File",
            command=lambda: self.switch_nav("browse"),
            bg="#132a22",
            hover_bg=GREEN_HOVER,
            fg="#4ade80",
            font=FONT_SMALL,
            pady=6
        ).pack(side=tk.RIGHT)

    # =========================================================
    # VIEW 2: BROWSE FILE
    # =========================================================
    def _build_browse_view(self, parent):
        tk.Label(
            parent,
            text="File Selection & Forensic Inspection",
            font=FONT_TITLE,
            bg=BG_DARK,
            fg=TEXT_WHITE
        ).pack(anchor="w", pady=(0, 14))

        # Main Inspection Card
        card = tk.Frame(parent, bg=BORDER_SUBTLE, padx=1, pady=1)
        card.pack(fill=tk.BOTH, expand=True)

        card_inner = tk.Frame(card, bg=BG_CARD, padx=24, pady=20)
        card_inner.pack(fill=tk.BOTH, expand=True)

        # Dropzone / Selector Banner
        dropzone = tk.Frame(card_inner, bg="#0d182e", bd=1, relief=tk.SOLID, highlightbackground=BORDER_ACTIVE, highlightthickness=1, padx=20, pady=22)
        dropzone.pack(fill=tk.X, pady=(0, 18))

        tk.Label(
            dropzone,
            text="📁",
            font=("Segoe UI", 32),
            bg="#0d182e",
            fg=CYAN_ACCENT
        ).pack()

        tk.Label(
            dropzone,
            text="SELECT TARGET FILE FOR DIGITAL FORENSICS AUDIT",
            font=FONT_SECTION,
            bg="#0d182e",
            fg=TEXT_WHITE
        ).pack(pady=(4, 2))

        tk.Label(
            dropzone,
            text="Calculate MD5 cryptographic checksum and inspect filesystem parameters",
            font=FONT_SMALL,
            bg="#0d182e",
            fg=TEXT_MUTED
        ).pack(pady=(0, 12))

        # File Entry & Browse Controls
        sel_row = tk.Frame(dropzone, bg="#0d182e")
        sel_row.pack(fill=tk.X, padx=40)

        # IMPORTANT: Keep self.file_entry compatible with existing methods
        self.file_entry = tk.Entry(
            sel_row,
            textvariable=self.file_path_var,
            bg=BG_INPUT,
            fg=TEXT_WHITE,
            insertbackground=CYAN_ACCENT,
            font=FONT_BODY,
            bd=6,
            relief=tk.FLAT
        )
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        CyberButton(
            sel_row,
            text="📂 Browse File...",
            command=self.browse_file,
            bg=BLUE_PRIMARY,
            hover_bg=BLUE_HOVER,
            pady=7
        ).pack(side=tk.RIGHT)

        # Inspection Details Grid
        details_box = tk.LabelFrame(
            card_inner,
            text=" FORENSIC FILE ATTRIBUTES ",
            font=FONT_BODY_BOLD,
            bg=BG_CARD,
            fg=CYAN_ACCENT,
            padx=16,
            pady=14
        )
        details_box.pack(fill=tk.BOTH, expand=True, pady=(0, 16))

        self.browse_labels = {}
        attr_fields = [
            ("name", "File Name:", "No file selected"),
            ("path", "Full Path:", "-"),
            ("size", "File Size:", "-"),
            ("type", "File Type:", "-"),
            ("hash", "Calculated MD5 Checksum:", "-"),
        ]

        for i, (key, label_text, default_text) in enumerate(attr_fields):
            tk.Label(
                details_box,
                text=label_text,
                font=FONT_BODY_BOLD,
                bg=BG_CARD,
                fg=TEXT_LIGHT
            ).grid(row=i, column=0, sticky="w", pady=6, padx=(0, 14))

            val_lbl = tk.Label(
                details_box,
                text=default_text,
                font=FONT_CODE_BOLD if key == "hash" else FONT_BODY,
                bg=BG_CARD,
                fg=CYAN_ACCENT if key == "hash" else TEXT_WHITE,
                anchor="w",
                justify=tk.LEFT
            )
            val_lbl.grid(row=i, column=1, sticky="w", pady=6)
            self.browse_labels[key] = val_lbl

        # Copy Hash Button next to Hash label
        self.copy_hash_btn = CyberButton(
            details_box,
            text="📋 Copy Hash",
            command=self.copy_current_hash_to_clipboard,
            bg="#182c4d",
            hover_bg="#233f6e",
            fg=CYAN_ACCENT,
            font=FONT_SMALL,
            padx=8,
            pady=2
        )
        self.copy_hash_btn.grid(row=4, column=2, sticky="w", padx=10)

        # Action Buttons
        act_row = tk.Frame(card_inner, bg=BG_CARD)
        act_row.pack(fill=tk.X)

        CyberButton(
            act_row,
            text="🔐 Store Baseline Hash",
            command=self.store_file_hash,
            bg=GREEN_SAFE,
            hover_bg=GREEN_HOVER,
            pady=8
        ).pack(side=tk.LEFT, padx=(0, 12))

        CyberButton(
            act_row,
            text="🔍 Verify Integrity Now",
            command=self.check_file_integrity,
            bg=BLUE_PRIMARY,
            hover_bg=BLUE_HOVER,
            pady=8
        ).pack(side=tk.LEFT)

    # =========================================================
    # VIEW 3: STORE HASH
    # =========================================================
    def _build_store_view(self, parent):
        tk.Label(
            parent,
            text="Cryptographic Baseline Storage",
            font=FONT_TITLE,
            bg=BG_DARK,
            fg=TEXT_WHITE
        ).pack(anchor="w", pady=(0, 14))

        card = tk.Frame(parent, bg=BORDER_SUBTLE, padx=1, pady=1)
        card.pack(fill=tk.BOTH, expand=True)

        card_inner = tk.Frame(card, bg=BG_CARD, padx=24, pady=20)
        card_inner.pack(fill=tk.BOTH, expand=True)

        # Instructions / Explanatory Banner
        info_banner = tk.Frame(card_inner, bg="#0d1b33", padx=16, pady=12, bd=1, relief=tk.SOLID)
        info_banner.pack(fill=tk.X, pady=(0, 18))

        tk.Label(
            info_banner,
            text="ℹ BASELINE INTEGRITY PROTOCOL",
            font=FONT_BODY_BOLD,
            bg="#0d1b33",
            fg=CYAN_ACCENT
        ).pack(anchor="w")

        tk.Label(
            info_banner,
            text=(
                "Storing a cryptographic hash creates a tamper-proof digital fingerprint of the selected file "
                "in MySQL (`file_hashes`). If the file was previously registered, its baseline will be updated. "
                "Subsequent integrity audits will compare against this trusted fingerprint."
            ),
            font=FONT_SMALL,
            bg="#0d1b33",
            fg=TEXT_MUTED,
            justify=tk.LEFT,
            wraplength=780
        ).pack(anchor="w", pady=(4, 0))

        # File Selection Block
        tk.Label(
            card_inner,
            text="Target File for Baseline Hash:",
            font=FONT_BODY_BOLD,
            bg=BG_CARD,
            fg=TEXT_LIGHT
        ).pack(anchor="w", pady=(0, 4))

        f_row = tk.Frame(card_inner, bg=BG_CARD)
        f_row.pack(fill=tk.X, pady=(0, 16))

        store_entry = tk.Entry(
            f_row,
            textvariable=self.file_path_var,
            bg=BG_INPUT,
            fg=TEXT_WHITE,
            insertbackground=CYAN_ACCENT,
            font=FONT_BODY,
            bd=6,
            relief=tk.FLAT
        )
        store_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        CyberButton(
            f_row,
            text="📂 Browse...",
            command=self.browse_file,
            bg=BLUE_PRIMARY,
            hover_bg=BLUE_HOVER,
            pady=6
        ).pack(side=tk.RIGHT)

        # Metadata Card
        meta_box = tk.LabelFrame(
            card_inner,
            text=" RECORD PREVIEW ",
            font=FONT_BODY_BOLD,
            bg=BG_CARD,
            fg=CYAN_ACCENT,
            padx=16,
            pady=14
        )
        meta_box.pack(fill=tk.X, pady=(0, 18))

        self.store_meta_labels = {}
        for row, (k, title) in enumerate([
            ("file", "File Name:"),
            ("size", "Size on Disk:"),
            ("location", "File Location:"),
            ("hash", "MD5 Hash:"),
        ]):
            tk.Label(meta_box, text=title, font=FONT_BODY_BOLD, bg=BG_CARD, fg=TEXT_LIGHT).grid(row=row, column=0, sticky="w", pady=5, padx=(0, 12))
            lbl = tk.Label(meta_box, text="-", font=FONT_CODE_BOLD if k == "hash" else FONT_BODY, bg=BG_CARD, fg=CYAN_ACCENT if k == "hash" else TEXT_WHITE)
            lbl.grid(row=row, column=1, sticky="w", pady=5)
            self.store_meta_labels[k] = lbl

        # Store Button
        CyberButton(
            card_inner,
            text="🔐 COMMIT HASH TO DATABASE",
            command=self.store_file_hash,
            bg=GREEN_SAFE,
            hover_bg=GREEN_HOVER,
            font=FONT_BODY_BOLD,
            pady=10
        ).pack(fill=tk.X, pady=(0, 10))

        # Recent Confirmation Box
        self.store_status_card = tk.Label(
            card_inner,
            text="Select a file and click Commit Hash to register.",
            font=FONT_SMALL,
            bg=BG_CARD,
            fg=TEXT_MUTED
        )
        self.store_status_card.pack(anchor="w")

    # =========================================================
    # VIEW 4: CHECK INTEGRITY
    # =========================================================
    def _build_check_view(self, parent):
        tk.Label(
            parent,
            text="Cryptographic Integrity Verification",
            font=FONT_TITLE,
            bg=BG_DARK,
            fg=TEXT_WHITE
        ).pack(anchor="w", pady=(0, 14))

        card = tk.Frame(parent, bg=BORDER_SUBTLE, padx=1, pady=1)
        card.pack(fill=tk.BOTH, expand=True)

        card_inner = tk.Frame(card, bg=BG_CARD, padx=24, pady=20)
        card_inner.pack(fill=tk.BOTH, expand=True)

        # File Selection Row
        tk.Label(
            card_inner,
            text="Select File to Verify Against Database Baseline:",
            font=FONT_BODY_BOLD,
            bg=BG_CARD,
            fg=TEXT_LIGHT
        ).pack(anchor="w", pady=(0, 4))

        c_row = tk.Frame(card_inner, bg=BG_CARD)
        c_row.pack(fill=tk.X, pady=(0, 14))

        check_entry = tk.Entry(
            c_row,
            textvariable=self.file_path_var,
            bg=BG_INPUT,
            fg=TEXT_WHITE,
            insertbackground=CYAN_ACCENT,
            font=FONT_BODY,
            bd=6,
            relief=tk.FLAT
        )
        check_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        CyberButton(
            c_row,
            text="📂 Browse...",
            command=self.browse_file,
            bg=BLUE_PRIMARY,
            hover_bg=BLUE_HOVER,
            pady=6
        ).pack(side=tk.RIGHT)

        # Verification Trigger Button
        CyberButton(
            card_inner,
            text="🔍 RUN INTEGRITY VERIFICATION",
            command=self.check_file_integrity,
            bg=BLUE_PRIMARY,
            hover_bg=BLUE_HOVER,
            font=FONT_BODY_BOLD,
            pady=10
        ).pack(fill=tk.X, pady=(0, 16))

        # ---------------- Prominent Result Card ----------------
        self.result_container = tk.Frame(card_inner, bg=BORDER_SUBTLE, padx=1, pady=1)
        self.result_container.pack(fill=tk.BOTH, expand=True)

        self.result_inner = tk.Frame(self.result_container, bg="#0d182e", padx=20, pady=18)
        self.result_inner.pack(fill=tk.BOTH, expand=True)

        # Result Banner Icon & Title
        self.res_icon_lbl = tk.Label(
            self.result_inner,
            text="⚪",
            font=("Segoe UI", 32),
            bg="#0d182e",
            fg=TEXT_MUTED
        )
        self.res_icon_lbl.pack(pady=(4, 2))

        self.res_title_lbl = tk.Label(
            self.result_inner,
            text="READY FOR INTEGRITY AUDIT",
            font=FONT_TITLE,
            bg="#0d182e",
            fg=TEXT_WHITE
        )
        self.res_title_lbl.pack()

        self.res_desc_lbl = tk.Label(
            self.result_inner,
            text="Select a target file above and press 'Run Integrity Verification'.",
            font=FONT_BODY,
            bg="#0d182e",
            fg=TEXT_MUTED,
            wraplength=700
        )
        self.res_desc_lbl.pack(pady=(3, 16))

        # Comparison Grid
        self.compare_frame = tk.Frame(self.result_inner, bg="#0d182e")
        self.compare_frame.pack(fill=tk.X)

        self.res_fields = {}
        for r, (k, label_txt) in enumerate([
            ("file", "File Name:"),
            ("orig_hash", "Original Baseline Hash:"),
            ("curr_hash", "Current Calculated Hash:"),
            ("check_time", "Verification Timestamp:"),
            ("diff", "Forensic Result:"),
        ]):
            tk.Label(self.compare_frame, text=label_txt, font=FONT_BODY_BOLD, bg="#0d182e", fg=TEXT_LIGHT).grid(row=r, column=0, sticky="w", pady=4, padx=(0, 12))
            val = tk.Label(self.compare_frame, text="-", font=FONT_CODE_BOLD if "hash" in k else FONT_BODY, bg="#0d182e", fg=CYAN_ACCENT if "hash" in k else TEXT_WHITE)
            val.grid(row=r, column=1, sticky="w", pady=4)
            self.res_fields[k] = val

    # =========================================================
    # VIEW 5: REPORTS / HISTORY
    # =========================================================
    def _build_reports_view(self, parent):
        title_box = tk.Frame(parent, bg=BG_DARK)
        title_box.pack(fill=tk.X, pady=(0, 14))

        tk.Label(
            title_box,
            text="Forensics Audit History & Reports",
            font=FONT_TITLE,
            bg=BG_DARK,
            fg=TEXT_WHITE
        ).pack(side=tk.LEFT)

        CyberButton(
            title_box,
            text="📄 Export Forensics Report",
            command=self.export_audit_report,
            bg="#1b3052",
            hover_bg="#264575",
            fg=CYAN_ACCENT,
            font=FONT_SMALL,
            pady=4
        ).pack(side=tk.RIGHT, padx=(8, 0))

        CyberButton(
            title_box,
            text="🔄 Refresh",
            command=self.refresh_reports_table,
            bg="#182846",
            hover_bg="#223a63",
            fg=TEXT_LIGHT,
            font=FONT_SMALL,
            pady=4
        ).pack(side=tk.RIGHT)

        card = tk.Frame(parent, bg=BORDER_SUBTLE, padx=1, pady=1)
        card.pack(fill=tk.BOTH, expand=True)

        card_inner = tk.Frame(card, bg=BG_CARD, padx=16, pady=14)
        card_inner.pack(fill=tk.BOTH, expand=True)

        # Filter bar
        filter_bar = tk.Frame(card_inner, bg=BG_CARD)
        filter_bar.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            filter_bar,
            text="AUDIT LOGS",
            font=FONT_SECTION,
            bg=BG_CARD,
            fg=TEXT_WHITE
        ).pack(side=tk.LEFT)

        # Status filter radio buttons
        status_box = tk.Frame(filter_bar, bg=BG_CARD)
        status_box.pack(side=tk.RIGHT)

        tk.Label(
            status_box,
            text="Filter Status:",
            font=FONT_SMALL,
            bg=BG_CARD,
            fg=TEXT_MUTED
        ).pack(side=tk.LEFT, padx=(0, 6))

        self.report_filter_var = tk.StringVar(value="ALL")
        for mode in ("ALL", "VERIFIED", "MODIFIED"):
            rb = tk.Radiobutton(
                status_box,
                text=mode,
                value=mode,
                variable=self.report_filter_var,
                bg=BG_CARD,
                fg=TEXT_LIGHT,
                selectcolor=BG_INPUT,
                activebackground=BG_CARD,
                activeforeground=CYAN_ACCENT,
                font=FONT_SMALL,
                command=self.filter_reports_table
            )
            rb.pack(side=tk.LEFT, padx=3)

        # Reports Treeview
        rep_tree_frame = tk.Frame(card_inner, bg=BG_CARD)
        rep_tree_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("file", "orig_hash", "curr_hash", "status", "time")
        self.reports_tree = ttk.Treeview(
            rep_tree_frame,
            columns=cols,
            show="headings",
            style="Cyber.Treeview",
            selectmode="browse"
        )

        self.reports_tree.heading("file", text="Target File")
        self.reports_tree.heading("orig_hash", text="Baseline MD5 Hash")
        self.reports_tree.heading("curr_hash", text="Computed MD5 Hash")
        self.reports_tree.heading("status", text="Integrity Result")
        self.reports_tree.heading("time", text="Audit Timestamp")

        self.reports_tree.column("file", width=200, anchor="w")
        self.reports_tree.column("orig_hash", width=240, anchor="w")
        self.reports_tree.column("curr_hash", width=240, anchor="w")
        self.reports_tree.column("status", width=150, anchor="center")
        self.reports_tree.column("time", width=160, anchor="center")

        rep_scroll = ttk.Scrollbar(rep_tree_frame, orient=tk.VERTICAL, command=self.reports_tree.yview)
        self.reports_tree.configure(yscrollcommand=rep_scroll.set)

        self.reports_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        rep_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    # =========================================================
    # VIEW 6: SETTINGS & SCHEDULER
    # =========================================================
    def _build_settings_view(self, parent):
        tk.Label(
            parent,
            text="Settings & Automated Periodic Monitoring",
            font=FONT_TITLE,
            bg=BG_DARK,
            fg=TEXT_WHITE
        ).pack(anchor="w", pady=(0, 14))

        container = tk.Frame(parent, bg=BG_DARK)
        container.pack(fill=tk.BOTH, expand=True)

        # Left Column: Scheduled Checks Frame (Preserved functionality)
        left_card = tk.Frame(container, bg=BORDER_SUBTLE, padx=1, pady=1)
        left_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        sched_inner = tk.Frame(left_card, bg=BG_CARD, padx=20, pady=18)
        sched_inner.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            sched_inner,
            text="⏰ AUTOMATED INTEGRITY SCHEDULER",
            font=FONT_SECTION,
            bg=BG_CARD,
            fg=CYAN_ACCENT
        ).pack(anchor="w", pady=(0, 4))

        tk.Label(
            sched_inner,
            text="Runs background integrity checks at configured intervals using multithreading.",
            font=FONT_SMALL,
            bg=BG_CARD,
            fg=TEXT_MUTED
        ).pack(anchor="w", pady=(0, 16))

        # Target File
        tk.Label(
            sched_inner,
            text="Monitored File Path:",
            font=FONT_BODY_BOLD,
            bg=BG_CARD,
            fg=TEXT_LIGHT
        ).pack(anchor="w", pady=(0, 4))

        s_f_row = tk.Frame(sched_inner, bg=BG_CARD)
        s_f_row.pack(fill=tk.X, pady=(0, 12))

        # IMPORTANT: Keep self.sched_file_entry for backward compatibility
        self.sched_file_entry = tk.Entry(
            s_f_row,
            textvariable=self.sched_file_path_var,
            bg=BG_INPUT,
            fg=TEXT_WHITE,
            insertbackground=CYAN_ACCENT,
            font=FONT_BODY,
            bd=5,
            relief=tk.FLAT
        )
        self.sched_file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        CyberButton(
            s_f_row,
            text="Browse",
            command=self.browse_scheduled_file,
            bg=BLUE_PRIMARY,
            hover_bg=BLUE_HOVER,
            pady=5
        ).pack(side=tk.RIGHT)

        # Interval Entry (Minutes)
        tk.Label(
            sched_inner,
            text="Audit Interval (Minutes):",
            font=FONT_BODY_BOLD,
            bg=BG_CARD,
            fg=TEXT_LIGHT
        ).pack(anchor="w", pady=(0, 4))

        # IMPORTANT: Keep self.interval_entry for backward compatibility
        self.interval_entry = tk.Entry(
            sched_inner,
            width=15,
            bg=BG_INPUT,
            fg=TEXT_WHITE,
            insertbackground=CYAN_ACCENT,
            font=FONT_BODY,
            bd=5,
            relief=tk.FLAT
        )
        self.interval_entry.insert(0, "5")
        self.interval_entry.pack(anchor="w", pady=(0, 16))

        CyberButton(
            sched_inner,
            text="▶ Start Scheduled Checks",
            command=self.schedule_integrity_check,
            bg=ORANGE_WARN,
            hover_bg="#d97706",
            font=FONT_BODY_BOLD,
            pady=9
        ).pack(fill=tk.X, pady=(0, 14))

        # Scheduler Status Indicator
        self.sched_status_lbl = tk.Label(
            sched_inner,
            text="Status: No active background scheduler running.",
            font=FONT_SMALL,
            bg=BG_CARD,
            fg=TEXT_MUTED
        )
        self.sched_status_lbl.pack(anchor="w")

        # Right Column: System Diagnostics & About Info
        right_card = tk.Frame(container, bg=BORDER_SUBTLE, padx=1, pady=1)
        right_card.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(8, 0))

        diag_inner = tk.Frame(right_card, bg=BG_CARD, padx=20, pady=18)
        diag_inner.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            diag_inner,
            text="🛡️ FORENSICS & SYSTEM INFORMATION",
            font=FONT_SECTION,
            bg=BG_CARD,
            fg=CYAN_ACCENT
        ).pack(anchor="w", pady=(0, 12))

        about_text = (
            "File Integrity Checker detects unauthorized modifications to critical system and user files "
            "by calculating cryptographic MD5 hashes and evaluating baseline deviations.\n\n"
            "Key Capabilities:\n"
            "• Cryptographic MD5 checksum computation (RFC 1321)\n"
            "• Baseline storage in MySQL security database\n"
            "• Instant tamper & alteration detection\n"
            "• Multithreaded background monitoring scheduler"
        )

        tk.Label(
            diag_inner,
            text=about_text,
            font=FONT_SMALL,
            bg=BG_CARD,
            fg=TEXT_LIGHT,
            justify=tk.LEFT,
            wraplength=380
        ).pack(anchor="w", pady=(0, 16))

        CyberButton(
            diag_inner,
            text="About / Ethical Hacking Credentials",
            command=self.show_about_info,
            bg="#203454",
            hover_bg="#2c4773",
            fg=CYAN_ACCENT,
            font=FONT_SMALL,
            pady=7
        ).pack(fill=tk.X)

    # ------------------------------------------------
    # File Inspection Helper
    # ------------------------------------------------
    def update_selected_file_details(self, file_path):
        if not file_path or not os.path.isfile(file_path):
            return

        file_name = os.path.basename(file_path)
        file_size_bytes = os.path.getsize(file_path)

        if file_size_bytes < 1024:
            size_str = f"{file_size_bytes} Bytes"
        elif file_size_bytes < 1024 * 1024:
            size_str = f"{file_size_bytes / 1024:.2f} KB ({file_size_bytes:,} bytes)"
        else:
            size_str = f"{file_size_bytes / (1024 * 1024):.2f} MB ({file_size_bytes:,} bytes)"

        _, ext = os.path.splitext(file_path)
        ext_str = f"{ext.upper()} Document/File" if ext else "Standard File"

        computed_hash = compute_md5(file_path) or "Error calculating hash"

        self.selected_file_info = {
            "name": file_name,
            "path": file_path,
            "size": size_str,
            "type": ext_str,
            "hash": computed_hash,
        }

        # Update Browse view labels
        if hasattr(self, "browse_labels"):
            self.browse_labels["name"].configure(text=file_name)
            self.browse_labels["path"].configure(text=file_path)
            self.browse_labels["size"].configure(text=size_str)
            self.browse_labels["type"].configure(text=ext_str)
            self.browse_labels["hash"].configure(text=computed_hash)

        # Update Store view labels
        if hasattr(self, "store_meta_labels"):
            self.store_meta_labels["file"].configure(text=file_name)
            self.store_meta_labels["size"].configure(text=size_str)
            self.store_meta_labels["location"].configure(text=file_path)
            self.store_meta_labels["hash"].configure(text=computed_hash)

    def copy_current_hash_to_clipboard(self):
        curr_hash = self.selected_file_info.get("hash", "")
        if curr_hash and curr_hash != "-":
            self.root.clipboard_clear()
            self.root.clipboard_append(curr_hash)
            self.notification.show(f"Copied MD5 hash to clipboard: {curr_hash}", msg_type="info")
        else:
            self.notification.show("No hash available to copy. Select a file first.", msg_type="warning")

    # ------------------------------------------------
    # Browse File (Preserved API)
    # ------------------------------------------------
    def browse_file(self):
        path = filedialog.askopenfilename()
        if path:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, path)
            self.file_path_var.set(path)
            self.update_selected_file_details(path)
            self.notification.show(f"Loaded file: {os.path.basename(path)}", msg_type="info")

    # ------------------------------------------------
    # Browse Scheduled File (Preserved API)
    # ------------------------------------------------
    def browse_scheduled_file(self):
        path = filedialog.askopenfilename()
        if path:
            self.sched_file_entry.delete(0, tk.END)
            self.sched_file_entry.insert(0, path)
            self.sched_file_path_var.set(path)

    # ------------------------------------------------
    # Store Hash (Preserved API & MySQL logic)
    # ------------------------------------------------
    def store_file_hash(self):
        file_path = self.file_entry.get().strip()

        if not file_path:
            self.notification.show("Please select a file to store.", msg_type="error")
            messagebox.showerror("Error", "Please select a file.")
            return

        if not os.path.isfile(file_path):
            self.notification.show("Selected file does not exist on disk.", msg_type="error")
            messagebox.showerror("Error", "Selected file does not exist.")
            return

        file_hash = compute_md5(file_path)
        if file_hash is None:
            self.notification.show("Unable to calculate file hash.", msg_type="error")
            messagebox.showerror("Error", "Unable to calculate file hash.")
            return

        file_name = os.path.basename(file_path)

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
                    (file_hash, file_name)
                )
                self.conn.commit()
                msg = f"Baseline hash successfully updated for '{file_name}'"
                self.notification.show(msg, msg_type="success")
                messagebox.showinfo("Updated", f"Hash updated for {file_name}")
            else:
                self.cursor.execute(
                    """
                    INSERT INTO file_hashes
                    (file_name, file_hash)
                    VALUES (%s, %s)
                    """,
                    (file_name, file_hash)
                )
                self.conn.commit()
                msg = f"Baseline hash successfully stored for '{file_name}'"
                self.notification.show(msg, msg_type="success")
                messagebox.showinfo("Stored", f"Hash stored for {file_name}")

            if hasattr(self, "store_status_card"):
                self.store_status_card.configure(
                    text=f"✓ Last Action: Hash registered for {file_name} at {datetime.now().strftime('%H:%M:%S')}",
                    fg=GREEN_SAFE
                )

            # Refresh table and stat cards
            self.refresh_database_records()

        except Exception as error:
            self.notification.show(f"Database Error: {error}", msg_type="error")
            messagebox.showerror("Database Error", str(error))

    # ------------------------------------------------
    # Check Integrity (Preserved API & MySQL logic)
    # ------------------------------------------------
    def check_file_integrity(self):
        file_path = self.file_entry.get().strip()

        if not file_path:
            self.notification.show("Please select a file to check.", msg_type="error")
            messagebox.showerror("Error", "Please select a file.")
            return

        if not os.path.isfile(file_path):
            self.notification.show("Target file does not exist on disk.", msg_type="error")
            messagebox.showerror("Error", "File does not exist.")
            return

        current_hash = compute_md5(file_path)
        if current_hash is None:
            return

        file_name = os.path.basename(file_path)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.session_checks += 1

        try:
            self.cursor.execute(
                """
                SELECT file_hash
                FROM file_hashes
                WHERE file_name = %s
                """,
                (file_name,)
            )
            stored_hash_row = self.cursor.fetchone()

            if stored_hash_row:
                stored_hash = stored_hash_row[0]

                if current_hash == stored_hash:
                    self.session_verified += 1
                    status_str = "SAFE / VERIFIED"

                    # Update Result Display Card
                    self._update_result_card(
                        status="SAFE",
                        title="FILE INTEGRITY VERIFIED",
                        desc="Cryptographic MD5 checksum matches the stored forensic baseline. File is untampered.",
                        file_name=file_name,
                        orig_hash=stored_hash,
                        curr_hash=current_hash,
                        time_str=now_str,
                        diff_str="MATCH (No modifications detected)"
                    )

                    self.audit_history.append({
                        "file": file_name,
                        "orig": stored_hash,
                        "curr": current_hash,
                        "status": "VERIFIED",
                        "time": now_str
                    })

                    self.notification.show(f"✓ File integrity verified: '{file_name}' has NOT been modified.", msg_type="success")
                    messagebox.showinfo(
                        "Integrity OK",
                        "File integrity verified.\n\n"
                        "The file has NOT been modified."
                    )

                else:
                    self.session_modified += 1
                    status_str = "MODIFIED / TAMPERED"

                    # Update Result Display Card
                    self._update_result_card(
                        status="MODIFIED",
                        title="FILE INTEGRITY VIOLATION",
                        desc="CRITICAL ALERT: File has been MODIFIED or TAMPERED with! Cryptographic hash does not match baseline.",
                        file_name=file_name,
                        orig_hash=stored_hash,
                        curr_hash=current_hash,
                        time_str=now_str,
                        diff_str="MISMATCH (Unauthorized alteration detected)"
                    )

                    self.audit_history.append({
                        "file": file_name,
                        "orig": stored_hash,
                        "curr": current_hash,
                        "status": "MODIFIED",
                        "time": now_str
                    })

                    self.notification.show(f"⚠ CRITICAL ALERT: '{file_name}' has been MODIFIED!", msg_type="error")
                    messagebox.showwarning(
                        "Integrity Alert",
                        "File has been MODIFIED!"
                    )

            else:
                status_str = "NOT REGISTERED"
                self._update_result_card(
                    status="MISSING",
                    title="BASELINE RECORD NOT FOUND",
                    desc=f"'{file_name}' is not registered in the database. Please store the hash first.",
                    file_name=file_name,
                    orig_hash="NOT FOUND",
                    curr_hash=current_hash,
                    time_str=now_str,
                    diff_str="No baseline registered"
                )

                self.notification.show(f"No stored baseline hash found for '{file_name}'.", msg_type="warning")
                messagebox.showerror(
                    "Missing",
                    "File not found in database.\n"
                    "Please store the hash first."
                )

            # Update Stat Cards & Refresh Table
            self.refresh_database_records()

        except Exception as error:
            self.notification.show(f"Database Error: {error}", msg_type="error")
            messagebox.showerror("Database Error", str(error))

    def _update_result_card(self, status, title, desc, file_name, orig_hash, curr_hash, time_str, diff_str):
        if not hasattr(self, "result_inner"):
            return

        if status == "SAFE":
            icon_char = "🟢"
            border_c = GREEN_SAFE
            bg_c = "#092419"
            fg_c = "#4ade80"
        elif status == "MODIFIED":
            icon_char = "🔴"
            border_c = RED_ALERT
            bg_c = "#290d12"
            fg_c = "#f87171"
        else:
            icon_char = "🟠"
            border_c = ORANGE_WARN
            bg_c = "#261705"
            fg_c = "#fbbf24"

        self.result_container.configure(bg=border_c)
        self.result_inner.configure(bg=bg_c)
        self.compare_frame.configure(bg=bg_c)

        self.res_icon_lbl.configure(text=icon_char, bg=bg_c, fg=fg_c)
        self.res_title_lbl.configure(text=title, bg=bg_c, fg=fg_c)
        self.res_desc_lbl.configure(text=desc, bg=bg_c, fg=TEXT_WHITE)

        for w in self.compare_frame.winfo_children():
            w.configure(bg=bg_c)

        self.res_fields["file"].configure(text=file_name)
        self.res_fields["orig_hash"].configure(text=orig_hash)
        self.res_fields["curr_hash"].configure(text=curr_hash)
        self.res_fields["check_time"].configure(text=time_str)
        self.res_fields["diff"].configure(text=diff_str, fg=fg_c)

    # ------------------------------------------------
    # Scheduled Integrity Check (Preserved API & multithreading)
    # ------------------------------------------------
    def schedule_integrity_check(self):
        file_path = self.sched_file_entry.get().strip()
        interval = self.interval_entry.get().strip()

        if not file_path:
            self.notification.show("Please select a file for scheduled checks.", msg_type="error")
            messagebox.showerror("Input Error", "Please select a file.")
            return

        if not os.path.isfile(file_path):
            self.notification.show("Selected file does not exist.", msg_type="error")
            messagebox.showerror("Input Error", "Selected file does not exist.")
            return

        if not interval.isdigit():
            self.notification.show("Enter a valid numerical interval.", msg_type="error")
            messagebox.showerror("Input Error", "Enter a valid interval.")
            return

        interval_minutes = int(interval)
        if interval_minutes <= 0:
            self.notification.show("Interval must be greater than 0.", msg_type="error")
            messagebox.showerror("Input Error", "Interval must be greater than 0.")
            return

        interval_seconds = interval_minutes * 60
        file_name = os.path.basename(file_path)

        self.scheduler_running = True
        self.scheduled_target = file_name
        if hasattr(self, "sched_status_lbl"):
            self.sched_status_lbl.configure(
                text=f"🟢 Active: Monitoring '{file_name}' every {interval_minutes} minute(s).",
                fg=GREEN_SAFE
            )

        self.notification.show(
            f"Periodic checks started for {file_name} every {interval_minutes} min.",
            msg_type="info"
        )

        messagebox.showinfo(
            "Scheduled Check",
            f"Periodic checks started for:\n\n{file_name}\n\nEvery {interval_minutes} minute(s)."
        )

        def periodic_check():
            while self.scheduler_running:
                time.sleep(interval_seconds)
                if not self.scheduler_running:
                    break

                if not os.path.isfile(file_path):
                    self.root.after(
                        0,
                        lambda: messagebox.showerror(
                            "Error",
                            f"{file_name} no longer exists."
                        )
                    )
                    break

                current_hash = compute_md5(file_path)
                if current_hash is None:
                    break

                try:
                    # Query using dedicated cursor
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
                        if current_hash != stored_hash[0]:
                            self.root.after(
                                0,
                                lambda: [
                                    self.notification.show(f"⚠ TAMPER ALERT: {file_name} has been MODIFIED!", msg_type="error"),
                                    messagebox.showwarning("Integrity Alert", f"{file_name} has been MODIFIED!")
                                ]
                            )
                        else:
                            self.root.after(
                                0,
                                lambda: self.notification.show(f"✓ Scheduled Check: {file_name} is verified unmodified.", msg_type="success")
                            )
                    else:
                        self.root.after(
                            0,
                            lambda: messagebox.showerror(
                                "Error",
                                f"No stored hash found for {file_name}."
                            )
                        )

                except Exception as error:
                    print(f"Scheduled check error: {error}")
                    break

        thread = threading.Thread(target=periodic_check, daemon=True)
        thread.start()

    # ------------------------------------------------
    # Database Table Operations
    # ------------------------------------------------
    def refresh_database_records(self):
        try:
            self.cursor.execute(
                """
                SELECT id, file_name, file_hash
                FROM file_hashes
                ORDER BY id DESC
                """
            )
            rows = self.cursor.fetchall()
            total_count = len(rows)

            # Update Stat Cards
            if hasattr(self, "stat_cards"):
                self.stat_cards["total_files"].configure(text=str(total_count))
                self.stat_cards["verified_files"].configure(text=str(self.session_verified))
                self.stat_cards["modified_files"].configure(text=str(self.session_modified))
                self.stat_cards["total_checks"].configure(text=str(self.session_checks))

            self.all_db_rows = rows
            self.filter_dashboard_table()

        except Exception as err:
            print("Refresh DB error:", err)

    def filter_dashboard_table(self):
        query = self.table_search_var.get().strip().lower() if hasattr(self, "table_search_var") else ""

        # Clear existing items
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)

        rows = getattr(self, "all_db_rows", [])
        for row_id, file_name, file_hash in rows:
            if query and query not in file_name.lower() and query not in file_hash.lower():
                continue

            # Determine check status from session history
            matched_history = [h for h in self.audit_history if h["file"] == file_name]
            if matched_history:
                last_hist = matched_history[-1]
                if last_hist["status"] == "VERIFIED":
                    status_text = "🟢 SAFE / VERIFIED"
                else:
                    status_text = "🔴 TAMPERED"
                last_time = last_hist["time"]
            else:
                status_text = "⚪ STORED"
                last_time = "Baseline"

            self.file_tree.insert(
                "",
                tk.END,
                iid=str(row_id),
                values=(file_name, file_hash, status_text, last_time)
            )

    def check_selected_table_file(self):
        selected = self.file_tree.selection()
        if not selected:
            self.notification.show("Please select a file row from the table.", msg_type="warning")
            return

        item = self.file_tree.item(selected[0])
        file_name = item["values"][0]

        # Check if current path matches
        curr_path = self.file_entry.get().strip()
        if curr_path and os.path.basename(curr_path) == file_name and os.path.isfile(curr_path):
            self.switch_nav("check")
            self.check_file_integrity()
        else:
            # Ask user to locate file on disk
            messagebox.showinfo("Locate File", f"Please locate '{file_name}' on disk to verify its current hash.")
            path = filedialog.askopenfilename(initialfile=file_name)
            if path:
                self.file_entry.delete(0, tk.END)
                self.file_entry.insert(0, path)
                self.file_path_var.set(path)
                self.update_selected_file_details(path)
                self.switch_nav("check")
                self.check_file_integrity()

    def view_selected_file_details(self):
        selected = self.file_tree.selection()
        if not selected:
            self.notification.show("Please select a file to view details.", msg_type="warning")
            return

        item = self.file_tree.item(selected[0])
        file_name, file_hash, status, last_time = item["values"]

        # Detail Modal Dialog
        dlg = tk.Toplevel(self.root)
        dlg.title(f"Forensic Record: {file_name}")
        dlg.geometry("540x360")
        dlg.resizable(False, False)
        dlg.configure(bg=BG_DARK)
        center_window(dlg, 540, 360)
        dlg.transient(self.root)
        dlg.grab_set()

        card = tk.Frame(dlg, bg=BORDER_SUBTLE, padx=1, pady=1)
        card.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        inner = tk.Frame(card, bg=BG_CARD, padx=20, pady=16)
        inner.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            inner,
            text=f"📋 FORENSIC FILE DETAILS",
            font=FONT_TITLE,
            bg=BG_CARD,
            fg=TEXT_WHITE
        ).pack(anchor="w", pady=(0, 12))

        grid = tk.Frame(inner, bg=BG_CARD)
        grid.pack(fill=tk.X, pady=(0, 16))

        for r, (l, v) in enumerate([
            ("File Name:", file_name),
            ("Baseline MD5 Hash:", file_hash),
            ("Integrity Status:", status),
            ("Last Audit Time:", last_time),
            ("Security Standard:", "MD5 Hashing (RFC 1321)"),
            ("Database Status:", "Active in `file_hashes`"),
        ]):
            tk.Label(grid, text=l, font=FONT_BODY_BOLD, bg=BG_CARD, fg=TEXT_MUTED).grid(row=r, column=0, sticky="w", pady=4)
            tk.Label(grid, text=v, font=FONT_CODE_BOLD if "Hash" in l else FONT_BODY, bg=BG_CARD, fg=CYAN_ACCENT if "Hash" in l else TEXT_WHITE).grid(row=r, column=1, sticky="w", pady=4, padx=(10, 0))

        CyberButton(
            inner,
            text="Close Details",
            command=dlg.destroy,
            bg=BLUE_PRIMARY,
            hover_bg=BLUE_HOVER,
            pady=6
        ).pack(fill=tk.X)

    def delete_selected_file_hash(self):
        selected = self.file_tree.selection()
        if not selected:
            self.notification.show("Please select a file to delete.", msg_type="warning")
            return

        item = self.file_tree.item(selected[0])
        file_name = item["values"][0]

        confirm = messagebox.askyesno(
            "Confirm Baseline Deletion",
            f"Are you sure you want to remove the baseline hash for:\n\n{file_name}?\n\nThis cannot be undone."
        )

        if confirm:
            try:
                self.cursor.execute(
                    "DELETE FROM file_hashes WHERE file_name = %s",
                    (file_name,)
                )
                self.conn.commit()
                self.notification.show(f"Deleted baseline record for '{file_name}'.", msg_type="info")
                self.refresh_database_records()
            except Exception as e:
                self.notification.show(f"Database error deleting record: {e}", msg_type="error")

    # ------------------------------------------------
    # Reports View Table & Export
    # ------------------------------------------------
    def refresh_reports_table(self):
        self.filter_reports_table()

    def filter_reports_table(self):
        for item in self.reports_tree.get_children():
            self.reports_tree.delete(item)

        filter_mode = self.report_filter_var.get()

        for hist in self.audit_history:
            if filter_mode != "ALL" and hist["status"] != filter_mode:
                continue

            status_display = "🟢 VERIFIED" if hist["status"] == "VERIFIED" else "🔴 MODIFIED"
            self.reports_tree.insert(
                "",
                tk.END,
                values=(hist["file"], hist["orig"], hist["curr"], status_display, hist["time"])
            )

    def export_audit_report(self):
        if not self.audit_history:
            self.notification.show("No audit history records available to export.", msg_type="warning")
            return

        export_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Report", "*.txt"), ("CSV File", "*.csv"), ("All Files", "*.*")],
            initialfile=f"file_integrity_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )

        if not export_path:
            return

        try:
            with open(export_path, "w", encoding="utf-8") as f:
                f.write("=" * 70 + "\n")
                f.write("FILE INTEGRITY CHECKER - DIGITAL FORENSICS AUDIT REPORT\n")
                f.write("=" * 70 + "\n")
                f.write(f"Generated On: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Lead Analyst: {self.username}\n")
                f.write(f"Total Audits Performed: {len(self.audit_history)}\n")
                f.write(f"Verified Safe Files: {self.session_verified}\n")
                f.write(f"Tamper Violations: {self.session_modified}\n")
                f.write("=" * 70 + "\n\n")

                f.write(f"{'Target File':<25} {'Status':<15} {'Timestamp':<20}\n")
                f.write("-" * 70 + "\n")
                for h in self.audit_history:
                    f.write(f"{h['file']:<25} {h['status']:<15} {h['time']:<20}\n")
                    f.write(f"  Baseline: {h['orig']}\n")
                    f.write(f"  Computed: {h['curr']}\n\n")

                f.write("=" * 70 + "\n")
                f.write("END OF AUDIT REPORT\n")

            self.notification.show(f"Audit report saved to: {os.path.basename(export_path)}", msg_type="success")
            messagebox.showinfo("Report Exported", f"Forensics report successfully saved to:\n\n{export_path}")
        except Exception as err:
            self.notification.show(f"Export Error: {err}", msg_type="error")

    # ------------------------------------------------
    # About / Ethical Hacking (Preserved API)
    # ------------------------------------------------
    def show_about_info(self):
        messagebox.showinfo(
            "Ethical Hacking & Forensics",
            "File Integrity Checker\n\n"
            "• Detects unauthorized file tampering & modifications\n"
            "• Uses cryptographic MD5 file hashing (RFC 1321)\n"
            "• Stores forensic baseline hashes in MySQL\n"
            "• Performs automated scheduled integrity audits\n"
            "• Built for Digital Forensics and Incident Response\n\n"
            "Built by:\n"
            "• Viraj Jadhav\n"
            "• Pawar Neha\n"
            "• Bhosale Shivneri"
        )

    # ------------------------------------------------
    # Logout & Close Application (Preserved API)
    # ------------------------------------------------
    def logout(self):
        confirm = messagebox.askyesno("Confirm Sign Out", "Are you sure you want to log out of the forensics dashboard?")
        if confirm:
            self.on_close()
            from auth.login import login_window
            login_window()

    def on_close(self):
        self.scheduler_running = False
        try:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
        except Exception:
            pass
        self.root.destroy()


if __name__ == "__main__":
    FileIntegrityChecker()