import tkinter as tk
import requests
import re

# ============================================================
# FeedbackTrack - Forgot Password Page
# File name: forgot_password.py
#
# Features:
# 1. Matches the About page colours and font
# 2. Responsive layout when resizing
# 3. Rounded white card and purple button
# 4. Back to Login navigation
# 5. Sends an actual password reset email through Firebase
# ============================================================


# ==============================
# Colour Palette - same as about.py
# ==============================

BG_COLOR = "#F3F2FC"
PRIMARY_COLOR = "#6C63FF"
HOVER_COLOR = "#554BEF"
DARK_TEXT = "#1E1B2E"
LIGHT_TEXT = "#6B6880"
WHITE = "#FFFFFF"
BORDER_COLOR = "#E0DCFB"

FONT_FAMILY = "Segoe UI"


# ==============================
# Firebase Configuration
# ==============================

# Use the same Firebase Web API key as your login page.
FIREBASE_API_KEY = "AIzaSyBd1KHyHiU9OfPu1BoH3H3KORtUJrOZbmg"

FIREBASE_RESET_URL = (
    "https://identitytoolkit.googleapis.com/v1/"
    "accounts:sendOobCode"
)


# ==============================
# Rounded Rectangle Helper
# ==============================

def rounded_rectangle(
    canvas, x1, y1, x2, y2,
    radius=12, fill=WHITE, outline=""
):
    """Draw a rounded rectangle on a Tkinter Canvas."""

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

    return canvas.create_polygon(
        points,
        smooth=True,
        splinesteps=36,
        fill=fill,
        outline=outline
    )


# ==============================
# Rounded Button
# ==============================

class RoundedButton(tk.Canvas):

    def __init__(
        self, parent, text="Send Reset Link",
        command=None, width=170, height=42
    ):
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=parent["bg"],
            highlightthickness=0,
            bd=0,
            cursor="hand2"
        )

        self.command = command
        self.width = width
        self.height = height

        self.button_shape = rounded_rectangle(
            self, 1, 1, width - 1, height - 1,
            radius=12,
            fill=PRIMARY_COLOR,
            outline=PRIMARY_COLOR
        )

        self.button_text = self.create_text(
            width / 2,
            height / 2,
            text=text,
            fill=WHITE,
            font=(FONT_FAMILY, 10, "bold")
        )

        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)

        self.tag_bind(
            self.button_text, "<Button-1>", self.on_click
        )

    def on_enter(self, event=None):
        self.itemconfigure(
            self.button_shape,
            fill=HOVER_COLOR,
            outline=HOVER_COLOR
        )

    def on_leave(self, event=None):
        self.itemconfigure(
            self.button_shape,
            fill=PRIMARY_COLOR,
            outline=PRIMARY_COLOR
        )

    def on_click(self, event=None):
        if self.command:
            self.command()


# ==============================
# Forgot Password Application
# ==============================

