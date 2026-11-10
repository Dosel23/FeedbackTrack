import tkinter as tk
from tkinter import messagebox
import subprocess
import sys
import os
import re
import requests

# Firebase profile database and Authentication REST API.
try:
    from firebase_config import db, set_session
    try:
        from firebase_admin import auth as firebase_auth
    except Exception:
        firebase_auth = None
    FIRESTORE_IMPORT_ERROR = None
except Exception as firebase_import_error:
    db = None
    firebase_auth = None
    FIRESTORE_IMPORT_ERROR = firebase_import_error

FIREBASE_API_KEY = "AIzaSyBd1KHyHiU9OfPu1BoH3H3KORtUJrOZbmg"
FIREBASE_SIGNIN_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
FIREBASE_UPDATE_URL = "https://identitytoolkit.googleapis.com/v1/accounts:update"


# ============================================================
# FeedbackTrack - My Account Page
# ============================================================
# RESPONSIVE DESIGN:
# - Matches submit_feedback.py window size (1200x780).
# - Keeps the same minimum window size (850x620).
# - Adjusts the navigation bar, sidebar, and content spacing.
# - Matches the Logout icon, font, spacing, and padding.
# - Keeps the original account form and functionality.
# ============================================================


# ============================================================
# COLORS
# ============================================================

BACKGROUND = "#F3F2FC"
WHITE = "#FFFFFF"

LEFT_BACKGROUND = "#FAFAFE"
ICON_BACKGROUND = "#EFEFFD"

PURPLE = "#6C63FF"
PURPLE_DARK = "#5750D9"

TEXT = "#1E1B2E"
TEXT_LIGHT = "#6B6880"

BORDER = "#E0DCFB"
CARD_BORDER = "#E2E0F0"

# Same sidebar font sizes as submit_feedback.py.
SIDEBAR_FONT_SIZE = 10
SIDEBAR_ICON_SIZE = 10


# ============================================================
# ROUNDED BUTTON
# ============================================================

class RoundedButton(tk.Canvas):

    def __init__(
        self,
        parent,
        text="",
        width=120,
        height=38,
        radius=12,
        bg_color=PURPLE,
        fg_color=WHITE,
        font=("Segoe UI", 10, "bold"),
        command=None,
        border_color=None,
        border_width=1
    ):

        super().__init__(
            parent,
            width=width,
            height=height,
            bg=parent["bg"],
            highlightthickness=0,
            bd=0
        )

        self.command = command
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.border_color = border_color
        self.border_width = border_width

        self.radius = radius
        self.text = text
        self.font = font

        self.width = width
        self.height = height

        self.draw()

        self.bind("<Button-1>", lambda event: self.on_click())
        self.bind("<Enter>", lambda event: self.config(cursor="hand2"))
        self.bind("<Leave>", lambda event: self.config(cursor=""))

    # ========================================================
    # DRAW BUTTON
    # ========================================================

    def draw(self):

        self.delete("all")

        # Keep the rounded corners within the button dimensions.
        r = min(self.radius, self.width / 2, self.height / 2)

        w = self.width
        h = self.height

        if self.border_color:

            self.create_rounded_rectangle(
                0, 0, w, h, r,
                fill=self.border_color,
                outline=""
            )

            self.create_rounded_rectangle(
                self.border_width,
                self.border_width,
                w - self.border_width,
                h - self.border_width,
                max(1, r - self.border_width),
                fill=self.bg_color,
                outline=""
            )

        else:

            self.create_rounded_rectangle(
                0, 0, w, h, r,
                fill=self.bg_color,
                outline=""
            )

        self.create_text(
            w / 2,
            h / 2,
            text=self.text,
            fill=self.fg_color,
            font=self.font,
            anchor="center",
            justify="center"
        )

    # ========================================================
    # RESPONSIVE BUTTON SIZE
    # ========================================================

    def set_size(self, width, height):

        width = max(1, int(width))
        height = max(1, int(height))

        if self.width == width and self.height == height:
            return

        self.width = width
        self.height = height

        self.config(
            width=width,
            height=height
        )

        self.draw()

    # ========================================================
    # CREATE ROUNDED RECTANGLE
    # ========================================================

    def create_rounded_rectangle(
        self, x1, y1, x2, y2, radius, **kwargs
    ):

        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1
        ]

        return self.create_polygon(
            points,
            smooth=True,
            **kwargs
        )

    # ========================================================
    # BUTTON CLICK
    # ========================================================

    def on_click(self):

        if self.command:
            self.command()


# ============================================================
# MAIN APPLICATION
# ============================================================

