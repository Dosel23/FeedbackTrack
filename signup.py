import tkinter as tk
from tkinter import messagebox
import subprocess
import sys
import os
import re
import requests
from datetime import datetime, timezone

# ============================================================
# FIREBASE CONFIGURATION
# ============================================================
FIREBASE_API_KEY =  "AIzaSyBd1KHyHiU9OfPu1BoH3H3KORtUJrOZbmg"
FIREBASE_AUTH_URL = (
    "https://identitytoolkit.googleapis.com/v1/accounts:signUp"
)

try:
    from firebase_config import (
        db, lookup_username, set_session, clear_session,
        delete_auth_account
    )
    FIRESTORE_IMPORT_ERROR = None
except Exception as error:
    db = None
    FIRESTORE_IMPORT_ERROR = error


# ============================================================
# COLORS
# ============================================================
BACKGROUND = "#F3F2FC"
WHITE = "#FFFFFF"
LEFT_BACKGROUND = "#FAFAFE"
ICON_BACKGROUND = "#EEEDFF"
PURPLE = "#6C63FF"
PURPLE_DARK = "#5750D9"
TEXT = "#1E1B2E"
TEXT_LIGHT = "#6B6880"
BORDER = "#E0DCFB"
CARD_BORDER = "#E2E0F0"
ERROR_COLOR = "#C62828"
WARNING_COLOR = "#B45309"
SUCCESS_COLOR = "#2E7D32"


# ============================================================
# VALIDATION HELPERS
# ============================================================
def show_field_message(label, message="", kind="error"):
    if label is not None and label.winfo_exists():
        color = {
            "error": ERROR_COLOR,
            "warning": WARNING_COLOR,
            "success": SUCCESS_COLOR
        }.get(kind, ERROR_COLOR)

        label.config(text=message, fg=color)


def is_placeholder(entry):
    return entry.get() == entry.placeholder_text


def validate_full_name(event=None):
    value = full_name_entry.get().strip()

    if not value or is_placeholder(full_name_entry):
        show_field_message(full_name_error, "Full name is required.")
        return False

    if len(value) < 2:
        show_field_message(
            full_name_error,
            "Please enter a name with at least 2 characters."
        )
        return False

    show_field_message(full_name_error, "")
    return True


def validate_username(event=None, check_database=False):
    value = username_entry.get().strip()

    if not value or is_placeholder(username_entry):
        show_field_message(username_error, "Username is required.")
        return False

    # Username can have any length.
    # Only letters, numbers, and underscores are allowed.
    if not re.fullmatch(r"[A-Za-z0-9_]+", value):
        show_field_message(
            username_error,
            "Use only letters, numbers or underscores."
        )
        return False

    if check_database:
        if db is None:
            show_field_message(
                username_error,
                "Could not check username availability.",
                "warning"
            )
            return False

        try:
            existing_users = lookup_username(value)

            if existing_users:
                show_field_message(
                    username_error,
                    "This username is already in use."
                )
                return False

        except Exception:
            show_field_message(
                username_error,
                "Could not check username. Please try again.",
                "warning"
            )
            return False

    show_field_message(username_error, "")
    return True


def validate_email(event=None):
    value = email_entry.get().strip()

    if not value or is_placeholder(email_entry):
        show_field_message(email_error, "Student email is required.")
        return False

    # Required format:
    # 08230 + exactly 3 digits + .sce@rub.edu.bt
    pattern = r"08230\d{3}\.sce@rub\.edu\.bt"

    if not re.fullmatch(pattern, value):
        show_field_message(
            email_error,
            "Use this format: 08230XXX.sce@rub.edu.bt"
        )
        return False

    show_field_message(
        email_error,
        "Email format is valid.",
        "success"
    )
    return True