class ForgotPasswordPage:

    def __init__(self, root):

        self.root = root
        self.root.title("FeedbackTrack - Reset Password")

        # Same starting window size as the About page.
        self.root.geometry("460x430")
        self.root.minsize(380, 400)
        self.root.resizable(True, True)
        self.root.configure(bg=BG_COLOR)

        # Keep the About page's borderless window style.
        self.root.overrideredirect(True)

        self.placeholder = "Enter your email address"

        # Centre the window when the page first opens.
        self.center_window()

        # Main canvas redraws the layout when the window resizes.
        self.canvas = tk.Canvas(
            self.root,
            bg=BG_COLOR,
            highlightthickness=0,
            bd=0
        )
        self.canvas.pack(fill="both", expand=True)

        # Create the heading and form widgets.
        self.create_widgets()

        self.canvas.bind("<Configure>", self.draw_page)
        self.root.bind("<Escape>", self.back_to_login)

    # ==============================
    # Centre Window
    # ==============================

    def center_window(self):

        self.root.update_idletasks()

        width = 460
        height = 430

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        self.root.geometry(
            f"{width}x{height}+{x}+{y}"
        )

    # ==============================
    # Create Widgets
    # ==============================

    def create_widgets(self):

        # Back to Login
        self.back_label = tk.Label(
            self.root,
            text="← Back to Login",
            font=(FONT_FAMILY, 10, "bold"),
            fg=LIGHT_TEXT,
            bg=WHITE,
            cursor="hand2"
        )
        self.back_label.bind(
            "<Button-1>", self.back_to_login
        )

        # Main heading
        self.heading = tk.Label(
            self.root,
            text="Reset your Password",
            font=(FONT_FAMILY, 18, "bold"),
            fg=DARK_TEXT,
            bg=WHITE
        )

        # Subtitle
        self.subtitle = tk.Label(
            self.root,
            text="We'll email you a link to create a new password.",
            font=(FONT_FAMILY, 9),
            fg=LIGHT_TEXT,
            bg=WHITE,
            wraplength=390,
            justify="center"
        )

        # Email label
        self.email_label = tk.Label(
            self.root,
            text="Email Address",
            font=(FONT_FAMILY, 9, "bold"),
            fg=DARK_TEXT,
            bg=WHITE
        )

        # Rounded email entry outline
        self.entry_canvas = tk.Canvas(
            self.root,
            width=340,
            height=44,
            bg=WHITE,
            highlightthickness=0,
            bd=0
        )

        rounded_rectangle(
            self.entry_canvas,
            1, 1, 339, 43,
            radius=10,
            fill=WHITE,
            outline=BORDER_COLOR
        )

        self.email_entry = tk.Entry(
            self.entry_canvas,
            font=(FONT_FAMILY, 10),
            fg=LIGHT_TEXT,
            bg=WHITE,
            relief="flat",
            bd=0,
            insertbackground=DARK_TEXT
        )

        self.email_entry.insert(0, self.placeholder)

        self.entry_canvas.create_window(
            170, 22,
            window=self.email_entry,
            width=300,
            height=30
        )

        self.email_entry.bind(
            "<FocusIn>", self.remove_placeholder
        )
        self.email_entry.bind(
            "<FocusOut>", self.restore_placeholder
        )
        self.email_entry.bind(
            "<Return>", self.send_reset_link
        )

        # Inline validation and status message.
        self.status_label = tk.Label(
            self.root,
            text="",
            font=(FONT_FAMILY, 8),
            fg="#D93025",
            bg=WHITE,
            wraplength=340,
            justify="center"
        )

        self.email_entry.bind(
            "<KeyRelease>", self.clear_status
        )

        # Send Reset Link button
        self.reset_button = RoundedButton(
            self.root,
            text="Send Reset Link",
            command=self.send_reset_link,
            width=170,
            height=42
        )

    # ==============================
    # Responsive Layout
    # ==============================

    def draw_page(self, event=None):

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        if width < 100 or height < 100:
            return

        # Redraw the white rounded card.
        self.canvas.delete("page_content")

        rounded_rectangle(
            self.canvas,
            3, 3,
            width - 3, height - 3,
            radius=20,
            fill=WHITE,
            outline=WHITE,
        )

        # Adjust the form width to fit smaller windows.
        content_width = min(340, width - 40)
        content_width = max(200, content_width)

        centre_x = width / 2

        # Back to Login
        self.back_label.place(
            x=20,
            y=18
        )

        # Heading
        self.heading.place(
            x=centre_x,
            y=height * 0.29,
            anchor="center"
        )

        # Subtitle
        self.subtitle.config(
            wraplength=max(200, width - 50)
        )
        self.subtitle.place(
            x=centre_x,
            y=height * 0.40,
            anchor="center"
        )

        # Email label
        self.email_label.place(
            x=centre_x - content_width / 2 + 2,
            y=height * 0.53,
            anchor="nw"
        )

        # Resize the entry outline.
        self.entry_canvas.config(
            width=content_width
        )

        self.entry_canvas.delete("outline")

        rounded_rectangle(
            self.entry_canvas,
            1, 1,
            content_width - 1, 43,
            radius=10,
            fill=WHITE,
            outline=BORDER_COLOR
        )

        # Keep the input inside the rounded border.
        if not hasattr(self, "email_window"):

            self.email_window = self.entry_canvas.create_window(
                content_width / 2,
                22,
                window=self.email_entry,
                width=content_width - 30,
                height=30
            )

        else:

            self.entry_canvas.coords(
                self.email_window,
                content_width / 2,
                22
            )

            self.entry_canvas.itemconfigure(
                self.email_window,
                width=content_width - 30
            )

        self.entry_canvas.place(
            x=centre_x,
            y=height * 0.58,
            anchor="n"
        )

        # Validation message: moved slightly down to prevent overlap.
        self.status_label.config(
            wraplength=max(200, content_width)
        )
        self.status_label.place(
            x=centre_x,
            y=height * 0.73,
            anchor="center"
        )

        # Send Reset Link button
        self.reset_button.place(
            x=centre_x,
            y=height * 0.85,
            anchor="center"
        )

    # ==============================
    # Placeholder Handling
    # ==============================

    def remove_placeholder(self, event=None):

        if self.email_entry.get() == self.placeholder:
            self.email_entry.delete(0, tk.END)
            self.email_entry.config(fg=DARK_TEXT)

    def restore_placeholder(self, event=None):

        if not self.email_entry.get().strip():
            self.email_entry.insert(0, self.placeholder)
            self.email_entry.config(fg=LIGHT_TEXT)

    # ==============================
    # Inline Status Message
    # ==============================

    def show_status(self, message, success=False):
        """Show validation, success, or error feedback below the email field."""

        self.status_label.config(
            text=message,
            fg="#218838" if success else "#D93025"
        )

    def clear_status(self, event=None):
        """Clear the previous message when the user edits the email."""

        if hasattr(self, "status_label"):
            self.status_label.config(text="")

    # ==============================
    # Back to Login
    # ==============================

    def back_to_login(self, event=None):
        """Close this window so the existing login process can return."""

        self.root.destroy()

    # ==============================
    # Send Firebase Password Reset
    # ==============================

    def send_reset_link(self, event=None):

        email = self.email_entry.get().strip()

        if not email or email == self.placeholder:
            self.show_status(
                "Please enter your registered email address."
            )
            self.email_entry.focus_set()
            return

        # Validate the email format using Python's re module.
        if not re.fullmatch(
            r"[^\s@]+@[^\s@]+\.[^\s@]+",
            email
        ):
            self.show_status(
                "Please enter a valid email address."
            )
            self.email_entry.focus_set()
            return

        try:
            response = requests.post(
                f"{FIREBASE_RESET_URL}?key={FIREBASE_API_KEY}",
                json={
                    "requestType": "PASSWORD_RESET",
                    "email": email
                },
                timeout=20
            )

            if response.ok:
                self.show_status(
                    "If an account matches that email address, password reset "
                    "instructions will be sent. Please check your inbox and "
                    "spam folder.",
                    success=True
                )
                return

            # Convert Firebase error codes into simple messages.
            try:
                error_code = response.json().get(
                    "error", {}
                ).get("message", "")
            except ValueError:
                error_code = ""

            if error_code == "EMAIL_NOT_FOUND":
                message = (
                    "No account was found for that email address. "
                    "Please check the email and try again."
                )

            elif error_code == "INVALID_EMAIL":
                message = (
                    "Please enter a valid email address."
                )

            elif error_code == "OPERATION_NOT_ALLOWED":
                message = (
                    "Password reset is not enabled in Firebase Authentication. "
                    "Check your Firebase sign-in settings."
                )

            elif error_code == "TOO_MANY_ATTEMPTS_TRY_LATER":
                message = (
                    "Too many attempts were made. Please wait and try again later."
                )

            else:
                message = (
                    "Firebase could not process your request. "
                    "Please try again later."
                )

            self.show_status(message)

        except requests.exceptions.Timeout:
            self.show_status(
                "Firebase took too long to respond. Please try again."
            )

        except requests.exceptions.RequestException:
            self.show_status(
                "Could not connect to Firebase. "
                "Please check your internet connection and try again."
            )


# ==============================
# Run the Application
# ==============================

if __name__ == "__main__":

    root = tk.Tk()

    app = ForgotPasswordPage(root)

    root.mainloop()