class MyAccountApp(tk.Tk):

    def __init__(self):

        super().__init__()

        # ====================================================
        # WINDOW
        # ====================================================

        self.title("FeedbackTrack - My Account")
        self.geometry("1200x780")
        self.minsize(850, 620)
        self.configure(bg=BACKGROUND)
        self.resizable(True, True)

        self.child_process = None
        self.resize_job = None

        # Keep references to the About window so it opens above this page.
        self.about_window = None
        self.about_app = None

        # The login page passes the authenticated Firebase UID as argv[1].
        self.user_uid = sys.argv[1].strip() if len(sys.argv) > 1 else None
        self.profile_document = None
        self.profile_data = {}
        self.profile_email = None
        self.original_name = ""

        # Password placeholder text.
        self.current_password_placeholder = "Enter current password"
        self.new_password_placeholder = "Enter new password"
        self.confirm_password_placeholder = "Re-enter new password"

        # ====================================================
        # TOP NAVIGATION BAR
        # ====================================================

        navbar = tk.Frame(self, bg=BACKGROUND)
        navbar.pack(fill="x", padx=40, pady=(18, 8))

        self.navbar = navbar

        # ====================================================
        # FEEDBACKTRACK LOGO
        # ====================================================

        brand_frame = tk.Frame(navbar, bg=BACKGROUND)
        brand_frame.pack(side="left")

        self.brand_frame = brand_frame

        self.logo_icon = tk.Label(
            brand_frame,
            text="💬",
            font=("Segoe UI Emoji", 19),
            fg=TEXT,
            bg=BACKGROUND
        )
        self.logo_icon.pack(side="left", padx=(0, 8))

        self.logo_text = tk.Label(
            brand_frame,
            text="FeedbackTrack",
            font=("Segoe UI", 19, "bold"),
            fg=TEXT,
            bg=BACKGROUND
        )
        self.logo_text.pack(side="left")

        # ====================================================
        # MAIN CARD OUTER CONTAINER
        # ====================================================

        card_outer = tk.Frame(self, bg=BACKGROUND)
        card_outer.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=(8, 10)
        )

        self.card_outer = card_outer

        # ====================================================
        # MAIN WHITE CARD
        # ====================================================

        card = tk.Frame(
            card_outer,
            bg=WHITE,
            highlightthickness=1,
            highlightbackground=CARD_BORDER
        )
        card.pack(fill="both", expand=True)

        self.card = card

        # ====================================================
        # MAIN CARD GRID
        # ====================================================

        card.grid_columnconfigure(0, weight=0)
        card.grid_columnconfigure(1, weight=1)
        card.grid_rowconfigure(0, weight=1)

        # ====================================================
        # LEFT SIDEBAR
        # ====================================================

        sidebar = tk.Frame(
            card,
            bg=LEFT_BACKGROUND,
            width=220,
            highlightthickness=1,
            highlightbackground=CARD_BORDER
        )
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        self.sidebar = sidebar

        # ====================================================
        # SIDEBAR CONTENT
        # ====================================================

        sidebar_content = tk.Frame(
            sidebar,
            bg=LEFT_BACKGROUND
        )
        sidebar_content.pack(
            fill="x",
            padx=14,
            pady=22
        )

        self.sidebar_content = sidebar_content

        # ====================================================
        # SUBMIT FEEDBACK
        # ====================================================

        submit_menu = tk.Frame(
            sidebar_content,
            bg=LEFT_BACKGROUND,
            cursor="hand2"
        )
        submit_menu.pack(fill="x", pady=(0, 10))

        submit_icon = tk.Label(
            submit_menu,
            text="🖊",
            font=("Segoe UI Emoji", SIDEBAR_ICON_SIZE),
            fg=TEXT_LIGHT,
            bg=LEFT_BACKGROUND,
            cursor="hand2"
        )
        submit_icon.pack(side="left", padx=(12, 6), pady=9)

        submit_label = tk.Label(
            submit_menu,
            text="Submit Feedback",
            font=("Segoe UI", SIDEBAR_FONT_SIZE),
            fg=TEXT_LIGHT,
            bg=LEFT_BACKGROUND,
            cursor="hand2"
        )
        submit_label.pack(side="left", pady=9)

        for widget in (submit_menu, submit_icon, submit_label):
            widget.bind(
                "<Button-1>",
                lambda event: self.on_submit_feedback()
            )

        # ====================================================
        # MY FEEDBACK
        # ====================================================

        feedback_menu = tk.Frame(
            sidebar_content,
            bg=LEFT_BACKGROUND,
            cursor="hand2"
        )
        feedback_menu.pack(fill="x", pady=(0, 8))

        feedback_icon = tk.Label(
            feedback_menu,
            text="📁",
            font=("Segoe UI Emoji", SIDEBAR_ICON_SIZE),
            fg=TEXT_LIGHT,
            bg=LEFT_BACKGROUND,
            cursor="hand2"
        )
        feedback_icon.pack(side="left", padx=(12, 7))

        feedback_label = tk.Label(
            feedback_menu,
            text="My Feedback",
            font=("Segoe UI", SIDEBAR_FONT_SIZE),
            fg=TEXT_LIGHT,
            bg=LEFT_BACKGROUND,
            cursor="hand2"
        )
        feedback_label.pack(side="left")

        for widget in (feedback_menu, feedback_icon, feedback_label):
            widget.bind(
                "<Button-1>",
                lambda event: self.on_my_feedback()
            )

        # ====================================================
        # MY ACCOUNT - PURPLE HIGHLIGHT
        # ====================================================

        account_menu = tk.Frame(
            sidebar_content,
            bg=PURPLE,
            cursor="hand2"
        )
        account_menu.pack(fill="x", pady=(0, 8))

        account_icon = tk.Label(
            account_menu,
            text="👤",
            font=("Segoe UI Emoji", SIDEBAR_ICON_SIZE),
            fg=WHITE,
            bg=PURPLE,
            cursor="hand2"
        )
        account_icon.pack(side="left", padx=(12, 6), pady=9)

        account_label = tk.Label(
            account_menu,
            text="My Account",
            font=("Segoe UI", SIDEBAR_FONT_SIZE, "bold"),
            fg=WHITE,
            bg=PURPLE,
            cursor="hand2"
        )
        account_label.pack(side="left", pady=9)

        for widget in (account_menu, account_icon, account_label):
            widget.bind(
                "<Button-1>",
                lambda event: self.on_my_account()
            )

        # ====================================================
        # LOGOUT
        # Matches submit_feedback.py and view_feedback.py.
        # ====================================================

        logout_menu = tk.Frame(
            sidebar_content,
            bg=LEFT_BACKGROUND,
            cursor="hand2"
        )
        logout_menu.pack(fill="x")

        # Same arrow icon, font, and spacing as Submit Feedback.
        logout_icon = tk.Label(
            logout_menu,
            text="↪",
            font=("Segoe UI Emoji", SIDEBAR_ICON_SIZE),
            fg=TEXT_LIGHT,
            bg=LEFT_BACKGROUND,
            cursor="hand2"
        )
        logout_icon.pack(
            side="left",
            padx=(12, 7),
            pady=10
        )

        logout_label = tk.Label(
            logout_menu,
            text="Logout",
            font=("Segoe UI", SIDEBAR_FONT_SIZE),
            fg=TEXT_LIGHT,
            bg=LEFT_BACKGROUND,
            cursor="hand2"
        )
        logout_label.pack(side="left", pady=10)

        # Make the icon, text, and entire row clickable.
        for widget in (logout_menu, logout_icon, logout_label):
            widget.bind(
                "<Button-1>",
                lambda event: self.on_logout()
            )

        # ====================================================
        # RIGHT MAIN AREA
        # ====================================================

        main_area = tk.Frame(card, bg=WHITE)
        main_area.grid(row=0, column=1, sticky="nsew")

        self.main_area = main_area

        # ====================================================
        # MAIN CONTENT
        # ====================================================

        content = tk.Frame(main_area, bg=WHITE)
        content.pack(
            fill="both",
            expand=True,
            padx=34,
            pady=32
        )

        self.content = content

        # ====================================================
        # PAGE TITLE
        # ====================================================

        self.page_title = tk.Label(
            content,
            text="My Account",
            font=("Segoe UI", 21, "bold"),
            fg=TEXT,
            bg=WHITE
        )
        self.page_title.pack(anchor="nw")

        # ====================================================
        # SUBTITLE
        # ====================================================

        self.subtitle = tk.Label(
            content,
            text="Update your name or change your password.",
            font=("Segoe UI", 12),
            fg=TEXT_LIGHT,
            bg=WHITE
        )
        self.subtitle.pack(anchor="nw", pady=(4, 24))

        # ====================================================
        # ACCOUNT FORM CARD
        # ====================================================

        form_card = tk.Frame(
            content,
            bg=WHITE,
            highlightthickness=0
        )
        form_card.pack(anchor="nw")

        self.form_card = form_card

        # ====================================================
        # FULL NAME LABEL
        # ====================================================

        tk.Label(
            form_card,
            text="Full Name",
            font=("Segoe UI", 10, "bold"),
            fg=TEXT,
            bg=WHITE
        ).pack(anchor="w", pady=(0, 4))

        # ====================================================
        # FULL NAME BOX
        # ====================================================

        name_box = tk.Frame(
            form_card,
            bg=WHITE,
            highlightthickness=1,
            highlightbackground=BORDER,
            width=290,
            height=42
        )
        name_box.pack_propagate(False)
        name_box.pack(anchor="w", pady=(0, 9))

        tk.Label(
            name_box,
            text="👤",
            font=("Segoe UI Emoji", 10),
            fg="#332E48",
            bg=WHITE
        ).pack(side="left", padx=(8, 5))

        self.name_entry = tk.Entry(
            name_box,
            font=("Segoe UI", 11),
            bd=0,
            relief="flat",
            bg=WHITE,
            fg=TEXT,
            insertbackground=TEXT
        )
        self.name_entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 8)
        )
        # Filled from the logged-in student profile in Firestore.
        self.name_entry.insert(0, "")

        # ====================================================
        # USERNAME / CAMPUS ID LABEL
        # ====================================================

        tk.Label(
            form_card,
            text="Username / Campus ID",
            font=("Segoe UI", 10, "bold"),
            fg=TEXT,
            bg=WHITE
        ).pack(anchor="w", pady=(0, 4))

        # ====================================================
        # USERNAME / CAMPUS ID BOX
        # ====================================================

        username_box = tk.Frame(
            form_card,
            bg="#F2F0FB",
            highlightthickness=1,
            highlightbackground=BORDER,
            width=290,
            height=42
        )
        username_box.pack_propagate(False)
        username_box.pack(anchor="w", pady=(0, 12))

        tk.Label(
            username_box,
            text="👤",
            font=("Segoe UI Emoji", 10),
            fg="#77738D",
            bg="#F2F0FB"
        ).pack(side="left", padx=(8, 5))

        self.username_entry = tk.Entry(
            username_box,
            font=("Segoe UI", 11),
            bd=0,
            relief="flat",
            bg="#F2F0FB",
            fg=TEXT_LIGHT,
            insertbackground=TEXT
        )
        self.username_entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 8)
        )
        # Loaded from the logged-in student profile in Firestore.
        self.username_entry.insert(0, "")

        # ====================================================
        # DIVIDER
        # ====================================================

        divider = tk.Frame(
            form_card,
            bg=BORDER,
            width=290,
            height=1
        )
        divider.pack(anchor="w", pady=(0, 14))

        # ====================================================
        # CHANGE PASSWORD TITLE
        # ====================================================

        tk.Label(
            form_card,
            text="CHANGE PASSWORD",
            font=("Segoe UI", 9, "bold"),
            fg=TEXT_LIGHT,
            bg=WHITE
        ).pack(anchor="w", pady=(0, 10))

        # ====================================================
        # CURRENT PASSWORD
        # ====================================================

        tk.Label(
            form_card,
            text="Current Password",
            font=("Segoe UI", 10, "bold"),
            fg=TEXT,
            bg=WHITE
        ).pack(anchor="w", pady=(0, 4))

        current_password_box = tk.Frame(
            form_card,
            bg=WHITE,
            highlightthickness=1,
            highlightbackground=BORDER,
            width=290,
            height=42
        )
        current_password_box.pack_propagate(False)
        current_password_box.pack(anchor="w", pady=(0, 9))

        tk.Label(
            current_password_box,
            text="🔒",
            font=("Segoe UI Emoji", 10),
            fg="#77738D",
            bg=WHITE
        ).pack(side="left", padx=(8, 5))

        self.current_password_entry = tk.Entry(
            current_password_box,
            font=("Segoe UI", 11),
            bd=0,
            relief="flat",
            bg=WHITE,
            fg=TEXT_LIGHT,
            insertbackground=TEXT
        )
        self.current_password_entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 8)
        )

        self.add_password_visibility_toggle(
            self.current_password_entry, current_password_box, self.current_password_placeholder
        )

        self.current_password_entry.insert(
            0,
            self.current_password_placeholder
        )

        self.current_password_error = tk.Label(
            form_card,
            text="",
            font=("Segoe UI", 11),
            fg="#D93025",
            bg=WHITE,
            wraplength=290,
            justify="left"
        )
        self.current_password_error.pack(anchor="w", pady=(0, 5))

        self.current_password_entry.bind(
            "<KeyRelease>",
            lambda event: self.validate_password_fields()
        )

        self.current_password_entry.bind(
            "<FocusIn>",
            lambda event: self.clear_password_placeholder(
                self.current_password_entry,
                self.current_password_placeholder
            )
        )
        self.current_password_entry.bind(
            "<FocusOut>",
            lambda event: self.restore_password_placeholder(
                self.current_password_entry,
                self.current_password_placeholder
            )
        )

        # ====================================================
        # NEW PASSWORD
        # ====================================================

        tk.Label(
            form_card,
            text="New Password",
            font=("Segoe UI", 10, "bold"),
            fg=TEXT,
            bg=WHITE
        ).pack(anchor="w", pady=(0, 4))

        new_password_box = tk.Frame(
            form_card,
            bg=WHITE,
            highlightthickness=1,
            highlightbackground=BORDER,
            width=290,
            height=42
        )
        new_password_box.pack_propagate(False)
        new_password_box.pack(anchor="w", pady=(0, 9))

        tk.Label(
            new_password_box,
            text="🔒",
            font=("Segoe UI Emoji", 10),
            fg="#77738D",
            bg=WHITE
        ).pack(side="left", padx=(8, 5))

        self.new_password_entry = tk.Entry(
            new_password_box,
            font=("Segoe UI", 11),
            bd=0,
            relief="flat",
            bg=WHITE,
            fg=TEXT_LIGHT,
            insertbackground=TEXT
        )
        self.new_password_entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 8)
        )

        self.add_password_visibility_toggle(
            self.new_password_entry, new_password_box, self.new_password_placeholder
        )

        self.new_password_entry.insert(
            0,
            self.new_password_placeholder
        )

        self.new_password_error = tk.Label(
            form_card,
            text="",
            font=("Segoe UI", 11),
            fg="#D93025",
            bg=WHITE,
            wraplength=290,
            justify="left"
        )
        self.new_password_error.pack(anchor="w", pady=(0, 5))

        self.new_password_entry.bind(
            "<KeyRelease>",
            lambda event: self.validate_password_fields()
        )

        self.new_password_entry.bind(
            "<FocusIn>",
            lambda event: self.clear_password_placeholder(
                self.new_password_entry,
                self.new_password_placeholder
            )
        )
        self.new_password_entry.bind(
            "<FocusOut>",
            lambda event: self.restore_password_placeholder(
                self.new_password_entry,
                self.new_password_placeholder
            )
        )

        # ====================================================
        # CONFIRM NEW PASSWORD
        # ====================================================

        tk.Label(
            form_card,
            text="Confirm New Password",
            font=("Segoe UI", 10, "bold"),
            fg=TEXT,
            bg=WHITE
        ).pack(anchor="w", pady=(0, 4))

        confirm_password_box = tk.Frame(
            form_card,
            bg=WHITE,
            highlightthickness=1,
            highlightbackground=BORDER,
            width=290,
            height=42
        )
        confirm_password_box.pack_propagate(False)
        confirm_password_box.pack(anchor="w", pady=(0, 12))

        tk.Label(
            confirm_password_box,
            text="🔒",
            font=("Segoe UI Emoji", 10),
            fg="#77738D",
            bg=WHITE
        ).pack(side="left", padx=(8, 5))

        self.confirm_password_entry = tk.Entry(
            confirm_password_box,
            font=("Segoe UI", 11),
            bd=0,
            relief="flat",
            bg=WHITE,
            fg=TEXT_LIGHT,
            insertbackground=TEXT
        )
        self.confirm_password_entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 8)
        )

        self.add_password_visibility_toggle(
            self.confirm_password_entry, confirm_password_box, self.confirm_password_placeholder
        )

        self.confirm_password_entry.insert(
            0,
            self.confirm_password_placeholder
        )

        self.confirm_password_error = tk.Label(
            form_card,
            text="",
            font=("Segoe UI", 11),
            fg="#D93025",
            bg=WHITE,
            wraplength=290,
            justify="left"
        )
        self.confirm_password_error.pack(anchor="w", pady=(0, 5))

        self.confirm_password_entry.bind(
            "<KeyRelease>",
            lambda event: self.validate_password_fields()
        )

        self.confirm_password_entry.bind(
            "<FocusIn>",
            lambda event: self.clear_password_placeholder(
                self.confirm_password_entry,
                self.confirm_password_placeholder
            )
        )
        self.confirm_password_entry.bind(
            "<FocusOut>",
            lambda event: self.restore_password_placeholder(
                self.confirm_password_entry,
                self.confirm_password_placeholder
            )
        )

        # ====================================================
        # SAVE CHANGES / CANCEL
        # ====================================================

        button_area = tk.Frame(form_card, bg=WHITE)
        button_area.pack(anchor="w")

        self.button_area = button_area

        save_button = RoundedButton(
            button_area,
            text="Save Changes",
            width=125,
            height=40,
            radius=18,
            bg_color=PURPLE,
            fg_color=WHITE,
            font=("Segoe UI", 10, "bold"),
            command=self.save_changes
        )
        save_button.pack(side="left", padx=(0, 14))

        cancel_button = RoundedButton(
            button_area,
            text="Cancel",
            width=78,
            height=40,
            radius=18,
            bg_color=WHITE,
            fg_color=TEXT_LIGHT,
            font=("Segoe UI", 10),
            command=self.cancel_changes
        )
        cancel_button.pack(side="left")

        # ====================================================
        # FOOTER
        # ====================================================

        footer = tk.Frame(self, bg=BACKGROUND)
        footer.pack(side="bottom", pady=(0, 12))

        self.footer = footer

        self.footer_text = tk.Label(
            footer,
            text="© 2026 FeedbackTrack · Made for Student Voices   ",
            font=("Segoe UI", 10),
            fg="#8D8A9F",
            bg=BACKGROUND
        )
        self.footer_text.pack(side="left")

        about = tk.Label(
            footer,
            text="About",
            font=("Segoe UI", 10, "bold"),
            fg=PURPLE,
            bg=BACKGROUND,
            cursor="hand2"
        )
        about.pack(side="left")

        about.bind(
            "<Button-1>",
            lambda event: self.on_about()
        )

        # ====================================================
        # RESPONSIVE LAYOUT
        # ====================================================

        self.bind(
            "<Configure>",
            self.schedule_responsive_layout
        )

        self.after_idle(self.update_responsive_layout)

        # Load the real profile after the form widgets exist.
        self.after_idle(self.load_student_profile)

        # ====================================================
        # WINDOW CLOSE
        # ====================================================

        self.protocol(
            "WM_DELETE_WINDOW",
            self.close_application
        )

    # ========================================================
    # SCHEDULE RESPONSIVE LAYOUT
    # ========================================================

    def schedule_responsive_layout(self, event=None):

        # Only respond to changes in the main application window.
        if event is not None and event.widget is not self:
            return

        # Avoid running the resize function too frequently.
        if self.resize_job is not None:
            try:
                self.after_cancel(self.resize_job)
            except tk.TclError:
                pass

        self.resize_job = self.after(
            60,
            self.update_responsive_layout
        )

    # ========================================================
    # UPDATE RESPONSIVE LAYOUT
    # ========================================================

    def update_responsive_layout(self):

        self.resize_job = None

        if not self.winfo_exists():
            return

        window_width = self.winfo_width()
        window_height = self.winfo_height()

        # ----------------------------------------------------
        # 1. NAVIGATION BAR MARGINS AND LOGO
        # ----------------------------------------------------

        if window_width < 850:
            navbar_padding = 20
            logo_font_size = 16
        else:
            navbar_padding = 30
            logo_font_size = 19

        self.navbar.pack_configure(
            padx=navbar_padding
        )

        self.logo_text.config(
            font=("Segoe UI", logo_font_size, "bold")
        )

        self.logo_icon.config(
            font=("Segoe UI Emoji", logo_font_size)
        )

        # ----------------------------------------------------
        # 2. MAIN CARD OUTER MARGINS
        # ----------------------------------------------------

        if window_width < 850:
            outer_padding = 16
        else:
            outer_padding = 30

        self.card_outer.pack_configure(
            padx=outer_padding
        )

        # ----------------------------------------------------
        # 3. SIDEBAR WIDTH
        # ----------------------------------------------------

        if window_width < 950:
            sidebar_width = 190
            sidebar_content_padding = 10
        else:
            sidebar_width = 220
            sidebar_content_padding = 14

        self.sidebar.config(
            width=sidebar_width
        )

        self.sidebar_content.pack_configure(
            padx=sidebar_content_padding
        )

        # Keep sidebar labels and icons the same size as submit_feedback.py.
        for menu in self.sidebar_content.winfo_children():
            for child in menu.winfo_children():
                if isinstance(child, tk.Label):
                    if child.cget("text") in (
                        "Submit Feedback", "My Feedback", "My Account", "Logout"
                    ):
                        current_font = child.cget("font")
                        is_bold = "bold" in str(current_font).lower()
                        child.config(
                            font=("Segoe UI", SIDEBAR_FONT_SIZE, "bold")
                            if is_bold else ("Segoe UI", SIDEBAR_FONT_SIZE)
                        )
                    elif child.cget("text") in ("🖊", "📁", "👤", "↪"):
                        child.config(font=("Segoe UI Emoji", SIDEBAR_ICON_SIZE))

        # ----------------------------------------------------
        # 4. MAIN CONTENT SPACING
        # ----------------------------------------------------

        if window_width < 950:
            content_padding_x = 18
        else:
            content_padding_x = 34

        if window_height < 700:
            content_padding_y = 16
        elif window_width < 950:
            content_padding_y = 22
        else:
            content_padding_y = 32

        self.content.pack_configure(
            padx=content_padding_x,
            pady=content_padding_y
        )

        # ----------------------------------------------------
        # 5. PAGE TITLE AND SUBTITLE
        # ----------------------------------------------------

        if window_width < 950:
            title_font_size = 18
            subtitle_gap = 14
        else:
            title_font_size = 21
            subtitle_gap = 24

        self.page_title.config(
            font=("Segoe UI", title_font_size, "bold")
        )

        self.subtitle.config(font=("Segoe UI", 12))
        self.subtitle.pack_configure(
            pady=(4, subtitle_gap)
        )

        # ----------------------------------------------------
        # 6. FORM SPACING
        # ----------------------------------------------------

        if window_width < 850:
            field_gap = 6
        else:
            field_gap = 9

        # Adjust the vertical gaps around the fixed-width fields.
        for widget in self.form_card.winfo_children():

            if isinstance(widget, tk.Frame):

                children = widget.winfo_children()

                if any(
                    isinstance(child, tk.Entry)
                    for child in children
                ):

                    if widget is self.username_entry:
                        continue

                    widget.pack_configure(
                        pady=(0, field_gap)
                    )

        # ----------------------------------------------------
        # 7. FOOTER
        # ----------------------------------------------------

        if window_width < 950:
            footer_font_size = 8
        else:
            footer_font_size = 9

        self.footer_text.config(
            font=("Segoe UI", footer_font_size)
        )

    # ========================================================
    # PASSWORD VISIBILITY EYE TOGGLE (MATCHES ADMIN ACCOUNT)
    # ========================================================

    def add_password_visibility_toggle(self, entry, box, placeholder):

        entry.password_visible = False

        visibility_icon = tk.Canvas(
            box,
            width=27,
            height=26,
            bg=WHITE,
            highlightthickness=0,
            bd=0,
            cursor="hand2"
        )
        visibility_icon.pack(side="right", padx=(0, 5), pady=1)

        def draw_visibility_icon():
            visibility_icon.delete("all")
            visibility_icon.create_arc(
                3, 5, 24, 21,
                start=200,
                extent=140,
                style="arc",
                outline="#332E48",
                width=1.4
            )
            visibility_icon.create_arc(
                3, 5, 24, 21,
                start=20,
                extent=140,
                style="arc",
                outline="#332E48",
                width=1.4
            )
            visibility_icon.create_oval(
                10, 9, 17, 16,
                outline="#332E48",
                width=1.3
            )
            visibility_icon.create_oval(
                12, 11, 15, 14,
                fill="#332E48",
                outline="#332E48"
            )
            if not entry.password_visible:
                visibility_icon.create_line(
                    4, 22, 23, 3,
                    fill="#332E48",
                    width=1.5
                )

        def toggle_password_visibility(event=None):
            entry.password_visible = not entry.password_visible
            value = self.get_password_value(entry, placeholder)
            if not value:
                entry.config(show="")
            elif entry.password_visible:
                entry.config(show="")
            else:
                entry.config(show="•")
            draw_visibility_icon()

        visibility_icon.bind("<Button-1>", toggle_password_visibility)
        visibility_icon.bind(
            "<Enter>",
            lambda event: visibility_icon.config(cursor="hand2")
        )
        draw_visibility_icon()
        entry.visibility_icon_redraw = draw_visibility_icon

    # ========================================================
    # CLEAR PASSWORD PLACEHOLDER
    # ========================================================

    def clear_password_placeholder(self, entry, placeholder):

        if entry.get() == placeholder:
            entry.delete(0, tk.END)
            entry.config(
                fg=TEXT,
                show="" if getattr(entry, "password_visible", False) else "•"
            )

        self.validate_password_fields()

    # ========================================================
    # RESTORE PASSWORD PLACEHOLDER
    # ========================================================

    def restore_password_placeholder(self, entry, placeholder):

        if entry.get() == "":
            entry.config(
                fg=TEXT_LIGHT,
                show=""
            )
            entry.insert(0, placeholder)

        self.validate_password_fields()

    # ========================================================
    # GET PASSWORD WITHOUT PLACEHOLDER
    # ========================================================

    def get_password_value(self, entry, placeholder):

        value = entry.get()
        if value == placeholder:
            return ""
        return value

    # ========================================================
    # STRONG PASSWORD VALIDATION (SAME AS ADMIN ACCOUNT)
    # ========================================================

    def validate_strong_password(self, password):

        if len(password) < 8:
            return "Use at least 8 characters."
        if not re.search(r"[A-Z]", password):
            return "Include at least one uppercase letter (A-Z)."
        if not re.search(r"[a-z]", password):
            return "Include at least one lowercase letter (a-z)."
        if not re.search(r"[0-9]", password):
            return "Include at least one number (0-9)."
        if not re.search(r"[^A-Za-z0-9]", password):
            return "Include at least one special character, e.g. @ or #."
        return ""

    # ========================================================
    # LIVE PASSWORD INPUT VALIDATION (SAME AS ADMIN ACCOUNT)
    # ========================================================

    def validate_password_fields(self):

        current_password = self.get_password_value(
            self.current_password_entry, self.current_password_placeholder
        )
        new_password = self.get_password_value(
            self.new_password_entry, self.new_password_placeholder
        )
        confirm_password = self.get_password_value(
            self.confirm_password_entry, self.confirm_password_placeholder
        )

        if not current_password and (new_password or confirm_password):
            self.current_password_error.config(
                text="Enter your current password to change it."
            )
        else:
            self.current_password_error.config(text="")

        if new_password:
            self.new_password_error.config(
                text=self.validate_strong_password(new_password)
            )
        else:
            self.new_password_error.config(text="")

        if confirm_password:
            if not new_password:
                confirm_error = "Enter your new password first."
            elif confirm_password != new_password:
                confirm_error = "Passwords do not match."
            else:
                confirm_error = ""
            self.confirm_password_error.config(text=confirm_error)
        else:
            self.confirm_password_error.config(text="")

    # ========================================================
    # SAVE CHANGES
    # ========================================================

    def load_student_profile(self):
        """Load the signed-in student's profile from Firestore."""
        if db is None:
            messagebox.showerror(
                "Database Connection Error",
                "The student profile could not be loaded because Firestore is not available.\n\n"
                "Check firebase_config.py, serviceAccountKey.json, and firebase-admin.\n\n"
                f"Details: {FIRESTORE_IMPORT_ERROR}"
            )
            return

        if not self.user_uid:
            messagebox.showwarning(
                "Student Not Identified",
                "No logged-in student ID was received. Open My Account from the student login "
                "session so the correct profile can be loaded."
            )
            return

        try:
            # Prefer an explicit UID field, then a document whose ID is the UID.
            document = None
            # The profile document is named after the user's UID: read it first.
            candidate = db.collection("users").document(self.user_uid).get()
            if candidate.exists:
                document = candidate

            for field in (
                () if document is not None
                else ("uid", "user_uid", "firebase_uid", "auth_uid")
            ):
                matches = db.collection("users").where(field, "==", self.user_uid).limit(1).get()
                if matches:
                    document = matches[0]
                    break

            if document is None:
                candidate = db.collection("users").document(self.user_uid).get()
                if candidate.exists:
                    document = candidate

            # Existing signup implementations may store profiles without a UID field.
            # In that case, obtain the authenticated email from Firebase Admin and
            # locate the existing users document by its email.
            if document is None and firebase_auth is not None:
                try:
                    auth_user = firebase_auth.get_user(self.user_uid)
                    if auth_user.email:
                        matches = db.collection("users").where(
                            "email", "==", auth_user.email
                        ).limit(1).get()
                        if matches:
                            document = matches[0]
                except Exception as lookup_error:
                    print("Firebase UID/email lookup:", repr(lookup_error))

            if document is None:
                messagebox.showerror(
                    "Profile Not Found",
                    "Your Firebase login succeeded, but no matching student profile was found "
                    "in the Firestore 'users' collection. Check that the profile stores the "
                    "Firebase UID in a uid/auth_uid/firebase_uid field or uses it as its document ID."
                )
                return

            self.profile_document = document.reference
            self.profile_data = document.to_dict() or {}
            self.profile_email = self.profile_data.get("email")

            full_name = (
                self.profile_data.get("full_name")
                or self.profile_data.get("name")
                or self.profile_data.get("display_name")
                or ""
            )
            username = (
                self.profile_data.get("username")
                or self.profile_data.get("campus_id")
                or self.profile_data.get("student_id")
                or ""
            )

            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, str(full_name))
            self.original_name = str(full_name)

            self.username_entry.config(state="normal")
            self.username_entry.delete(0, tk.END)
            self.username_entry.insert(0, str(username))
            self.username_entry.config(state="readonly")

        except Exception as error:
            print("Student profile load error:", repr(error))
            messagebox.showerror(
                "Profile Load Failed",
                "Could not retrieve your account information from Firestore. Check your "
                "internet connection and Firebase configuration, then try again."
            )

    # ========================================================
    # SAVE CHANGES
    # ========================================================

    def save_changes(self):
        if db is None:
            messagebox.showerror("My Account", "Firestore is not available. Your changes were not saved.")
            return
        if not self.user_uid or self.profile_document is None:
            messagebox.showerror(
                "My Account",
                "Your student profile is not loaded. Please reopen this page from your logged-in account."
            )
            return

        new_name = self.name_entry.get().strip()
        if not new_name:
            messagebox.showwarning("My Account", "Please enter your full name.")
            self.name_entry.focus_set()
            return

        current_password = self.get_password_value(self.current_password_entry, self.current_password_placeholder)
        new_password = self.get_password_value(self.new_password_entry, self.new_password_placeholder)
        confirm_password = self.get_password_value(self.confirm_password_entry, self.confirm_password_placeholder)

        if new_password or confirm_password or current_password:
            if not current_password:
                messagebox.showwarning("My Account", "Please enter your current password.")
                self.current_password_entry.focus_set()
                return
            if not new_password:
                messagebox.showwarning("My Account", "Please enter your new password.")
                self.new_password_entry.focus_set()
                return
            if new_password != confirm_password:
                messagebox.showwarning("My Account", "New passwords do not match.")
                self.confirm_password_entry.focus_set()
                return
            password_error = self.validate_strong_password(new_password)
            if password_error:
                messagebox.showwarning(
                    "Weak Password",
                    "Your new password does not meet the requirements.\n\n"
                    + password_error
                )
                self.new_password_entry.focus_set()
                return
            if not self.profile_email:
                messagebox.showerror(
                    "Password Update Failed",
                    "Your profile does not have an email address. Password changes cannot be verified."
                )
                return

        try:
            updates = {}
            if "full_name" in self.profile_data:
                updates["full_name"] = new_name
            elif "name" in self.profile_data:
                updates["name"] = new_name
            elif "display_name" in self.profile_data:
                updates["display_name"] = new_name
            else:
                updates["full_name"] = new_name

            # Verify the current password with Firebase before changing it.
            if new_password:
                response = requests.post(
                    f"{FIREBASE_SIGNIN_URL}?key={FIREBASE_API_KEY}",
                    json={"email": self.profile_email, "password": current_password, "returnSecureToken": True},
                    timeout=20
                )
                result = response.json()
                if not response.ok:
                    messagebox.showerror(
                        "Password Update Failed",
                        "The current password is incorrect or Firebase could not verify it."
                    )
                    return

                token = result.get("idToken")
                if not token:
                    messagebox.showerror("Password Update Failed", "Firebase did not return a valid session token.")
                    return

                update_response = requests.post(
                    f"{FIREBASE_UPDATE_URL}?key={FIREBASE_API_KEY}",
                    json={"idToken": token, "password": new_password, "returnSecureToken": True},
                    timeout=20
                )
                if not update_response.ok:
                    try:
                        error_code = update_response.json().get("error", {}).get("message", "")
                    except ValueError:
                        error_code = ""
                    messagebox.showerror(
                        "Password Update Failed",
                        "Firebase could not update your password. "
                        + (f"Details: {error_code}" if error_code else "Please try again.")
                    )
                    return

            # A password change replaces the Firebase tokens: keep the session valid.
            if 'update_response' in locals():
                try:
                    set_session(update_response.json())
                except ValueError:
                    pass

            if new_name != self.original_name:
                self.profile_document.update(updates)
                self.profile_data.update(updates)
                self.original_name = new_name

            messagebox.showinfo("My Account", "Your account changes have been saved successfully.")
            self.cancel_changes()

        except requests.exceptions.RequestException as error:
            print("Firebase account update error:", repr(error))
            messagebox.showerror("My Account", "Could not connect to Firebase. Check your internet connection and try again.")
        except Exception as error:
            print("Account save error:", repr(error))
            messagebox.showerror("My Account", "Your account changes could not be saved. Please try again.")

    # ========================================================
    # CANCEL
    # ========================================================

    def cancel_changes(self):

        # Clear all password fields and restore their placeholders.
        for entry, placeholder in [
            (
                self.current_password_entry,
                self.current_password_placeholder
            ),
            (
                self.new_password_entry,
                self.new_password_placeholder
            ),
            (
                self.confirm_password_entry,
                self.confirm_password_placeholder
            )
        ]:

            entry.delete(0, tk.END)

            entry.config(
                fg=TEXT_LIGHT,
                show=""
            )

            entry.insert(0, placeholder)
            entry.password_visible = False
            redraw_icon = getattr(entry, "visibility_icon_redraw", None)
            if redraw_icon:
                redraw_icon()

        self.validate_password_fields()

    # ========================================================
    # SUBMIT FEEDBACK PAGE
    # ========================================================

    def on_submit_feedback(self):

        self.open_page("submit_feedback.py")

    # ========================================================
    # MY FEEDBACK PAGE
    # ========================================================

    def on_my_feedback(self):

        self.open_page("my_feedback.py")

    # ========================================================
    # MY ACCOUNT PAGE
    # ========================================================

    def on_my_account(self):

        # The user is already on the My Account page.
        self.lift()

    # ========================================================
    # LOGIN
    # ========================================================

    def on_login(self):

        self.open_page("homepage.py")

    # ========================================================
    # SIGN UP
    # ========================================================

    def on_signup(self):

        self.open_page("signup.py")

    # ========================================================
    # LOGOUT
    # ========================================================

    def on_logout(self):

        answer = messagebox.askyesno(
            "Logout",
            "Are you sure you want to logout?"
        )

        if not answer:
            return

        self.open_page("homepage.py")

    # ========================================================
    # ABOUT
    # ========================================================

    def on_about(self):

        # If About is already open, bring it above My Account.
        if self.about_window is not None:
            try:
                if self.about_window.winfo_exists():
                    self.about_window.lift()
                    self.about_window.attributes("-topmost", True)
                    self.about_window.focus_force()
                    return
            except tk.TclError:
                pass

        self.about_window = None
        self.about_app = None

        try:
            # Use the existing AboutPage inside a child window instead of
            # opening a separate process and hiding My Account.
            from about import AboutPage

            self.about_window = tk.Toplevel(self)
            self.about_window.transient(self)
            self.about_app = AboutPage(self.about_window)

            self.about_window.lift()
            self.about_window.attributes("-topmost", True)
            self.about_window.focus_force()

            self.about_window.bind(
                "<Destroy>",
                self.on_about_destroy,
                add="+"
            )

        except Exception as error:
            if self.about_window is not None:
                try:
                    if self.about_window.winfo_exists():
                        self.about_window.destroy()
                except tk.TclError:
                    pass

            self.about_window = None
            self.about_app = None

            messagebox.showerror(
                "About Page Error",
                f"Could not open the About page.\n\n{error}",
                parent=self
            )

    # ========================================================
    # CLEAN UP ABOUT WINDOW REFERENCES
    # ========================================================

    def on_about_destroy(self, event=None):

        # Clear references only when the About Toplevel is destroyed.
        if (
            event is not None
            and self.about_window is not None
            and event.widget is self.about_window
        ):
            self.about_window = None
            self.about_app = None

    # ========================================================
    # OPEN ANOTHER PAGE
    # ========================================================

    def open_page(self, filename):

        if self.child_process is not None:

            if self.child_process.poll() is None:
                return

            self.child_process = None

        current_folder = os.path.dirname(
            os.path.abspath(__file__)
        )

        page_path = os.path.join(
            current_folder,
            filename
        )

        if not os.path.isfile(page_path):

            messagebox.showerror(
                "Page Not Found",
                f"{filename} was not found.\n\n"
                "Please keep the FeedbackTrack pages "
                "in the same folder."
            )

            return

        try:

            command = [sys.executable, page_path]
            if self.user_uid and filename not in ("homepage.py", "signup.py"):
                command.append(self.user_uid)

            self.child_process = subprocess.Popen(
                command,
                cwd=current_folder
            )

            # Hide this page while the other page is open.
            self.withdraw()

            # Check when the other page closes.
            self.check_child_process()

        except OSError as error:

            self.child_process = None

            messagebox.showerror(
                "Navigation Error",
                f"Could not open {filename}.\n\n{error}"
            )

    # ========================================================
    # CHECK CHILD PROCESS
    # ========================================================

    def check_child_process(self):

        if not self.winfo_exists():
            return

        if self.child_process is None:
            return

        if self.child_process.poll() is not None:

            self.child_process = None

            # Show this page again.
            self.deiconify()
            self.lift()

            # Recalculate the layout after restoring the page.
            self.after_idle(self.update_responsive_layout)

        else:

            # Check again after 200 milliseconds.
            self.after(
                200,
                self.check_child_process
            )

    # ========================================================
    # CLOSE APPLICATION
    # ========================================================

    def close_application(self):

        # Cancel any pending resize update.
        if self.resize_job is not None:
            try:
                self.after_cancel(self.resize_job)
            except tk.TclError:
                pass

        # Close the About window before closing My Account.
        if self.about_window is not None:
            try:
                if self.about_window.winfo_exists():
                    self.about_window.destroy()
            except tk.TclError:
                pass

        self.about_window = None
        self.about_app = None

        # Close any child page that is still running.
        if self.child_process is not None:

            if self.child_process.poll() is None:

                try:
                    self.child_process.terminate()
                except OSError:
                    pass

        self.destroy()


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    app = MyAccountApp()
    app.mainloop()