def validate_password(event=None):
    value = password_entry.get()

    if not value or is_placeholder(password_entry):
        show_field_message(password_error, "Password is required.")
        return False

    if len(value) < 8:
        show_field_message(
            password_error,
            "Password must contain at least 8 characters."
        )
        return False

    if not re.search(r"[A-Z]", value):
        show_field_message(
            password_error,
            "Add at least one uppercase letter (A–Z)."
        )
        return False

    if not re.search(r"[a-z]", value):
        show_field_message(
            password_error,
            "Add at least one lowercase letter (a–z)."
        )
        return False

    if not re.search(r"\d", value):
        show_field_message(
            password_error,
            "Add at least one number (0–9)."
        )
        return False

    if not re.search(r"[^A-Za-z0-9]", value):
        show_field_message(
            password_error,
            "Add at least one special character, such as ! or #."
        )
        return False

    show_field_message(
        password_error,
        "Password meets all requirements.",
        "success"
    )

    if (
        confirm_password_entry.get()
        and not is_placeholder(confirm_password_entry)
    ):
        validate_confirm_password()

    return True


def validate_confirm_password(event=None):
    value = confirm_password_entry.get()
    password = password_entry.get()

    if not value or is_placeholder(confirm_password_entry):
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

    show_field_message(
        confirm_password_error,
        "Passwords match.",
        "success"
    )
    return True


# ============================================================
# PLACEHOLDER HELPER
# ============================================================
def add_placeholder(entry, placeholder, is_password=False):
    entry.placeholder_text = placeholder
    entry.password_visible = False
    entry.insert(0, placeholder)
    entry.config(fg=TEXT_LIGHT, show="")

    def on_focus_in(event):
        if is_placeholder(entry):
            entry.delete(0, tk.END)
            entry.config(fg=TEXT)

            if is_password:
                entry.config(
                    show="" if entry.password_visible else "*"
                )

    def on_focus_out(event):
        if entry.get() == "":
            entry.config(show="")
            entry.insert(0, placeholder)
            entry.config(fg=TEXT_LIGHT)

    entry.bind("<FocusIn>", on_focus_in, add="+")
    entry.bind("<FocusOut>", on_focus_out, add="+")


# ============================================================
# MAIN WINDOW
# ============================================================
root = tk.Tk()
root.title("FeedbackTrack - Student Sign Up")

# Same window size as homepage.py.
root.geometry("1200x780")
root.minsize(850, 620)

root.configure(bg=BACKGROUND)
root.resizable(True, True)

login_process = None
about_process = None


# ============================================================
# NAVIGATION
# ============================================================
def check_process_closed(page_name):
    global login_process, about_process

    process = login_process if page_name == "login" else about_process

    if process is None:
        return

    if process.poll() is not None:
        if page_name == "login":
            login_process = None
        else:
            about_process = None

        root.deiconify()
        root.lift()
    else:
        root.after(
            200,
            lambda: check_process_closed(page_name)
        )


def open_page(filename, page_name):
    global login_process, about_process

    current_process = (
        login_process if page_name == "login" else about_process
    )

    if current_process is not None:
        if current_process.poll() is None:
            return

        if page_name == "login":
            login_process = None
        else:
            about_process = None

    current_folder = os.path.dirname(os.path.abspath(__file__))
    page_path = os.path.join(current_folder, filename)

    if not os.path.isfile(page_path):
        messagebox.showerror(
            "Page Not Found",
            f"{filename} was not found.\n\n"
            "Keep the required Python files in the same folder."
        )
        return

    try:
        process = subprocess.Popen(
            [sys.executable, page_path],
            cwd=current_folder
        )

        if page_name == "login":
            login_process = process

            # Keep the original Login navigation behavior.
            root.withdraw()

        else:
            about_process = process

            # CHANGED:
            # Do not hide the sign-up page when opening About.
            # The About window can now appear in front of it.
            root.deiconify()

        root.after(
            200,
            lambda: check_process_closed(page_name)
        )

    except OSError as error:
        messagebox.showerror(
            "Navigation Error",
            f"Could not open {filename}.\n\n{error}"
        )


def open_login():
    open_page("homepage.py", "login")


def open_about():
    open_page("about.py", "about")


# ============================================================
# RESET FORM
# ============================================================
def reset_form():
    fields = [
        (full_name_entry, "Enter your full name"),
        (username_entry, "Choose a username"),
        (email_entry, "Enter your student email"),
        (password_entry, "Enter your password"),
        (confirm_password_entry, "Re-enter your password")
    ]

    for entry, placeholder in fields:
        entry.config(show="")
        entry.delete(0, tk.END)
        entry.insert(0, placeholder)
        entry.config(fg=TEXT_LIGHT)

        if hasattr(entry, "password_visible"):
            entry.password_visible = False

        if hasattr(entry, "visibility_icon_redraw"):
            entry.visibility_icon_redraw()

    for label in (
        full_name_error,
        username_error,
        email_error,
        password_error,
        confirm_password_error
    ):
        show_field_message(label, "")


