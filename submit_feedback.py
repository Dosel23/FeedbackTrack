
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import os
from datetime import datetime

# Firebase connection. Keep firebase_config.py and serviceAccountKey.json
# in the same folder as this file.
try:
    from firebase_config import db
    FIREBASE_IMPORT_ERROR = None
except Exception:
    db = None
    FIREBASE_IMPORT_ERROR = True

# ============================================================
# FeedbackTrack - Submit Feedback Page
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
PURPLE_LIGHT = "#EEEDFF"

# ============================================================
# CONSISTENT SIDEBAR AND CATEGORY FONT SIZES
# ============================================================
SIDEBAR_FONT_SIZE = 10
SIDEBAR_ICON_SIZE = 10
CATEGORY_TITLE_FONT_SIZE = 11
CATEGORY_FONT_SIZE = 10


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
        font=("Segoe UI", 11, "bold"),
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
        self.config(width=width, height=height)
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
class SubmitFeedbackApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # ====================================================
        # WINDOW
        # ====================================================
        self.title("FeedbackTrack - Submit Feedback")
        self.geometry("1200x780")
        self.minsize(850, 620)

        self.configure(bg=BACKGROUND)
        self.resizable(True, True)
        self.child_process = None
        self.resize_job = None

        # Keep track of the About window and its application.
        self.about_window = None
        self.about_app = None

        # Preserve the authenticated student's Firebase UID.
        # Read it from the command line first, then the environment.
        self.user_uid = (
            sys.argv[1].strip()
            if len(sys.argv) > 1 and sys.argv[1].strip()
            else os.environ.get(
                "FEEDBACKTRACK_STUDENT_UID", ""
            ).strip()
        )

        if not self.user_uid:
            self.user_uid = None

        self.validation_active = False

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

        sidebar_content = tk.Frame(sidebar, bg=LEFT_BACKGROUND)
        sidebar_content.pack(fill="x", padx=14, pady=22)
        self.sidebar_content = sidebar_content

        # ====================================================
        # SUBMIT FEEDBACK
        # ====================================================
        submit_menu = tk.Frame(sidebar_content, bg=PURPLE)
        submit_menu.pack(fill="x", pady=(0, 10))

        tk.Label(
            submit_menu,
            text="🖊",
            font=("Segoe UI Emoji", SIDEBAR_ICON_SIZE),
            fg=WHITE,
            bg=PURPLE
        ).pack(side="left", padx=(12, 6), pady=9)

        tk.Label(
            submit_menu,
            text="Submit Feedback",
            font=("Segoe UI", SIDEBAR_FONT_SIZE),
            fg=WHITE,
            bg=PURPLE
        ).pack(side="left", pady=9)

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

        feedback_menu.bind(
            "<Button-1>",
            lambda event: self.on_my_feedback()
        )
        feedback_icon.bind(
            "<Button-1>",
            lambda event: self.on_my_feedback()
        )
        feedback_label.bind(
            "<Button-1>",
            lambda event: self.on_my_feedback()
        )

        # ====================================================
        # MY ACCOUNT
        # ====================================================
        account_menu = tk.Frame(sidebar_content, bg=LEFT_BACKGROUND)
        account_menu.pack(fill="x", pady=(0, 8))

        account_icon = tk.Label(
            account_menu,
            text="👤",
            font=("Segoe UI Emoji", SIDEBAR_ICON_SIZE),
            fg=TEXT_LIGHT,
            bg=LEFT_BACKGROUND,
            cursor="hand2"
        )
        account_icon.pack(side="left", padx=(8, 5))

        account_label = tk.Label(
            account_menu,
            text="My Account",
            font=("Segoe UI", SIDEBAR_FONT_SIZE),
            fg=TEXT_LIGHT,
            bg=LEFT_BACKGROUND,
            cursor="hand2"
        )
        account_label.pack(side="left")

        for widget in (account_menu, account_icon, account_label):
            widget.bind(
                "<Button-1>",
                lambda event: self.on_my_account()
            )

        # ====================================================
        # LOGOUT
        # ====================================================
        logout_menu = tk.Frame(
            sidebar_content,
            bg=LEFT_BACKGROUND,
            cursor="hand2"
        )
        logout_menu.pack(fill="x")

        logout_icon = tk.Label(
            logout_menu,
            text="↪",
            font=("Segoe UI Emoji", SIDEBAR_ICON_SIZE),
            fg=TEXT_LIGHT,
            bg=LEFT_BACKGROUND,
            cursor="hand2"
        )
        logout_icon.pack(side="left", padx=(12, 7), pady=10)

        logout_label = tk.Label(
            logout_menu,
            text="Logout",
            font=("Segoe UI", SIDEBAR_FONT_SIZE),
            fg=TEXT_LIGHT,
            bg=LEFT_BACKGROUND,
            cursor="hand2"
        )
        logout_label.pack(side="left", pady=10)

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

        content = tk.Frame(main_area, bg=WHITE)
        content.pack(fill="both", expand=True, padx=34, pady=32)
        self.content = content

        # ====================================================
        # TITLE
        # ====================================================
        self.page_title = tk.Label(
            content,
            text="Submit Your Feedback",
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
            text="Your feedback helps us improve. Be honest, be kind.",
            font=("Segoe UI", 11),
            fg=TEXT_LIGHT,
            bg=WHITE
        )
        self.subtitle.pack(anchor="nw", pady=(4, 24))

        # ====================================================
        # FORM + CATEGORY PANEL
        # ====================================================
        body = tk.Frame(content, bg=WHITE)
        body.pack(fill="both", expand=True)
        self.body = body

        # ====================================================
        # LEFT FORM AREA
        # ====================================================
        form_area = tk.Frame(body, bg=WHITE)
        form_area.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, 28)
        )
        self.form_area = form_area

        # ====================================================
        # CATEGORY REFERENCE PANEL
        # ====================================================
        category_panel = tk.Frame(
            body,
            bg=PURPLE_LIGHT,
            width=240,
            height=296
        )
        category_panel.pack(side="right", anchor="n")
        category_panel.pack_propagate(False)
        self.category_panel = category_panel

        # ====================================================
        # YOUR NAME LABEL
        # ====================================================
        name_label_frame = tk.Frame(form_area, bg=WHITE)
        name_label_frame.pack(anchor="w", fill="x")

        tk.Label(
            name_label_frame,
            text="Your Name",
            font=("Segoe UI", 11, "bold"),
            fg=TEXT,
            bg=WHITE
        ).pack(side="left")

        tk.Label(
            name_label_frame,
            text=" (Optional)",
            font=("Segoe UI", 9),
            fg=TEXT_LIGHT,
            bg=WHITE
        ).pack(side="left")

        # ====================================================
        # YOUR NAME BOX
        # ====================================================
        name_box = tk.Frame(
            form_area,
            bg=WHITE,
            highlightthickness=1,
            highlightbackground=BORDER,
            height=43
        )
        name_box.pack(fill="x", pady=(6, 17))
        name_box.pack_propagate(False)

        tk.Label(
            name_box,
            text="👤",
            font=("Segoe UI Emoji", 11),
            fg="#332E48",
            bg=WHITE
        ).pack(side="left", padx=(8, 4))

        self.name_entry = tk.Entry(
            name_box,
            font=("Segoe UI", 11),
            bd=0,
            relief="flat",
            bg=WHITE,
            fg=TEXT_LIGHT,
            insertbackground=TEXT
        )
        self.name_entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 8)
        )
        self.name_entry.insert(0, "Enter your name")
        self.name_entry.bind(
            "<FocusIn>",
            lambda event: self.clear_placeholder(
                self.name_entry,
                "Enter your name"
            )
        )

        # ====================================================
        # CATEGORY LABEL
        # ====================================================
        tk.Label(
            form_area,
            text="Category",
            font=("Segoe UI", 11, "bold"),
            fg=TEXT,
            bg=WHITE
        ).pack(anchor="w", pady=(0, 6))

        # ====================================================
        # CATEGORY DROPDOWN
        # ====================================================
        self.category_var = tk.StringVar()
        self.category_var.set("Select category")

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Feedback.TCombobox",
            fieldbackground=WHITE,
            background=WHITE,
            foreground=TEXT,
            bordercolor=BORDER,
            lightcolor=BORDER,
            darkcolor=BORDER,
            padding=8,
            font=("Segoe UI", 11)
        )

        self.category_dropdown = ttk.Combobox(
            form_area,
            textvariable=self.category_var,
            values=["Academic", "Food", "Hostel", "Library", "Other"],
            state="readonly",
            style="Feedback.TCombobox"
        )
        self.category_dropdown.pack(fill="x", ipady=3)
        self.category_dropdown.bind(
            "<<ComboboxSelected>>",
            self.on_form_change
        )

        # ====================================================
        # CATEGORY VALIDATION MESSAGE
        # ====================================================
        self.category_validation_label = tk.Label(
            form_area,
            text="",
            font=("Segoe UI", 9),
            fg="#D93025",
            bg=WHITE,
            wraplength=400,
            justify="left",
            anchor="w"
        )
        self.category_validation_label.pack(
            anchor="w",
            fill="x",
            pady=(4, 12)
        )

        # ====================================================
        # YOUR FEEDBACK LABEL
        # ====================================================
        tk.Label(
            form_area,
            text="Your Feedback",
            font=("Segoe UI", 11, "bold"),
            fg=TEXT,
            bg=WHITE
        ).pack(anchor="w", pady=(0, 6))

        # ====================================================
        # FEEDBACK TEXT BOX
        # ====================================================
        feedback_box = tk.Frame(
            form_area,
            bg=WHITE,
            highlightthickness=1,
            highlightbackground=BORDER
        )
        feedback_box.pack(fill="x")

        self.feedback_text = tk.Text(
            feedback_box,
            height=5,
            font=("Segoe UI", 11),
            bd=0,
            relief="flat",
            bg=WHITE,
            fg=TEXT_LIGHT,
            insertbackground=TEXT,
            wrap="word",
            padx=10,
            pady=9
        )
        self.feedback_text.pack(fill="both", expand=True)

        self.feedback_placeholder = "Write your feedback here..."
        self.feedback_text.insert("1.0", self.feedback_placeholder)
        self.feedback_text.bind(
            "<FocusIn>",
            self.clear_feedback_placeholder
        )
        self.feedback_text.bind(
            "<FocusOut>",
            self.restore_feedback_placeholder
        )
        self.feedback_text.bind(
            "<KeyRelease>",
            self.on_form_change
        )

        # ====================================================
        # FEEDBACK VALIDATION MESSAGE
        # ====================================================
        self.feedback_validation_label = tk.Label(
            form_area,
            text="",
            font=("Segoe UI", 9),
            fg="#D93025",
            bg=WHITE,
            wraplength=400,
            justify="left",
            anchor="w"
        )
        self.feedback_validation_label.pack(
            anchor="w",
            fill="x",
            pady=(5, 0)
        )

        # ====================================================
        # BUTTON AREA
        # ====================================================
        button_area = tk.Frame(form_area, bg=WHITE)
        button_area.pack(anchor="w", pady=(18, 0))
        self.button_area = button_area

        # ====================================================
        # SUBMIT BUTTON
        # ====================================================
        self.submit_button = RoundedButton(
            button_area,
            text="Submit Feedback",
            width=155,
            height=40,
            radius=11,
            bg_color=PURPLE,
            fg_color=WHITE,
            font=("Segoe UI", 11, "bold"),
            command=self.submit_feedback
        )
        self.submit_button.pack(side="left", padx=(0, 10))

        # ====================================================
        # CLEAR BUTTON
        # ====================================================
        clear_button = RoundedButton(
            button_area,
            text="Clear",
            width=73,
            height=40,
            radius=11,
            bg_color=WHITE,
            fg_color=TEXT_LIGHT,
            font=("Segoe UI", 11),
            border_color=BORDER,
            border_width=1,
            command=self.clear_form
        )
        clear_button.pack(side="left")
        self.clear_button = clear_button

        # ====================================================
        # FEEDBACK CATEGORIES PANEL
        # ====================================================
        category_content = tk.Frame(category_panel, bg=PURPLE_LIGHT)
        category_content.pack(
            fill="both",
            expand=True,
            padx=12,
            pady=18
        )
        self.category_content = category_content

        # ====================================================
        # PANEL TITLE
        # ====================================================
        self.category_title = tk.Label(
            category_content,
            text="Feedback Categories",
            font=("Segoe UI", CATEGORY_TITLE_FONT_SIZE, "bold"),
            fg=TEXT,
            bg=PURPLE_LIGHT
        )
        self.category_title.pack(anchor="w", padx=5, pady=(0, 2))

        # ====================================================
        # FEEDBACK CATEGORIES
        # ====================================================
        categories = [
            ("Academic", "🎓"),
            ("Food", "🍽"),
            ("Hostel", "🏠"),
            ("Library", "📚"),
            ("Other", "⭐")
        ]
        self.category_labels = []

        for name, emoji in categories:
            category = tk.Label(
                category_content,
                text=f"{emoji} {name}",
                font=("Segoe UI", CATEGORY_FONT_SIZE, "bold"),
                fg=TEXT_LIGHT,
                bg="#EEEDFF",
                padx=9,
                pady=4,
                anchor="w",
                justify="left"
            )
            category.pack(
                fill="x",
                padx=5,
                pady=2,
                anchor="w"
            )
            self.category_labels.append(category)

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
        about.bind("<Button-1>", lambda event: self.on_about())

        # ====================================================
        # RESPONSIVE LAYOUT
        # ====================================================
        self.bind("<Configure>", self.schedule_responsive_layout)
        self.after_idle(self.update_responsive_layout)

        self.check_form()

        self.protocol("WM_DELETE_WINDOW", self.close_application)

    # ========================================================
    # SCHEDULE RESPONSIVE LAYOUT
    # ========================================================
    def schedule_responsive_layout(self, event=None):
        if event is not None and event.widget is not self:
            return

        if self.resize_job is not None:
            try:
                self.after_cancel(self.resize_job)
            except tk.TclError:
                pass

        self.resize_job = self.after(60, self.update_responsive_layout)

    # ========================================================
    # UPDATE RESPONSIVE LAYOUT
    # ========================================================
    def update_responsive_layout(self):
        self.resize_job = None

        if not self.winfo_exists():
            return

        window_width = self.winfo_width()
        window_height = self.winfo_height()

        if window_width < 850:
            navbar_padding = 20
            logo_font_size = 16
        else:
            navbar_padding = 30
            logo_font_size = 19

        self.navbar.pack_configure(padx=navbar_padding)
        self.logo_text.config(font=("Segoe UI", logo_font_size, "bold"))
        self.logo_icon.config(font=("Segoe UI Emoji", logo_font_size))

        outer_padding = 16 if window_width < 850 else 30
        self.card_outer.pack_configure(padx=outer_padding)

        if window_width < 950:
            sidebar_width = 190
            sidebar_content_padding = 10
        else:
            sidebar_width = 220
            sidebar_content_padding = 14

        self.sidebar.config(width=sidebar_width)
        self.sidebar_content.pack_configure(padx=sidebar_content_padding)

        for widget in self.sidebar_content.winfo_children():
            for child in widget.winfo_children():
                if isinstance(child, tk.Label):
                    if child.cget("text") in (
                        "Submit Feedback", "My Feedback",
                        "My Account", "Logout"
                    ):
                        child.config(font=("Segoe UI", SIDEBAR_FONT_SIZE))
                    elif child.cget("text") in ("🖊", "📁", "👤", "↪"):
                        child.config(
                            font=("Segoe UI Emoji", SIDEBAR_ICON_SIZE)
                        )

        content_padding_x = 18 if window_width < 950 else 34

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

        if window_width < 950:
            title_font_size = 18
            subtitle_gap = 14
        else:
            title_font_size = 21
            subtitle_gap = 24

        self.page_title.config(font=("Segoe UI", title_font_size, "bold"))
        self.subtitle.pack_configure(pady=(4, subtitle_gap))

        if window_width < 950:
            category_width = 200
            category_gap = 16
            category_content_padding_x = 8
        else:
            category_width = 240
            category_gap = 28
            category_content_padding_x = 12

        if window_height < 700:
            category_height = 260
            category_content_padding_y = 10
        else:
            category_height = 296
            category_content_padding_y = 18

        self.category_panel.config(
            width=category_width,
            height=category_height
        )
        self.category_panel.pack_configure(side="right", anchor="n")
        self.form_area.pack_configure(padx=(0, category_gap))
        self.category_content.pack_configure(
            padx=category_content_padding_x,
            pady=category_content_padding_y
        )

        self.category_title.config(
            font=("Segoe UI", CATEGORY_TITLE_FONT_SIZE, "bold")
        )

        for category in self.category_labels:
            category.config(font=("Segoe UI", CATEGORY_FONT_SIZE, "bold"))

        if window_width < 950:
            name_box_padding = (6, 12)
            dropdown_padding = (0, 12)
            button_padding = (12, 0)
        else:
            name_box_padding = (6, 17)
            dropdown_padding = (0, 17)
            button_padding = (18, 0)

        for widget in self.form_area.winfo_children():
            if isinstance(widget, tk.Frame) and widget.winfo_height() > 0:
                children = widget.winfo_children()
                if any(isinstance(child, tk.Entry) for child in children):
                    widget.pack_configure(pady=name_box_padding)

        self.category_dropdown.pack_configure(pady=(0, 0))
        self.category_validation_label.pack_configure(
            pady=(4, dropdown_padding[1])
        )
        self.feedback_validation_label.pack_configure(pady=(5, 0))
        self.button_area.pack_configure(pady=button_padding)

        if window_width < 950:
            category_label_padx = 7
            category_label_pady = 3
        else:
            category_label_padx = 9
            category_label_pady = 4

        for category in self.category_labels:
            category.config(
                padx=category_label_padx,
                pady=category_label_pady
            )

        footer_font_size = 8 if window_width < 950 else 9
        self.footer_text.config(font=("Segoe UI", footer_font_size))

        form_width = max(150, self.form_area.winfo_width())
        self.category_validation_label.config(wraplength=form_width)
        self.feedback_validation_label.config(wraplength=form_width)

    # ========================================================
    # CLEAR ENTRY PLACEHOLDER
    # ========================================================
    def clear_placeholder(self, entry, default_text):
        if entry.get() == default_text:
            entry.delete(0, tk.END)
            entry.config(fg=TEXT)

    # ========================================================
    # CLEAR FEEDBACK PLACEHOLDER
    # ========================================================
    def clear_feedback_placeholder(self, event=None):
        current_text = self.feedback_text.get("1.0", tk.END).strip()

        if current_text == self.feedback_placeholder:
            self.feedback_text.delete("1.0", tk.END)
            self.feedback_text.config(fg=TEXT)

    # ========================================================
    # RESTORE FEEDBACK PLACEHOLDER
    # ========================================================
    def restore_feedback_placeholder(self, event=None):
        current_text = self.feedback_text.get("1.0", tk.END).strip()

        if current_text == "":
            self.feedback_text.insert("1.0", self.feedback_placeholder)
            self.feedback_text.config(fg=TEXT_LIGHT)

        if self.validation_active:
            self.update_validation()

    # ========================================================
    # GET CURRENT VALIDATION ERRORS
    # ========================================================
    def get_validation_errors(self):
        errors = {}

        category = self.category_var.get()
        feedback = self.feedback_text.get("1.0", tk.END).strip()

        if category == "Select category":
            errors["category"] = "Please select a feedback category."

        if feedback == self.feedback_placeholder:
            feedback = ""

        if len(feedback) < 10:
            errors["feedback"] = (
                "Please enter at least 10 characters of feedback."
            )

        return errors

    # ========================================================
    # UPDATE INLINE VALIDATION
    # ========================================================
    def update_validation(self):
        errors = self.get_validation_errors()

        self.category_validation_label.config(
            text=errors.get("category", "")
        )
        self.feedback_validation_label.config(
            text=errors.get("feedback", "")
        )

    # ========================================================
    # FORM CHANGE
    # ========================================================
    def on_form_change(self, event=None):
        if self.validation_active:
            self.update_validation()

        self.check_form()

    # ========================================================
    # CLEAR VALIDATION
    # ========================================================
    def clear_validation(self):
        self.category_validation_label.config(text="")
        self.feedback_validation_label.config(text="")
        self.validation_active = False

    # ========================================================
    # CHECK FORM
    # ========================================================
    def check_form(self):
        self.submit_button.bg_color = PURPLE
        self.submit_button.fg_color = WHITE
        self.submit_button.draw()

    # ========================================================
    # SUBMIT FEEDBACK
    # ========================================================
    def submit_feedback(self):
        category = self.category_var.get()
        name = self.name_entry.get()
        feedback = self.feedback_text.get("1.0", tk.END).strip()

        if feedback == self.feedback_placeholder:
            feedback = ""

        self.validation_active = True
        self.update_validation()

        errors = self.get_validation_errors()

        if errors:
            if "category" in errors:
                self.category_dropdown.focus_set()
            else:
                self.feedback_text.focus_set()
            return

        if name == "Enter your name" or not name.strip():
            name = "Anonymous"

        if db is None:
            messagebox.showerror(
                "Unable to Submit Feedback",
                "Your feedback could not be saved because the database connection "
                "is not available. Please contact the administrator or try again later."
            )
            return

        try:
            # The feedback must be linked to the logged-in student.
            if not self.user_uid:
                messagebox.showerror(
                    "Account Not Identified",
                    "Your logged-in account could not be identified.\n\n"
                    "Please log in again before submitting feedback."
                )
                return

            submission_time = datetime.now()

            db.collection("feedback").add({
                "name": name.strip(),
                "category": category,
                "feedback": feedback,
                "status": "New",
                "date": submission_time.strftime("%d %b %Y %I:%M %p"),
                "created_at": submission_time,

                # Store the owner's UID even for anonymous feedback.
                "user_uid": self.user_uid
            })

        except Exception as error:
            print("Feedback save error:", repr(error))
            messagebox.showerror(
                "Unable to Submit Feedback",
                "We couldn't save your feedback right now. Please check your internet "
                "connection and try again. If the problem continues, contact the administrator."
            )
            return

        self.clear_validation()

        messagebox.showinfo(
            "Feedback Submitted",
            "Thank you! Your feedback has been saved successfully.\n\n"
            f"Category: {category}\n"
            f"Name: {name}"
        )

        self.clear_form()

    # ========================================================
    # CLEAR FORM
    # ========================================================
    def clear_form(self):
        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, "Enter your name")
        self.name_entry.config(fg=TEXT_LIGHT)

        self.category_var.set("Select category")

        self.feedback_text.delete("1.0", tk.END)
        self.feedback_text.insert("1.0", self.feedback_placeholder)
        self.feedback_text.config(fg=TEXT_LIGHT)

        self.clear_validation()
        self.check_form()

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
    # MY ACCOUNT
    # ========================================================
    def on_my_account(self):
        self.open_page("my_account.py")

    # ========================================================
    # MY FEEDBACK
    # ========================================================
    def on_my_feedback(self):
        self.open_page("my_feedback.py")

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
        # If About is already open, bring it to the front.
        if self.about_window is not None:
            try:
                if self.about_window.winfo_exists():
                    self.about_window.lift()
                    self.about_window.focus_force()
                    return
            except tk.TclError:
                pass

        self.about_window = None
        self.about_app = None

        try:
            # Import the About page class from about.py.
            from about import AboutPage

            # Create About as a child window of Submit Feedback.
            self.about_window = tk.Toplevel(self)

            # Keep the relationship between the two windows.
            self.about_window.transient(self)

            # Build the existing About page inside this Toplevel.
            self.about_app = AboutPage(self.about_window)

            # Show About above Submit Feedback.
            self.about_window.lift()
            self.about_window.focus_force()

            # Clear saved references when the About window is destroyed.
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
                f"Could not open the About page.\n\n{error}"
            )

    # ========================================================
    # CLEAN UP ABOUT WINDOW REFERENCES
    # ========================================================
    def on_about_destroy(self, event=None):
        # Only clear the references when the About Toplevel is destroyed.
        if (
            event is not None
            and self.about_window is not None
            and event.widget is self.about_window
        ):
            self.about_window = None
            self.about_app = None

    # ========================================================
    # OPEN ANOTHER PAGE
    # Other pages continue using the original subprocess method.
    # ========================================================
    def open_page(self, filename):
        if self.child_process is not None:
            if self.child_process.poll() is None:
                return
            self.child_process = None

        current_folder = os.path.dirname(
            os.path.abspath(__file__)
        )

        page_path = os.path.join(current_folder, filename)

        if not os.path.isfile(page_path):
            messagebox.showerror(
                "Page Not Found",
                f"{filename} was not found.\n\n"
                "Please keep submit_feedback.py, "
                "my_feedback.py, my_account.py, homepage.py, "
                "signup.py, and about.py "
                "in the same folder."
            )
            return

        try:
            command = [sys.executable, page_path]

            # Do not pass the student's UID to pages that
            # should not receive it.
            if (
                self.user_uid
                and filename not in (
                    "homepage.py",
                    "signup.py",
                    "about.py"
                )
            ):
                command.append(self.user_uid)

            self.child_process = subprocess.Popen(
                command,
                cwd=current_folder
            )

            # Preserve the existing navigation for other pages.
            self.withdraw()

            self.check_child_process()

        except (OSError, tk.TclError) as error:
            self.child_process = None

            self.deiconify()
            self.lift()
            self.focus_force()

            messagebox.showerror(
                "Navigation Error",
                f"Could not open {filename}.\n\n{error}"
            )

    # ========================================================
    # CHECK CHILD PROCESS
    # ========================================================
    def check_child_process(self):
        try:
            if not self.winfo_exists():
                return

            if self.child_process is None:
                return

            if self.child_process.poll() is not None:
                self.child_process = None

                # Restore the main page after the child page closes.
                self.deiconify()
                self.lift()
                self.focus_force()

                self.after_idle(self.update_responsive_layout)

            else:
                self.after(200, self.check_child_process)

        except tk.TclError:
            pass

    # ========================================================
    # CLOSE APPLICATION
    # ========================================================
    def close_application(self):
        if self.resize_job is not None:
            try:
                self.after_cancel(self.resize_job)
            except tk.TclError:
                pass

        # Close About before destroying the main application.
        if self.about_window is not None:
            try:
                if self.about_window.winfo_exists():
                    self.about_window.destroy()
            except tk.TclError:
                pass

        self.about_window = None
        self.about_app = None

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
    app = SubmitFeedbackApp()
    app.mainloop()
