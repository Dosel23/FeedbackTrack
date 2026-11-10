import tkinter as tk
import subprocess
import sys
import os
import requests

# Firebase Authentication Web API configuration.
FIREBASE_API_KEY = "AIzaSyBd1KHyHiU9OfPu1BoH3H3KORtUJrOZbmg"
FIREBASE_SIGNIN_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"

# Firestore profile database (same configuration used by signup.py).
try:
    from firebase_config import (
        db, lookup_username, set_session, clear_session
    )
    FIRESTORE_IMPORT_ERROR = None
except Exception as firebase_import_error:
    db = None
    FIRESTORE_IMPORT_ERROR = firebase_import_error


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


# ============================================================
# ROUNDED BUTTON
# ============================================================

class RoundedButton(tk.Canvas):

    def __init__(
        self,
        parent,
        text="",
        width=140,
        height=50,
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

        self.bind(
            "<Button-1>",
            lambda event: self.on_click()
        )

        self.bind(
            "<Enter>",
            lambda event: self.config(cursor="hand2")
        )

        self.bind(
            "<Leave>",
            lambda event: self.config(cursor="")
        )

    # Draw the rounded button using the current dimensions.
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

    # Allow the button dimensions to change when the window is resized.
    def set_size(self, width, height):

        width = max(1, int(width))
        height = max(1, int(height))

        if self.width == width and self.height == height:
            return

        self.width = width
        self.height = height

        self.config(
            width=self.width,
            height=self.height
        )

        self.draw()

    def create_rounded_rectangle(
        self,
        x1,
        y1,
        x2,
        y2,
        radius,
        **kwargs
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

    def on_click(self):

        if self.command:
            self.command()


# ============================================================
# MAIN APPLICATION
# ============================================================

class FeedbackTrackApp(tk.Tk):

    def __init__(self):

        super().__init__()

        # ====================================================
        # WINDOW
        # ====================================================

        self.title("FeedbackTrack - Login")

        # Start with a larger window and allow resizing.
        self.geometry("1200x780")
        self.minsize(850, 620)

        self.configure(bg=BACKGROUND)
        self.resizable(True, True)

        # Process used to open another page.
        self.child_process = None

        # About window references.
        self.about_window = None
        self.about_app = None

        # Forgot Password window process reference.
        self.forgot_password_process = None

        # Prevent unnecessary repeated responsive updates.
        self.resize_job = None

        # ====================================================
        # TOP NAVIGATION BAR
        # ====================================================

        navbar = tk.Frame(
            self,
            bg=BACKGROUND
        )

        navbar.pack(
            fill="x",
            padx=30,
            pady=(18, 8)
        )

        self.navbar = navbar

        # ====================================================
        # LOGO
        # ====================================================

        brand_frame = tk.Frame(
            navbar,
            bg=BACKGROUND
        )

        brand_frame.pack(side="left")

        logo_icon = tk.Label(
            brand_frame,
            text="💬",
            font=("Segoe UI Emoji", 19),
            fg=TEXT,
            bg=BACKGROUND
        )

        logo_icon.pack(
            side="left",
            padx=(0, 9)
        )

        logo_text = tk.Label(
            brand_frame,
            text="FeedbackTrack",
            font=("Segoe UI", 19, "bold"),
            fg=TEXT,
            bg=BACKGROUND
        )

        logo_text.pack(side="left")

        # ====================================================
        # MAIN CARD CONTAINER
        # ====================================================

        card_outer = tk.Frame(
            self,
            bg=BACKGROUND
        )

        card_outer.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=(8, 10)
        )

        self.card_outer = card_outer

        # ====================================================
        # MAIN CARD
        # ====================================================

        card = tk.Frame(
            card_outer,
            bg=WHITE,
            highlightthickness=1,
            highlightbackground=CARD_BORDER
        )

        card.pack(
            fill="both",
            expand=True
        )

        self.card = card

        # ====================================================
        # TWO-COLUMN GRID
        # ====================================================

        card.grid_columnconfigure(
            0,
            weight=1,
            uniform="columns"
        )

        card.grid_columnconfigure(
            1,
            weight=1,
            uniform="columns"
        )

        card.grid_rowconfigure(0, weight=1)

        # ====================================================
        # LEFT PANEL
        # ====================================================

        left_panel = tk.Frame(
            card,
            bg=LEFT_BACKGROUND
        )

        left_panel.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        self.left_panel = left_panel

        # ====================================================
        # LEFT CONTENT
        # ====================================================

        left_content = tk.Frame(
            left_panel,
            bg=LEFT_BACKGROUND
        )

        left_content.place(
            relx=0.5,
            rely=0.5,
            anchor="center"
        )

        self.left_content = left_content

        # ====================================================
        # LEFT ICON CIRCLE
        # ====================================================

        icon_canvas = tk.Canvas(
            left_content,
            width=84,
            height=84,
            bg=LEFT_BACKGROUND,
            highlightthickness=0,
            bd=0
        )

        icon_canvas.pack(pady=(0, 18))

        icon_canvas.create_oval(
            5, 5, 79, 79,
            fill=ICON_BACKGROUND,
            outline=""
        )

        icon_canvas.create_text(
            42, 42,
            text="💬",
            font=("Segoe UI Emoji", 27),
            fill=TEXT
        )

        # ====================================================
        # LEFT TITLE
        # ====================================================

        left_title = tk.Frame(
            left_content,
            bg=LEFT_BACKGROUND
        )

        left_title.pack()

        tk.Label(
            left_title,
            text="Your Voice ",
            font=("Segoe UI", 21, "bold"),
            fg=TEXT,
            bg=LEFT_BACKGROUND
        ).pack(side="left")

        tk.Label(
            left_title,
            text="Matters",
            font=("Segoe UI", 21, "bold"),
            fg=PURPLE,
            bg=LEFT_BACKGROUND
        ).pack(side="left")

        # ====================================================
        # LEFT DESCRIPTION
        # ====================================================

        description = tk.Label(
            left_content,
            text=(
                "Share your feedback and help us make our college\n"
                "a better place — and see exactly what happens\n"
                "after you submit it."
            ),
            font=("Segoe UI", 11),
            fg=TEXT_LIGHT,
            bg=LEFT_BACKGROUND,
            justify="center"
        )

        description.pack(pady=(17, 23))

        # ====================================================
        # CATEGORY SECTION
        # ====================================================

        category_frame = tk.Frame(
            left_content,
            bg=LEFT_BACKGROUND
        )

        category_frame.pack(pady=(3, 0))

        self.category_frame = category_frame

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
                category_frame,
                text=f"{emoji} {name}",
                font=("Segoe UI", 10),
                fg=TEXT_LIGHT,
                bg="#EEEDFF",
                padx=11,
                pady=6
            )

            self.category_labels.append(category)

        # ====================================================
        # RIGHT PANEL
        # ====================================================

        right_panel = tk.Frame(
            card,
            bg=WHITE
        )

        right_panel.grid(
            row=0,
            column=1,
            sticky="nsew"
        )

        self.right_panel = right_panel

        # ====================================================
        # RIGHT CONTENT
        # ====================================================

        right_content = tk.Frame(
            right_panel,
            bg=WHITE
        )

        right_content.place(
            relx=0.5,
            rely=0.5,
            anchor="center"
        )

        self.right_content = right_content

        # ====================================================
        # WELCOME TITLE
        # ====================================================

        tk.Label(
            right_content,
            text="Welcome Back!",
            font=("Segoe UI", 23, "bold"),
            fg=TEXT,
            bg=WHITE
        ).pack(anchor="w")

        # ====================================================
        # SUBTITLE
        # ====================================================

        tk.Label(
            right_content,
            text="Login to submit feedback or view the tracker.",
            font=("Segoe UI", 11),
            fg="#706D85",
            bg=WHITE,
            wraplength=350,
            justify="left"
        ).pack(
            anchor="w",
            pady=(4, 22)
        )

        # ====================================================
        # USERNAME LABEL
        # ====================================================

        tk.Label(
            right_content,
            text="Username",
            font=("Segoe UI", 11, "bold"),
            fg=TEXT,
            bg=WHITE
        ).pack(
            anchor="w",
            pady=(0, 6)
        )

        # ====================================================
        # USERNAME BOX
        # ====================================================

        username_box = tk.Frame(
            right_content,
            bg=WHITE,
            highlightthickness=1,
            highlightbackground=BORDER,
            width=350,
            height=44
        )

        username_box.pack_propagate(False)

        username_box.pack(
            anchor="w",
            fill="x",
            pady=(0, 17)
        )

        self.username_box = username_box

        tk.Label(
            username_box,
            text="👤",
            font=("Segoe UI Emoji", 12),
            fg="#332E48",
            bg=WHITE
        ).pack(
            side="left",
            padx=(11, 6)
        )

        self.username_entry = tk.Entry(
            username_box,
            font=("Segoe UI", 11),
            bd=0,
            relief="flat",
            bg=WHITE,
            fg=TEXT_LIGHT,
            insertbackground=TEXT
        )

        self.username_entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 10)
        )

        self.username_entry.insert(
            0,
            "Enter your username"
        )

        self.username_entry.bind(
            "<FocusIn>",
            lambda event: self.clear_placeholder(
                self.username_entry,
                "Enter your username"
            )
        )

        # ====================================================
        # PASSWORD LABEL
        # ====================================================

        tk.Label(
            right_content,
            text="Password",
            font=("Segoe UI", 11, "bold"),
            fg=TEXT,
            bg=WHITE
        ).pack(
            anchor="w",
            pady=(0, 6)
        )

        # ====================================================
        # PASSWORD BOX
        # ====================================================

        password_box = tk.Frame(
            right_content,
            bg=WHITE,
            highlightthickness=1,
            highlightbackground=BORDER,
            width=350,
            height=44
        )

        password_box.pack_propagate(False)

        password_box.pack(
            anchor="w",
            fill="x",
            pady=(0, 6)
        )

        self.password_box = password_box

        tk.Label(
            password_box,
            text="🔒",
            font=("Segoe UI Emoji", 12),
            fg="#332E48",
            bg=WHITE
        ).pack(
            side="left",
            padx=(11, 6)
        )

        self.password_entry = tk.Entry(
            password_box,
            font=("Segoe UI", 11),
            bd=0,
            relief="flat",
            bg=WHITE,
            fg=TEXT_LIGHT,
            insertbackground=TEXT
        )

        self.password_entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 2)
        )

        # Eye icon to show or hide the password.
        self.password_visible = False

        self.password_eye = tk.Canvas(
            password_box,
            width=30,
            height=30,
            bg=WHITE,
            highlightthickness=0,
            bd=0,
            cursor="hand2"
        )

        self.password_eye.pack(
            side="right",
            padx=(0, 6),
            pady=1
        )

        self.password_eye.bind(
            "<Button-1>",
            lambda event: self.toggle_password_visibility()
        )

        self.password_eye.bind(
            "<Enter>",
            lambda event: self.password_eye.config(cursor="hand2")
        )

        self.password_eye.bind(
            "<Configure>",
            lambda event: self.draw_password_eye()
        )

        self.draw_password_eye()

        self.password_entry.insert(
            0,
            "Enter your password"
        )

        self.password_entry.bind(
            "<FocusIn>",
            lambda event: self.clear_placeholder(
                self.password_entry,
                "Enter your password"
            )
        )

        # ====================================================
        # INLINE VALIDATION MESSAGE
        # ====================================================

        self.validation_label = tk.Label(
            right_content,
            text="",
            font=("Segoe UI", 9),
            fg="#D93025",
            bg=WHITE,
            wraplength=350,
            justify="left",
            anchor="w"
        )

        self.validation_label.pack(
            anchor="w",
            fill="x",
            pady=(0, 6)
        )

        self.username_entry.bind(
            "<KeyRelease>",
            lambda event: self.clear_inline_message()
        )

        self.password_entry.bind(
            "<KeyRelease>",
            lambda event: self.clear_inline_message()
        )

        # ====================================================
        # FORGOT PASSWORD
        # ====================================================

        forgot_label = tk.Label(
            right_content,
            text="Forgot Password?",
            font=("Segoe UI", 10, "bold"),
            fg=PURPLE,
            bg=WHITE,
            cursor="hand2"
        )

        forgot_label.pack(
            anchor="e",
            pady=(0, 20)
        )

        forgot_label.bind(
            "<Button-1>",
            lambda event: self.on_forgot_password()
        )

        # ====================================================
        # LOGIN BUTTONS
        # ====================================================

        login_buttons = tk.Frame(
            right_content,
            bg=WHITE
        )

        login_buttons.pack(
            anchor="w",
            pady=(0, 20)
        )

        self.login_buttons = login_buttons

        student_button = RoundedButton(
            login_buttons,
            text="Login as\nstudent",
            width=165,
            height=54,
            radius=12,
            bg_color=PURPLE,
            fg_color=WHITE,
            font=("Segoe UI", 11, "bold"),
            command=self.on_student_login
        )

        student_button.pack(
            side="left",
            padx=(0, 16)
        )

        self.student_button = student_button

        admin_button = RoundedButton(
            login_buttons,
            text="Login as\nadmin",
            width=165,
            height=54,
            radius=12,
            bg_color=PURPLE,
            fg_color=WHITE,
            font=("Segoe UI", 11, "bold"),
            command=self.on_admin_login
        )

        admin_button.pack(side="left")

        self.admin_button = admin_button

        # ====================================================
        # STUDENT SIGN UP ROW
        # ====================================================

        signup_row = tk.Frame(
            right_content,
            bg=WHITE
        )

        signup_row.pack(anchor="center")

        tk.Label(
            signup_row,
            text="New Student?   ",
            font=("Segoe UI", 11, "bold"),
            fg=TEXT,
            bg=WHITE
        ).pack(side="left")

        signup_link = tk.Label(
            signup_row,
            text="Sign Up",
            font=("Segoe UI", 11, "bold"),
            fg=PURPLE,
            bg=WHITE,
            cursor="hand2"
        )

        signup_link.pack(side="left")

        signup_link.bind(
            "<Button-1>",
            lambda event: self.on_signup()
        )

        # ====================================================
        # ADMIN SIGN UP ROW
        # ====================================================

        admin_signup_row = tk.Frame(
            right_content,
            bg=WHITE
        )

        admin_signup_row.pack(
            anchor="center",
            pady=(7, 0)
        )

        tk.Label(
            admin_signup_row,
            text="New admin? ",
            font=("Segoe UI", 11, "bold"),
            fg=TEXT,
            bg=WHITE
        ).pack(side="left")

        admin_signup_link = tk.Label(
            admin_signup_row,
            text="Admin Sign Up",
            font=("Segoe UI", 11, "bold"),
            fg=PURPLE,
            bg=WHITE,
            cursor="hand2"
        )

        admin_signup_link.pack(side="left")

        admin_signup_link.bind(
            "<Button-1>",
            lambda event: self.on_admin_signup()
        )

        # ====================================================
        # FOOTER
        # About is centered horizontally at the bottom.
        # ====================================================

        footer = tk.Frame(
            self,
            bg=BACKGROUND
        )

        footer.pack(
            side="bottom",
            fill="x",
            pady=(0, 12)
        )

        footer_content = tk.Frame(
            footer,
            bg=BACKGROUND
        )

        footer_content.pack(anchor="center")

        tk.Label(
            footer_content,
            text="© 2026 FeedbackTrack · Made for Student Voices",
            font=("Segoe UI", 10),
            fg="#8D8A9F",
            bg=BACKGROUND
        ).pack(side="left", padx=(0, 10))

        about = tk.Label(
            footer_content,
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
        # RESPONSIVE EVENT BINDINGS
        # ====================================================

        self.bind("<Configure>", self.on_resize)

        self.left_panel.bind(
            "<Configure>",
            self.on_panel_resize
        )

        self.right_panel.bind(
            "<Configure>",
            self.on_panel_resize
        )

        self.protocol(
            "WM_DELETE_WINDOW",
            self.close_application
        )

        self.after_idle(self.update_responsive_layout)

    # ========================================================
    # RESPONSIVE LAYOUT
    # ========================================================

    def on_resize(self, event=None):
        """Adjust the layout when the main window is resized."""

        if event is not None and event.widget is not self:
            return

        if self.resize_job is not None:
            try:
                self.after_cancel(self.resize_job)
            except tk.TclError:
                pass

        self.resize_job = self.after(
            80,
            self.update_responsive_layout
        )

    def on_panel_resize(self, event=None):
        """Update controls when either panel changes size."""

        if event is not None:
            if event.widget not in (
                self.left_panel,
                self.right_panel
            ):
                return

        if self.resize_job is not None:
            try:
                self.after_cancel(self.resize_job)
            except tk.TclError:
                pass

        self.resize_job = self.after(
            80,
            self.update_responsive_layout
        )

    def update_responsive_layout(self):
        """Adjust margins, input widths, buttons, and categories."""

        self.resize_job = None

        if not self.winfo_exists():
            return

        window_width = self.winfo_width()
        window_height = self.winfo_height()

        # 1. Use more of the available window space.
        if window_width < 1000:
            horizontal_padding = 18
        elif window_width < 1400:
            horizontal_padding = 30
        else:
            horizontal_padding = 45

        self.navbar.pack_configure(
            padx=horizontal_padding
        )

        self.card_outer.pack_configure(
            padx=horizontal_padding
        )

        # Adjust vertical spacing for shorter windows.
        if window_height < 700:
            self.navbar.pack_configure(
                pady=(10, 5)
            )

            self.card_outer.pack_configure(
                pady=(5, 6)
            )
        else:
            self.navbar.pack_configure(
                pady=(18, 8)
            )

            self.card_outer.pack_configure(
                pady=(8, 10)
            )

        # 2. Adjust input field widths.
        right_width = self.right_panel.winfo_width()

        if right_width > 1:

            available_width = right_width - 65

            field_width = max(
                230,
                min(350, available_width)
            )

            self.username_box.config(
                width=field_width
            )

            self.password_box.config(
                width=field_width
            )

            self.password_eye.config(
                width=30,
                height=30
            )

            self.draw_password_eye()

            for widget in self.right_content.winfo_children():

                if (
                    isinstance(widget, tk.Label)
                    and widget.cget("text")
                    == "Login to submit feedback or view the tracker."
                ):
                    widget.config(
                        wraplength=field_width
                    )

                elif widget is self.validation_label:
                    widget.config(
                        wraplength=field_width
                    )

        # 3. Adjust login button widths.
        if right_width > 1:

            button_width = max(
                115,
                min(165, (right_width - 85) // 2)
            )

            self.student_button.set_size(
                button_width,
                54
            )

            self.admin_button.set_size(
                button_width,
                54
            )

        # 4. Arrange category labels based on the available width.
        left_width = self.left_panel.winfo_width()

        if left_width > 1:

            if left_width >= 440:
                columns = 5
            else:
                columns = 3

            for category in self.category_labels:
                category.grid_forget()

            for index, category in enumerate(
                self.category_labels
            ):

                row = index // columns
                column = index % columns

                category.grid(
                    row=row,
                    column=column,
                    padx=4,
                    pady=4,
                    sticky="ew"
                )

            for column in range(columns):
                self.category_frame.grid_columnconfigure(
                    column,
                    weight=1
                )

    # ========================================================
    # PLACEHOLDER
    # ========================================================

    def clear_placeholder(self, entry, default_text):

        if entry.get() == default_text:

            entry.delete(0, tk.END)
            entry.config(fg=TEXT)

            if "password" in default_text.lower():
                entry.config(show="•")

    # ========================================================
    # PASSWORD VISIBILITY ICON
    # ========================================================

    def draw_password_eye(self):
        """Draw the compact, scalable eye icon."""

        if (
            not hasattr(self, "password_eye")
            or not self.password_eye.winfo_exists()
        ):
            return

        self.password_eye.delete("all")

        width = max(1, self.password_eye.winfo_width())
        height = max(1, self.password_eye.winfo_height())

        scale_x = width / 27
        scale_y = height / 26
        color = "#332E48"

        self.password_eye.create_arc(
            3 * scale_x, 5 * scale_y,
            24 * scale_x, 21 * scale_y,
            start=200, extent=140,
            style="arc", outline=color, width=1.5
        )

        self.password_eye.create_arc(
            3 * scale_x, 5 * scale_y,
            24 * scale_x, 21 * scale_y,
            start=20, extent=140,
            style="arc", outline=color, width=1.5
        )

        self.password_eye.create_oval(
            10 * scale_x, 9 * scale_y,
            17 * scale_x, 16 * scale_y,
            outline=color, width=1.4
        )

        self.password_eye.create_oval(
            12 * scale_x, 11 * scale_y,
            15 * scale_x, 14 * scale_y,
            fill=color, outline=color
        )

        if not self.password_visible:

            self.password_eye.create_line(
                4 * scale_x, 22 * scale_y,
                23 * scale_x, 3 * scale_y,
                fill=color, width=1.5
            )

    def toggle_password_visibility(self):
        """Show or hide the password without changing its value."""

        current_value = self.password_entry.get()

        if current_value == "Enter your password":
            self.password_entry.focus_set()
            return

        self.password_visible = not self.password_visible

        self.password_entry.config(
            show="" if self.password_visible else "•"
        )

        self.draw_password_eye()
        self.password_entry.focus_set()

    # ========================================================
    # INLINE VALIDATION MESSAGE
    # ========================================================

    def show_inline_message(self, message, message_type="error"):
        """Show validation and error messages below the password field."""

        color = (
            "#D93025"
            if message_type in ("error", "warning")
            else TEXT_LIGHT
        )

        self.validation_label.config(
            text=str(message),
            fg=color
        )

    def clear_inline_message(self):
        """Clear the inline message when the user edits an input."""

        if hasattr(self, "validation_label"):
            self.validation_label.config(text="")

    # ========================================================
    # FIREBASE LOGIN
    # ========================================================

    def authenticate_user(self, required_role):
        """Check the username, password, and account role."""

        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if username in ("", "Enter your username"):
            self.show_inline_message(
                "Please enter your username.",
                "warning"
            )
            self.username_entry.focus_set()
            return

        if password in ("", "Enter your password"):
            self.show_inline_message(
                "Please enter your password.",
                "warning"
            )
            self.password_entry.focus_set()
            return

        if db is None:
            self.show_inline_message(
                "Could not connect to Firestore.\n\n"
                "Check that firebase_config.py and serviceAccountKey.json "
                "are in the same folder and that firebase-admin is installed.\n\n"
                f"Details: {FIRESTORE_IMPORT_ERROR}",
                "error"
            )
            return

        for button in (self.student_button, self.admin_button):
            button.config(cursor="wait")

        self.config(cursor="wait")
        self.update_idletasks()

        try:
            # Find the profile by username to retrieve the registered email.
            # (Public username directory: no one is signed in yet.)
            profile = lookup_username(username)

            if not profile:
                self.show_inline_message(
                    "Username or password is incorrect.",
                    "error"
                )
                return

            email = profile.get("email")

            if not email:
                self.show_inline_message(
                    "This account does not have an email address saved. "
                    "Please contact the administrator.",
                    "error"
                )
                return

            # Verify the password using Firebase Authentication.
            response = requests.post(
                f"{FIREBASE_SIGNIN_URL}?key={FIREBASE_API_KEY}",
                json={
                    "email": email,
                    "password": password,
                    "returnSecureToken": True
                },
                timeout=20
            )

            try:
                result = response.json()
            except ValueError:
                result = {}

            if not response.ok:

                error_code = result.get(
                    "error", {}
                ).get("message", "")

                if error_code in (
                    "EMAIL_NOT_FOUND",
                    "INVALID_PASSWORD",
                    "INVALID_LOGIN_CREDENTIALS",
                    "USER_DISABLED"
                ):
                    error_message = (
                        "Username or password is incorrect."
                    )

                elif error_code == "TOO_MANY_ATTEMPTS_TRY_LATER":
                    error_message = (
                        "Too many login attempts. "
                        "Please wait and try again."
                    )

                elif error_code == "OPERATION_NOT_ALLOWED":
                    error_message = (
                        "Email/Password sign-in is not enabled "
                        "in Firebase Authentication."
                    )

                else:
                    error_message = (
                        "Firebase login failed.\n\n"
                        f"Error: {error_code or 'Unknown error'}"
                    )

                self.show_inline_message(error_message, "error")
                return

            # Firebase returns localId as the authenticated user's UID.
            user_uid = result.get("localId")

            if not user_uid:
                self.show_inline_message(
                    "Firebase authenticated the account, but no user ID "
                    "was returned. Please try again.",
                    "error"
                )
                return

            # Start the signed-in session, then read the role from the
            # user's own profile (Firestore rules verify who is asking).
            set_session(result)

            try:
                own_profile = (
                    db.collection("users").document(user_uid).get()
                )
                role = str(
                    (own_profile.to_dict() or {}).get("role", "")
                ).strip().lower()
            except Exception:
                role = ""

            # Make sure the user has selected the correct type of login.
            if role != required_role:
                clear_session()

                if required_role == "student":
                    self.show_inline_message(
                        "This account is not registered as a student.",
                        "error"
                    )

                else:
                    self.show_inline_message(
                        "This account is not registered as an admin.",
                        "error"
                    )

                return

            # Firebase returns localId as the authenticated user's UID.
            user_uid = result.get("localId")

            if not user_uid:
                self.show_inline_message(
                    "Firebase authenticated the account, but no user ID "
                    "was returned. Please try again.",
                    "error"
                )
                return

            # Open the correct page and pass the user's UID to it.
            if required_role == "student":
                self.open_page(
                    "submit_feedback.py",
                    user_uid=user_uid
                )
            else:
                self.open_page(
                    "view_feedback.py",
                    user_uid=user_uid
                )

        except requests.exceptions.Timeout:
            self.show_inline_message(
                "Firebase did not respond in time. "
                "Check your internet connection and try again.",
                "error"
            )

        except requests.exceptions.RequestException as error:
            self.show_inline_message(
                "Could not connect to Firebase Authentication.\n\n"
                f"{error}",
                "error"
            )

        except Exception as error:
            self.show_inline_message(
                "Could not verify your account. "
                "Check your Firebase configuration.\n\n"
                f"{error}",
                "error"
            )

        finally:
            if self.winfo_exists():

                for button in (
                    self.student_button,
                    self.admin_button
                ):
                    button.config(cursor="hand2")

                self.config(cursor="")

    # ========================================================
    # STUDENT LOGIN
    # ========================================================

    def on_student_login(self):
        self.authenticate_user("student")

    # ========================================================
    # ADMIN LOGIN
    # ========================================================

    def on_admin_login(self):
        self.authenticate_user("admin")

    # ========================================================
    # HEADER LOGIN
    # Kept unchanged, although the header Login button is removed.
    # ========================================================

    def on_login_click(self):
        self.username_entry.focus_set()

    # ========================================================
    # OPEN ANOTHER PAGE
    # ========================================================

    def open_page(self, filename, user_uid=None):
        """
        Open another page and hide this window.

        user_uid is optional. Login passes the UID so the destination
        page knows which account was authenticated.
        """

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

            self.show_inline_message(
                f"{filename} was not found.\n\n"
                "Please keep homepage.py, signup.py, "
                "admin_signup.py, about.py, forgot_password.py, "
                "submit_feedback.py, and view_feedback.py "
                "in the same folder.",
                "error"
            )

            return

        try:
            command = [
                sys.executable,
                page_path
            ]

            if user_uid:
                command.append(user_uid)

            self.child_process = subprocess.Popen(
                command,
                cwd=current_folder
            )

            self.withdraw()

            self.check_child_process()

        except OSError as error:

            self.child_process = None

            self.show_inline_message(
                f"Could not open {filename}.\n\n{error}",
                "error"
            )

    def check_child_process(self):
        """Restore this page when the opened page closes."""

        if not self.winfo_exists():
            return

        if self.child_process is None:
            return

        if self.child_process.poll() is not None:

            self.child_process = None

            # The signed-in page was closed (logout): forget the session.
            try:
                clear_session()
            except NameError:
                pass

            self.deiconify()
            self.lift()

            self.after_idle(
                self.update_responsive_layout
            )

        else:

            self.after(
                200,
                self.check_child_process
            )

    # ========================================================
    # STUDENT SIGN UP
    # ========================================================

    def on_signup(self):
        self.open_page("signup.py")

    # ========================================================
    # ADMIN SIGN UP
    # ========================================================

    def on_admin_signup(self):
        self.open_page("admin_signup.py")

    # ========================================================
    # FORGOT PASSWORD
    # Opens Forgot Password without hiding the login window.
    # ========================================================

    def on_forgot_password(self):
        """
        Open Forgot Password as a separate window process.

        Unlike the other pages, the login window remains visible
        behind Forgot Password.
        """

        # If Forgot Password is already running, do not open another copy.
        if self.forgot_password_process is not None:

            if self.forgot_password_process.poll() is None:
                return

            self.forgot_password_process = None

        current_folder = os.path.dirname(
            os.path.abspath(__file__)
        )

        page_path = os.path.join(
            current_folder,
            "forgot_password.py"
        )

        if not os.path.isfile(page_path):
            self.show_inline_message(
                "forgot_password.py was not found.\n\n"
                "Please keep forgot_password.py in the same folder "
                "as homepage.py.",
                "error"
            )
            return

        try:
            self.forgot_password_process = subprocess.Popen(
                [sys.executable, page_path],
                cwd=current_folder
            )

            # Keep the login window visible.
            # The Forgot Password page will be configured to appear
            # on top in the next update to forgot_password.py.

            self.check_forgot_password_process()

        except OSError as error:

            self.forgot_password_process = None

            self.show_inline_message(
                "Could not open Forgot Password.\n\n"
                f"{error}",
                "error"
            )

    def check_forgot_password_process(self):
        """Track Forgot Password without hiding the login window."""

        if not self.winfo_exists():
            return

        if self.forgot_password_process is None:
            return

        if self.forgot_password_process.poll() is not None:
            self.forgot_password_process = None
        else:
            self.after(
                200,
                self.check_forgot_password_process
            )

    # ========================================================
    # ABOUT
    # ========================================================

    def on_about(self):
        """Open About above the login page without hiding homepage."""

        # If About is already open, bring it to the front.
        if (
            self.about_window is not None
            and self.about_window.winfo_exists()
        ):
            self.about_window.lift()
            self.about_window.focus_force()
            return

        try:
            # Import the existing About page class.
            from about import AboutPage

            # Create About as a child window of this homepage.
            self.about_window = tk.Toplevel(self)

            # Keep About associated with the homepage.
            self.about_window.transient(self)

            # Build the About interface inside the Toplevel.
            self.about_app = AboutPage(self.about_window)

            # Display About above the login page.
            self.about_window.lift()
            self.about_window.focus_force()

            # Clear the references when the About window is destroyed.
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

            self.show_inline_message(
                f"Could not open the About page.\n\n{error}",
                "error"
            )

    def on_about_destroy(self, event=None):
        """Clear the About window reference when it closes."""

        if (
            event is not None
            and self.about_window is not None
            and event.widget is self.about_window
        ):
            self.about_window = None
            self.about_app = None

    # ========================================================
    # CLOSE APPLICATION
    # ========================================================

    def close_application(self):

        # Cancel any pending responsive update.
        if self.resize_job is not None:

            try:
                self.after_cancel(self.resize_job)
            except tk.TclError:
                pass

        # Close the About window if it is still open.
        if self.about_window is not None:

            try:
                if self.about_window.winfo_exists():
                    self.about_window.destroy()
            except tk.TclError:
                pass

        # Close any child page that is still running.
        if self.child_process is not None:

            if self.child_process.poll() is None:

                try:
                    self.child_process.terminate()
                except OSError:
                    pass

        # Close Forgot Password if it is still running.
        if self.forgot_password_process is not None:

            if self.forgot_password_process.poll() is None:

                try:
                    self.forgot_password_process.terminate()
                except OSError:
                    pass

        self.destroy()


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    app = FeedbackTrackApp()
    app.mainloop()