# ============================================================
# CREATE STUDENT ACCOUNT
# ============================================================
def create_account():
    name_ok = validate_full_name()
    username_ok = validate_username()
    email_ok = validate_email()
    password_ok = validate_password()
    confirm_ok = validate_confirm_password()

    if not all((
        name_ok,
        username_ok,
        email_ok,
        password_ok,
        confirm_ok
    )):
        messagebox.showwarning(
            "Check Your Details",
            "Please fill in all required fields correctly."
        )
        return

    if db is None:
        messagebox.showerror(
            "Firebase Configuration Error",
            "Could not connect to Firestore.\n\n"
            "Check firebase_config.py, serviceAccountKey.json, "
            "and your firebase-admin installation.\n\n"
            f"Details: {FIRESTORE_IMPORT_ERROR}"
        )
        return

    # Check username availability before creating the Auth account.
    if not validate_username(check_database=True):
        return

    create_button.config(
        state="disabled",
        text="Creating Account..."
    )
    root.update_idletasks()

    try:
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
            error_code = auth_result.get(
                "error", {}
            ).get("message", "UNKNOWN_ERROR")

            friendly_errors = {
                "EMAIL_EXISTS":
                    "An account with this email already exists.",
                "INVALID_EMAIL":
                    "Please enter a valid student email address.",
                "WEAK_PASSWORD":
                    "Firebase rejected the password. Choose a stronger password.",
                "OPERATION_NOT_ALLOWED":
                    "Enable Email/Password sign-in in Firebase Authentication.",
                "TOO_MANY_ATTEMPTS_TRY_LATER":
                    "Too many attempts. Please wait and try again.",
                "API_KEY_INVALID":
                    "The Firebase Web API key is invalid. Check your project settings."
            }

            messagebox.showerror(
                "Account Creation Failed",
                friendly_errors.get(
                    error_code,
                    "Firebase could not create the account.\n\n"
                    f"Error: {error_code}"
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
            # Save student profile only. Never save the password here.
            db.collection("users").document(user_id).set({
                "full_name": full_name_entry.get().strip(),
                "username": username_entry.get().strip(),
                "email": email_entry.get().strip().lower(),
                "role": "student",
                "created_at": datetime.now(timezone.utc)
            })
        except Exception:
            clear_session()
            delete_auth_account(auth_result.get("idToken"))
            raise
        finally:
            clear_session()

        messagebox.showinfo(
            "Account Created",
            "Your student account has been created successfully!\n\n"
            "You can now log in using your email and password."
        )

        reset_form()

    except requests.exceptions.Timeout:
        messagebox.showerror(
            "Connection Timeout",
            "Firebase did not respond in time. "
            "Check your internet connection and try again."
        )

    except requests.exceptions.RequestException as error:
        messagebox.showerror(
            "Connection Error",
            f"Could not connect to Firebase Authentication.\n\n{error}"
        )

    except Exception as error:
        messagebox.showerror(
            "Account or Database Error",
            "Something went wrong while creating the account "
            "or saving the student profile.\n\n"
            "Check your Firebase settings and Firestore permissions.\n\n"
            f"Details: {error}"
        )

    finally:
        create_button.config(
            state="normal",
            text="Create Account"
        )


# ============================================================
# NAVIGATION BAR
# ============================================================
navbar = tk.Frame(root, bg=BACKGROUND)
navbar.pack(fill="x", padx=30, pady=(18, 8))

brand_frame = tk.Frame(navbar, bg=BACKGROUND)
brand_frame.pack(side="left")

tk.Label(
    brand_frame,
    text="💬",
    font=("Segoe UI Emoji", 19),
    fg=TEXT,
    bg=BACKGROUND
).pack(side="left", padx=(0, 9))

tk.Label(
    brand_frame,
    text="FeedbackTrack",
    font=("Segoe UI", 19, "bold"),
    fg=TEXT,
    bg=BACKGROUND
).pack(side="left")


# ============================================================
# MAIN CARD
# ============================================================
card_outer = tk.Frame(root, bg=BACKGROUND)
card_outer.pack(
    fill="both",
    expand=True,
    padx=30,
    pady=(8, 10)
)

card = tk.Frame(
    card_outer,
    bg=WHITE,
    highlightthickness=1,
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
    text="🌱",
    font=("Segoe UI Emoji", 29)
)

left_title = tk.Frame(left_content, bg=LEFT_BACKGROUND)
left_title.pack()

tk.Label(
    left_title,
    text="Join in ",
    font=("Segoe UI", 21, "bold"),
    fg=TEXT,
    bg=LEFT_BACKGROUND
).pack(side="left")

tk.Label(
    left_title,
    text="mintues",
    font=("Segoe UI", 21, "bold"),
    fg=PURPLE,
    bg=LEFT_BACKGROUND
).pack(side="left")

tk.Label(
    left_content,
    text=(
        "Create your student account to access\n"
        "FeedbackTrack and share feedback with\n"
        "your institution."
    ),
    font=("Segoe UI", 12),
    fg=TEXT_LIGHT,
    bg=LEFT_BACKGROUND,
    justify="center"
).pack(pady=(17, 0))


# ============================================================
# RIGHT PANEL
# ============================================================
right_panel = tk.Frame(card, bg=WHITE)
right_panel.grid(row=0, column=1, sticky="nsew")

right_content = tk.Frame(right_panel, bg=WHITE)
right_content.place(relx=0.5, rely=0.5, anchor="center")

tk.Label(
    right_content,
    text="Create Student Account",
    font=("Segoe UI", 21, "bold"),
    fg=TEXT,
    bg=WHITE
).pack()

tk.Label(
    right_content,
    text="Enter your details to get started.",
    font=("Segoe UI", 11),
    fg=TEXT_LIGHT,
    bg=WHITE
).pack(pady=(4, 12))


# ============================================================
# INPUT FIELD CREATION
# ============================================================
def create_input_field(
    parent,
    label_text,
    icon_text,
    placeholder,
    is_password=False,
    validation_function=None
):
    tk.Label(
        parent,
        text=label_text,
        font=("Segoe UI", 11, "bold"),
        fg=TEXT,
        bg=WHITE
    ).pack(anchor="w", pady=(0, 3))

    # Changed to match admin_signup.py: width=290, height=30.
    input_box = tk.Frame(
        parent,
        bg=WHITE,
        highlightthickness=1,
        highlightbackground=BORDER,
        width=290,
        height=30
    )
    input_box.pack_propagate(False)
    input_box.pack(anchor="w", pady=(0, 0))

    tk.Label(
        input_box,
        text=icon_text,
        font=("Segoe UI Emoji", 12),
        fg="#332E48",
        bg=WHITE,
        width=3
    ).pack(side="left")

    entry = tk.Entry(
        input_box,
        font=("Segoe UI", 11),
        bd=0,
        relief="flat",
        bg=WHITE,
        fg=TEXT_LIGHT,
        insertbackground=TEXT,
        show=""
    )
    entry.pack(
        side="left",
        fill="both",
        expand=True,
        padx=(0, 8)
    )

    add_placeholder(entry, placeholder, is_password)

    if is_password:
        visibility_icon = tk.Canvas(
            input_box,
            width=30,
            height=30,
            bg=WHITE,
            highlightthickness=0,
            bd=0,
            cursor="hand2"
        )
        visibility_icon.pack(side="right", padx=(0, 5), pady=1)

        def draw_visibility_icon():
            visibility_icon.delete("all")
            visibility_icon.create_arc(
                3, 5, 27, 23,
                start=200, extent=140,
                style="arc", outline="#332E48", width=1.5
            )
            visibility_icon.create_arc(
                3, 5, 27, 23,
                start=20, extent=140,
                style="arc", outline="#332E48", width=1.5
            )
            visibility_icon.create_oval(
                10, 10, 20, 20,
                outline="#332E48", width=1.4
            )
            visibility_icon.create_oval(
                13, 13, 17, 17,
                fill="#332E48", outline="#332E48"
            )

            if not entry.password_visible:
                visibility_icon.create_line(
                    4, 25, 26, 3,
                    fill="#332E48", width=1.5
                )

        def toggle_password_visibility(event=None):
            entry.password_visible = not entry.password_visible

            if is_placeholder(entry):
                entry.config(show="")
            else:
                entry.config(
                    show="" if entry.password_visible else "*"
                )

            draw_visibility_icon()

        visibility_icon.bind(
            "<Button-1>",
            toggle_password_visibility
        )
        draw_visibility_icon()
        entry.visibility_icon_redraw = draw_visibility_icon

    # Changed to match admin_signup.py: wraplength=290.
    error_label = tk.Label(
        parent,
        text="",
        font=("Segoe UI", 9),
        fg=ERROR_COLOR,
        bg=WHITE,
        justify="left",
        wraplength=290,
        anchor="w"
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
# FORM FIELDS
# ============================================================
full_name_entry = create_input_field(
    right_content,
    "Full Name",
    "👤",
    "Enter your full name",
    validation_function=validate_full_name
)
full_name_error = full_name_entry.validation_label

username_entry = create_input_field(
    right_content,
    "Username",
    "👤",
    "Choose a username",
    validation_function=validate_username
)
username_error = username_entry.validation_label

username_entry.bind(
    "<FocusOut>",
    lambda event: validate_username(check_database=True),
    add="+"
)

email_entry = create_input_field(
    right_content,
    "Student Email",
    "✉",
    "Enter your student email",
    validation_function=validate_email
)
email_error = email_entry.validation_label

password_entry = create_input_field(
    right_content,
    "Password",
    "🔒",
    "Enter your password",
    is_password=True,
    validation_function=validate_password
)
password_error = password_entry.validation_label

confirm_password_entry = create_input_field(
    right_content,
    "Confirm Password",
    "🔒",
    "Re-enter your password",
    is_password=True,
    validation_function=validate_confirm_password
)
confirm_password_error = confirm_password_entry.validation_label


# ============================================================
# CREATE ACCOUNT BUTTON
# ============================================================
# Changed to match admin_signup.py button dimensions and font.
create_button_frame = tk.Frame(
    right_content,
    bg=WHITE,
    width=290,
    height=30
)
create_button_frame.pack_propagate(False)
create_button_frame.pack(anchor="w", pady=(4, 10))

create_button = tk.Button(
    create_button_frame,
    text="Create Account",
    command=create_account,
    font=("Segoe UI", 11, "bold"),
    fg=WHITE,
    bg=PURPLE,
    activeforeground=WHITE,
    activebackground=PURPLE_DARK,
    relief="flat",
    bd=0,
    padx=0,
    pady=0,
    cursor="hand2"
)
create_button.pack(fill="both", expand=True)


# ============================================================
# LOGIN LINK
# ============================================================
login_row = tk.Frame(right_content, bg=WHITE)
login_row.pack(anchor="center")

tk.Label(
    login_row,
    text="Already have an account?   ",
    font=("Segoe UI", 11, "bold"),
    fg=TEXT,
    bg=WHITE
).pack(side="left")

login_link = tk.Label(
    login_row,
    text="Login",
    font=("Segoe UI", 11, "bold"),
    fg=PURPLE,
    bg=WHITE,
    cursor="hand2"
)
login_link.pack(side="left")
login_link.bind("<Button-1>", lambda event: open_login())


# ============================================================
# FOOTER
# ============================================================
footer = tk.Frame(root, bg=BACKGROUND)
footer.pack(side="bottom", pady=(0, 12))

tk.Label(
    footer,
    text="© 2026 FeedbackTrack · Student Feedback Management   ",
    font=("Segoe UI", 10),
    fg=TEXT_LIGHT,
    bg=BACKGROUND
).pack(side="left")

about = tk.Label(
    footer,
    text="About",
    font=("Segoe UI", 10, "bold"),
    fg=PURPLE,
    bg=BACKGROUND,
    cursor="hand2"
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
    for process in (login_process, about_process):
        if process is not None and process.poll() is None:
            try:
                process.terminate()
            except OSError:
                pass

    root.destroy()


root.protocol("WM_DELETE_WINDOW", close_signup)


# ============================================================
# RUN APPLICATION
# ============================================================
if __name__ == "__main__":
    root.mainloop()