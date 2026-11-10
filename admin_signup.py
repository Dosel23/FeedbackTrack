import tkinter as tk
from tkinter import messagebox, simpledialog
import subprocess
import sys
import os
import re
import requests
from datetime import datetime, timezone

# Firebase Authentication Web API key for your Firebase project.
FIREBASE_API_KEY = "AIzaSyBd1KHyHiU9OfPu1BoH3H3KORtUJrOZbmg"
FIREBASE_AUTH_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signUp"

# Firestore connection from your existing firebase_config.py.
# Keep firebase_config.py and serviceAccountKey.json beside this file.
try:
    from firebase_config import (
        db, lookup_username, set_session, clear_session,
        delete_auth_account
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
ICON_BACKGROUND = "#EEEDFF"
PURPLE = "#6C63FF"
PURPLE_DARK = "#5750D9"
PURPLE_LIGHT = "#EEEDFF"
TEXT = "#1E1B2E"
TEXT_LIGHT = "#6B6880"
BORDER = "#E0DCFB"
CARD_BORDER = "#E2E0F0"
ERROR_COLOR = "#C62828"
WARNING_COLOR = "#B45309"
SUCCESS_COLOR = "#2E7D32"


# ============================================================
# INLINE FIELD VALIDATION
# Each field displays its own message while the user types.
# ============================================================
def show_field_message(label, message="", kind="error"):
    if label is not None and label.winfo_exists():
        color = SUCCESS_COLOR if kind == "success" else (
            WARNING_COLOR if kind == "warning" else ERROR_COLOR
        )
        label.config(text=message, fg=color)


def validate_full_name(event=None):
    value = full_name_entry.get().strip()
    if not value or value == "Enter your full name":
        show_field_message(full_name_error, "Full name is required.")
        return False
    show_field_message(full_name_error, "")
    return True


def validate_username(event=None, check_database=False):
    value = username_entry.get().strip()
    if not value or value == "Choose a username":
        show_field_message(username_error, "Username is required.")
        return False

    # Check for an existing username when the user leaves this field.
    # The final check is also repeated before account creation.
    if check_database and db is not None:
        try:
            existing_users = lookup_username(value)
            if existing_users:
                show_field_message(
                    username_error,
                    "This username is already in use."
                )
                return False
        except Exception:
            # Do not block typing if the database check temporarily fails.
            show_field_message(username_error, "")
            return True

    show_field_message(username_error, "")
    return True


def validate_email(event=None):
    value = email_entry.get().strip()
    if not value or value == "Enter your email address":
        show_field_message(email_error, "Email address is required.")
        return False
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
        show_field_message(email_error, "Enter a valid email address.")
        return False
    show_field_message(email_error, "")
    return True


def validate_password(event=None):
    value = password_entry.get()
    if not value or value == "Enter your password":
        show_field_message(password_error, "Password is required.")
        return False

    # Strong password requirements: at least 8 characters, uppercase,
    # lowercase, number, and special character.
    if len(value) < 8:
        show_field_message(
            password_error,
            "Password must contain at least 8 characters."
        )
        return False
    if not re.search(r"[A-Z]", value):
        show_field_message(
            password_error,
            "Add at least one uppercase letter (A-Z)."
        )
        return False
    if not re.search(r"[a-z]", value):
        show_field_message(
            password_error,
            "Add at least one lowercase letter (a-z)."
        )
        return False
    if not re.search(r"\d", value):
        show_field_message(
            password_error,
            "Add at least one number (0-9)."
        )
        return False
    if not re.search(r"[^A-Za-z0-9]", value):
        show_field_message(
            password_error,
            "Add at least one special character (e.g. !, @, #)."
        )
        return False

    show_field_message(password_error, "", kind="success")

    # Update confirmation validation immediately when the password changes.
    if confirm_password_entry.get() not in (
        "", "Re-enter your password"
    ):
        validate_confirm_password()
    return True


def validate_confirm_password(event=None):
    value = confirm_password_entry.get()
    password = password_entry.get()

    if not value or value == "Re-enter your password":
        show_field_message(
            confirm_password_error,
            "Please confirm your password."
        )
        return False
    if value != password:
        show_field_message(
            confirm_password_error,
            "Passwords do not match."
        )
        return False
    show_field_message(confirm_password_error, "", kind="success")
    return True


# ============================================================
# ROUNDED BUTTON
# ============================================================
class RoundedButton(tk.Canvas):
    def __init__(
        self, parent, text="", width=120, height=38, radius=12,
        bg_color=WHITE, fg_color=TEXT, font=("Segoe UI", 9, "bold"),
        command=None, border_color=None, border_width=1
    ):
        super().__init__(
            parent, width=width, height=height, bg=parent["bg"],
            highlightthickness=0, bd=0
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

    def draw(self):
        self.delete("all")
        r, w, h = self.radius, self.width, self.height
        if self.border_color:
            self.create_rounded_rectangle(
                0, 0, w, h, r, fill=self.border_color, outline=""
            )
            self.create_rounded_rectangle(
                self.border_width, self.border_width,
                w - self.border_width, h - self.border_width,
                max(1, r - self.border_width),
                fill=self.bg_color, outline=""
            )
        else:
            self.create_rounded_rectangle(
                0, 0, w, h, r, fill=self.bg_color, outline=""
            )
        self.create_text(
            w / 2, h / 2, text=self.text, fill=self.fg_color,
            font=self.font, anchor="center", justify="center"
        )

    def create_rounded_rectangle(self, x1, y1, x2, y2, radius, **kwargs):
        points = [
            x1 + radius, y1, x2 - radius, y1, x2, y1,
            x2, y1 + radius, x2, y2 - radius, x2, y2,
            x2 - radius, y2, x1 + radius, y2, x1, y2,
            x1, y2 - radius, x1, y1 + radius, x1, y1
        ]
        return self.create_polygon(points, smooth=True, **kwargs)

    def on_click(self):
        if self.command:
            self.command()


# ============================================================
# MAIN APPLICATION WINDOW
# ============================================================
root = tk.Tk()
root.title("FeedbackTrack - Admin Sign Up")

# Match the window size used in homepage.py.
root.geometry("1200x780")
root.minsize(850, 620)

root.configure(bg=BACKGROUND)
root.resizable(True, True)

login_process = None
about_process = None


# ============================================================
# LOGIN AND ABOUT PAGE NAVIGATION
# ============================================================
def check_login_closed():
    global login_process
    if login_process is None:
        return
    if login_process.poll() is not None:
        login_process = None
        root.deiconify()
        root.lift()
    else:
        root.after(200, check_login_closed)


def open_login():
    global login_process
    if login_process is not None:
        if login_process.poll() is None:
            return
        login_process = None

    current_folder = os.path.dirname(os.path.abspath(__file__))
    homepage_path = os.path.join(current_folder, "homepage.py")
    if not os.path.isfile(homepage_path):
        messagebox.showerror(
            "Login Error",
            "homepage.py was not found.\n\n"
            "Please keep homepage.py and admin_signup.py in the same folder."
        )
        return
    try:
        login_process = subprocess.Popen(
            [sys.executable, homepage_path], cwd=current_folder
        )
        root.withdraw()
        root.after(200, check_login_closed)
    except OSError as error:
        login_process = None
        messagebox.showerror(
            "Login Error", f"Could not open the login page.\n\n{error}"
        )


def check_about_closed():
    global about_process
    if about_process is None:
        return
    if about_process.poll() is not None:
        about_process = None
        root.deiconify()
        root.lift()
    else:
        root.after(200, check_about_closed)


def open_about():
    global about_process
    if about_process is not None:
        if about_process.poll() is None:
            return
        about_process = None

    current_folder = os.path.dirname(os.path.abspath(__file__))
    about_path = os.path.join(current_folder, "about.py")
    if not os.path.isfile(about_path):
        messagebox.showerror(
            "About Error",
            "about.py was not found.\n\n"
            "Please keep homepage.py, admin_signup.py, and about.py "
            "in the same folder."
        )
        return
    try:
        about_process = subprocess.Popen(
            [sys.executable, about_path], cwd=current_folder
        )

        # Keep the sign-up page visible behind About.
        # Do not call root.withdraw() here.
        # about.py should use attributes("-topmost", True)
        # and lift() to display itself in front.
        root.after(200, check_about_closed)

    except OSError as error:
        about_process = None
        messagebox.showerror(
            "About Error", f"Could not open the About page.\n\n{error}"
        )


def open_signup():
    messagebox.showinfo(
        "Sign Up", "You are already on the admin registration page."
    )


# ============================================================
# CREATE ADMIN ACCOUNT
# ============================================================
def create_account():
    # Validate each field and show the message beside that field.
    name_ok = validate_full_name()
    username_ok = validate_username(check_database=True)
    email_ok = validate_email()
    password_ok = validate_password()
    confirm_ok = validate_confirm_password()

    if not all((name_ok, username_ok, email_ok, password_ok, confirm_ok)):
        return

    if db is None:
        messagebox.showerror(
            "Firebase Configuration Error",
            "Could not connect to Firestore.\n\n"
            "Check that firebase_config.py and serviceAccountKey.json "
            "are in the same folder and that firebase-admin is installed.\n\n"
            f"Details: {FIRESTORE_IMPORT_ERROR}"
        )
        return

    create_button.config(state="disabled", text="Creating Account...")
    root.update_idletasks()

    try:
        # Check username again immediately before creating the account.
        existing_users = lookup_username(username_entry.get().strip())
        if existing_users:
            show_field_message(
                username_error, "This username is already in use."
            )
            return

        response = requests.post(
            f"{FIREBASE_AUTH_URL}?key={FIREBASE_API_KEY}",
            json={
                "email": email_entry.get().strip(),
                "password": password_entry.get(),
                "returnSecureToken": True
            },
            timeout=20
        )

        try:
            auth_result = response.json()
        except ValueError:
            auth_result = {}

        if not response.ok:
            error_code = auth_result.get("error", {}).get(
                "message", "UNKNOWN_ERROR"
            )
            friendly_errors = {
                "EMAIL_EXISTS": "An account with this email already exists.",
                "INVALID_EMAIL": "Please enter a valid email address.",
                "WEAK_PASSWORD":
                    "Your password must contain at least 8 characters, an uppercase letter, a lowercase letter, a number, and a special character.",
                "OPERATION_NOT_ALLOWED":
                    "Email/Password sign-in is not enabled in Firebase Authentication.",
                "TOO_MANY_ATTEMPTS_TRY_LATER":
                    "Too many attempts. Please wait and try again.",
                "API_KEY_INVALID":
                    "The Firebase Web API key is invalid. Check your Firebase project settings."
            }
            messagebox.showerror(
                "Account Creation Failed",
                friendly_errors.get(
                    error_code,
                    f"Firebase could not create the account.\n\nError: {error_code}"
                )
            )
            return

        user_id = auth_result.get("localId")
        if not user_id:
            messagebox.showerror(
                "Account Creation Failed",
                "Firebase did not return a user ID. Please try again."
            )
            return

        # Sign in as the new user so Firestore rules accept the writes.
        set_session(auth_result)

        try:
            # Store profile data only. Passwords must never be saved in Firestore.
            db.collection("users").document(user_id).set({
                "full_name": full_name_entry.get().strip(),
                "username": username_entry.get().strip(),
                "email": email_entry.get().strip().lower(),
                "role": "admin",
                "created_at": datetime.now(timezone.utc)
            })
        except Exception as profile_error:
            clear_session()
            delete_auth_account(auth_result.get("idToken"))
            print("Admin profile error:", repr(profile_error))
            messagebox.showerror(
                "Account Not Created",
                "The admin profile could not be saved.\n\n"
                "Please check your internet connection and try again."
            )
            return
        finally:
            clear_session()

        messagebox.showinfo(
            "Account Created",
            "Your admin account has been created successfully!\n\n"
            "You can now log in using your email address and password."
        )

        for entry, placeholder in (
            (full_name_entry, "Enter your full name"),
            (username_entry, "Choose a username"),
            (email_entry, "Enter your email address"),
            (password_entry, "Enter your password"),
            (confirm_password_entry, "Re-enter your password")
        ):
            entry.config(show="")
            if hasattr(entry, "password_visible"):
                entry.password_visible = False
                if hasattr(entry, "visibility_icon_redraw"):
                    entry.visibility_icon_redraw()
            entry.delete(0, tk.END)
            entry.insert(0, placeholder)
            entry.config(fg=TEXT_LIGHT)

        for error_label in (
            full_name_error, username_error, email_error,
            password_error, confirm_password_error
        ):
            show_field_message(error_label, "")

    except requests.exceptions.Timeout:
        messagebox.showerror(
            "Connection Timeout",
            "Firebase did not respond in time. Check your internet connection and try again."
        )
    except requests.exceptions.RequestException as error:
        messagebox.showerror(
            "Connection Error",
            f"Could not connect to Firebase Authentication.\n\n{error}"
        )
    except Exception as error:
        messagebox.showerror(
            "Database Error",
            "The account may have been created in Firebase Authentication, "
            "but saving the profile to Firestore failed. Check your Firebase "
            "configuration and Firestore access.\n\n"
            f"Details: {error}"
        )
    finally:
        create_button.config(state="normal", text="Create Account")


# ============================================================
# PLACEHOLDER HELPER
# ============================================================
def add_placeholder(entry, placeholder, is_password=False):
    entry.insert(0, placeholder)
    entry.config(fg=TEXT_LIGHT)
    entry.password_visible = False
    entry.placeholder_text = placeholder

    def on_focus_in(event):
        if entry.get() == placeholder:
            entry.delete(0, tk.END)
            entry.config(fg=TEXT)
            if is_password:
                entry.config(show="" if entry.password_visible else "*")

    def on_focus_out(event):
        if entry.get() == "":
            entry.config(show="")
            entry.insert(0, placeholder)
            entry.config(fg=TEXT_LIGHT)

    entry.bind("<FocusIn>", on_focus_in)
    entry.bind("<FocusOut>", on_focus_out)


# ============================================================
# TOP NAVIGATION BAR AND LOGO
# ============================================================
navbar = tk.Frame(root, bg=BACKGROUND)
navbar.pack(fill="x", padx=30, pady=(18, 8))

brand_frame = tk.Frame(navbar, bg=BACKGROUND)
brand_frame.pack(side="left")

tk.Label(
    brand_frame, text="💬", font=("Segoe UI Emoji", 19),
    fg=TEXT, bg=BACKGROUND
).pack(side="left", padx=(0, 9))

tk.Label(
    brand_frame, text="FeedbackTrack", font=("Segoe UI", 19, "bold"),
    fg=TEXT, bg=BACKGROUND
).pack(side="left")


# ============================================================
# MAIN CARD
# ============================================================
card_outer = tk.Frame(root, bg=BACKGROUND)
card_outer.pack(fill="both", expand=True, padx=30, pady=(8, 10))

card = tk.Frame(
    card_outer, bg=WHITE, highlightthickness=1,
    highlightbackground=CARD_BORDER
)
card.pack(fill="both", expand=True)
card.grid_columnconfigure(0, weight=1, uniform="columns")
card.grid_columnconfigure(1, weight=1, uniform="columns")
card.grid_rowconfigure(0, weight=1)


# ============================================================
# LEFT PANEL
# ============================================================
left_panel = tk.Frame(card, bg=LEFT_BACKGROUND)
left_panel.grid(row=0, column=0, sticky="nsew")

left_content = tk.Frame(left_panel, bg=LEFT_BACKGROUND)
left_content.place(relx=0.5, rely=0.5, anchor="center")

icon_canvas = tk.Canvas(
    left_content, width=70, height=70, bg=LEFT_BACKGROUND,
    highlightthickness=0, bd=0
)
icon_canvas.pack(pady=(0, 32))
icon_canvas.create_oval(5, 5, 65, 65, fill=ICON_BACKGROUND, outline="")
icon_canvas.create_text(35, 35, text="🌱", font=("Segoe UI Emoji", 25))

left_title = tk.Frame(left_content, bg=LEFT_BACKGROUND)
left_title.pack()
tk.Label(
    left_title, text="Join in ", font=("Segoe UI", 21, "bold"),
    fg=TEXT, bg=LEFT_BACKGROUND
).pack(side="left")
tk.Label(
    left_title, text="minutes", font=("Segoe UI", 21, "bold"),
    fg=PURPLE, bg=LEFT_BACKGROUND
).pack(side="left")

tk.Label(
    left_content,
    text=(
        "Create an admin account to review student\n"
        "feedback, reply to it and move it from New to\n"
        "Resolved."
    ),
    font=("Segoe UI", 12), fg=TEXT_LIGHT,
    bg=LEFT_BACKGROUND, justify="left"
).pack(pady=(24, 0))


# ============================================================
# RIGHT PANEL AND FORM HEADING
# ============================================================
right_panel = tk.Frame(card, bg=WHITE)
right_panel.grid(row=0, column=1, sticky="nsew")

right_content = tk.Frame(right_panel, bg=WHITE)
right_content.place(relx=0.5, rely=0.5, anchor="center")

tk.Label(
    right_content, text="Create Admin Account",
    font=("Segoe UI", 21, "bold"), fg=TEXT, bg=WHITE
).pack()

tk.Label(
    right_content,
    text="Create an account to manage and respond to feedback.",
    font=("Segoe UI", 11), fg=TEXT_LIGHT, bg=WHITE
).pack(pady=(4, 12))


# ============================================================
# INPUT FIELD HELPER
# ============================================================
def create_input_field(
    parent, label_text, icon_text, placeholder,
    is_password=False, validation_function=None
):
    tk.Label(
        parent, text=label_text, font=("Segoe UI", 11, "bold"),
        fg=TEXT, bg=WHITE
    ).pack(anchor="w", pady=(0, 2))

    input_box = tk.Frame(
        parent, bg=WHITE, highlightthickness=1,
        highlightbackground=BORDER, width=290, height=30
    )
    input_box.pack_propagate(False)
    input_box.pack(anchor="w", pady=(0, 0))

    tk.Label(
        input_box, text=icon_text, font=("Segoe UI Emoji", 12),
        fg="#332E48", bg=WHITE, width=3
    ).pack(side="left")

    entry = tk.Entry(
        input_box, font=("Segoe UI", 11), bd=0,
        relief="flat", bg=WHITE, fg=TEXT_LIGHT,
        insertbackground=TEXT, show=""
    )
    entry.pack(side="left", fill="both", expand=True, padx=(0, 8))
    add_placeholder(entry, placeholder, is_password=is_password)

    if is_password:
        visibility_icon = tk.Canvas(
            input_box, width=27, height=26, bg=WHITE,
            highlightthickness=0, bd=0, cursor="hand2"
        )
        visibility_icon.pack(side="right", padx=(0, 5), pady=1)

        def draw_visibility_icon():
            visibility_icon.delete("all")
            visibility_icon.create_arc(
                3, 5, 24, 21, start=200, extent=140,
                style="arc", outline="#332E48", width=1.4
            )
            visibility_icon.create_arc(
                3, 5, 24, 21, start=20, extent=140,
                style="arc", outline="#332E48", width=1.4
            )
            visibility_icon.create_oval(
                10, 9, 17, 16, outline="#332E48", width=1.3
            )
            visibility_icon.create_oval(
                12, 11, 15, 14, fill="#332E48", outline="#332E48"
            )
            if not entry.password_visible:
                visibility_icon.create_line(
                    4, 22, 23, 3, fill="#332E48", width=1.5
                )

        def toggle_password_visibility(event=None):
            entry.password_visible = not entry.password_visible
            if entry.get() == placeholder:
                entry.config(show="")
            else:
                entry.config(
                    show="" if entry.password_visible else "*"
                )
            draw_visibility_icon()

        visibility_icon.bind("<Button-1>", toggle_password_visibility)
        visibility_icon.bind(
            "<Enter>", lambda event: visibility_icon.config(cursor="hand2")
        )
        draw_visibility_icon()
        entry.visibility_icon_redraw = draw_visibility_icon

    # Individual validation text directly below this field.
    error_label = tk.Label(
        parent, text="", font=("Segoe UI", 9),
        fg=ERROR_COLOR, bg=WHITE, justify="left",
        wraplength=290, anchor="w"
    )
    error_label.pack(anchor="w", fill="x", pady=(1, 3))
    entry.validation_label = error_label

    if validation_function:
        entry.bind(
            "<KeyRelease>",
            lambda event: validation_function(),
            add="+"
        )
        entry.bind(
            "<FocusOut>",
            lambda event: validation_function(),
            add="+"
        )

    return entry


# ============================================================
# FORM FIELDS WITH INDIVIDUAL LIVE VALIDATION
# ============================================================
full_name_entry = create_input_field(
    right_content, "Full Name", "👤", "Enter your full name",
    validation_function=validate_full_name
)
full_name_error = full_name_entry.validation_label

username_entry = create_input_field(
    right_content, "Username", "👤", "Choose a username",
    validation_function=validate_username
)
username_error = username_entry.validation_label
username_entry.bind(
    "<FocusOut>",
    lambda event: validate_username(check_database=True),
    add="+"
)

email_entry = create_input_field(
    right_content, "Email", "✉", "Enter your email address",
    validation_function=validate_email
)
email_error = email_entry.validation_label

password_entry = create_input_field(
    right_content, "Password", "🔒", "Enter your password",
    is_password=True, validation_function=validate_password
)
password_error = password_entry.validation_label

confirm_password_entry = create_input_field(
    right_content, "Confirm Password", "🔒", "Re-enter your password",
    is_password=True, validation_function=validate_confirm_password
)
confirm_password_error = confirm_password_entry.validation_label



# ============================================================
# CREATE ACCOUNT BUTTON
# ============================================================
create_button_frame = tk.Frame(
    right_content, bg=WHITE, width=290, height=30
)
create_button_frame.pack_propagate(False)
create_button_frame.pack(anchor="w", pady=(4, 10))

create_button = tk.Button(
    create_button_frame, text="Create Account", command=create_account,
    font=("Segoe UI", 11, "bold"), fg=WHITE, bg=PURPLE,
    activeforeground=WHITE, activebackground=PURPLE_DARK,
    relief="flat", bd=0, padx=0, pady=0, cursor="hand2"
)
create_button.pack(fill="both", expand=True)


# ============================================================
# EXISTING ACCOUNT ROW
# ============================================================
login_row = tk.Frame(right_content, bg=WHITE)
login_row.pack(anchor="center")

tk.Label(
    login_row, text="Already have an account?   ",
    font=("Segoe UI", 11, "bold"), fg=TEXT, bg=WHITE
).pack(side="left")

login_link = tk.Label(
    login_row, text="Login", font=("Segoe UI", 11, "bold"),
    fg=PURPLE, bg=WHITE, cursor="hand2"
)
login_link.pack(side="left")
login_link.bind("<Button-1>", lambda event: open_login())


# ============================================================
# FOOTER
# ============================================================
footer = tk.Frame(root, bg=BACKGROUND)
footer.pack(side="bottom", pady=(0, 12))

tk.Label(
    footer, text="© 2026 FeedbackTrack · Made for Feedback Management   ",
    font=("Segoe UI", 10), fg=TEXT_LIGHT, bg=BACKGROUND
).pack(side="left")

about = tk.Label(
    footer, text="About", font=("Segoe UI", 10, "bold"),
    fg=PURPLE, bg=BACKGROUND, cursor="hand2"
)
about.pack(side="left")
about.bind("<Button-1>", lambda event: open_about())


# ============================================================
# RESPONSIVE LAYOUT
# ============================================================
def update_responsive_layout(event=None):
    if event is not None and event.widget != root:
        return

    window_width = root.winfo_width()
    window_height = root.winfo_height()

    if window_width < 1000:
        side_margin = 18
    elif window_width < 1400:
        side_margin = 30
    else:
        side_margin = 45

    navbar.pack_configure(padx=side_margin)
    card_outer.pack_configure(padx=side_margin)

    if window_height < 700:
        navbar.pack_configure(pady=(10, 5))
        card_outer.pack_configure(pady=(5, 6))
    else:
        navbar.pack_configure(pady=(18, 8))
        card_outer.pack_configure(pady=(8, 10))


root.bind("<Configure>", update_responsive_layout)


# ============================================================
# CLOSE WINDOW
# ============================================================
def close_signup():
    if login_process is not None and login_process.poll() is None:
        try:
            login_process.terminate()
        except OSError:
            pass
    if about_process is not None and about_process.poll() is None:
        try:
            about_process.terminate()
        except OSError:
            pass
    root.destroy()


root.protocol("WM_DELETE_WINDOW", close_signup)


# ============================================================
# START APPLICATION
# Run using: python admin_signup.py
# ============================================================
if __name__ == "__main__":
    root.mainloop()