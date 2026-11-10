import tkinter as tk
from tkinter import messagebox

# Import the login window class from homepage.py.
# This allows landing.py to open your existing login page.
from homepage import FeedbackTrackApp

# Import the About page class from about.py.
from about import AboutPage


# ==============================
# Rounded Button
# ==============================

class RoundedButton(tk.Canvas):
    """Custom Tkinter widget to create smooth rounded buttons."""

    def __init__(
        self,
        parent,
        text="",
        width=120,
        height=38,
        radius=12,
        bg_color="#6C63FF",
        fg_color="#FFFFFF",
        font=("Segoe UI", 11, "bold"),
        command=None,
        border_color=None,
        border_width=1,
    ):
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=parent["bg"],
            highlightthickness=0,
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

        self.bind("<Button-1>", lambda e: self.on_click())
        self.bind("<Enter>", lambda e: self.config(cursor="hand2"))

    def set_size(self, width, height):
        """Resize the button when the available window space changes."""
        width = max(65, int(width))
        height = max(32, int(height))

        if width == self.width and height == self.height:
            return

        self.width = width
        self.height = height

        self.config(width=width, height=height)
        self.draw()

    def draw(self):
        """Draw the rounded button and its text."""
        self.delete("all")

        w, h = self.width, self.height
        r = min(self.radius, w / 2, h / 2)
        bw = self.border_width if self.border_color else 0

        if self.border_color:
            self.create_rounded_rect(
                0, 0, w, h, r,
                fill=self.border_color,
                outline=""
            )

            self.create_rounded_rect(
                bw, bw, w - bw, h - bw,
                max(1, r - bw),
                fill=self.bg_color,
                outline=""
            )
        else:
            self.create_rounded_rect(
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
        )

    def create_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        """Create a rounded rectangle using a smooth polygon."""
        points = [
            x1 + r, y1,
            x2 - r, y1,
            x2, y1,
            x2, y1 + r,
            x2, y2 - r,
            x2, y2,
            x2 - r, y2,
            x1 + r, y2,
            x1, y2,
            x1, y2 - r,
            x1, y1 + r,
            x1, y1,
        ]

        return self.create_polygon(
            points,
            smooth=True,
            **kwargs
        )

    def on_click(self):
        """Execute the function assigned to the button."""
        if self.command:
            self.command()


# ==============================
# Main Window
# ==============================

root = tk.Tk()
root.title("FeedbackTrack")

# Match the window size used in homepage.py.
root.geometry("1200x780")
root.minsize(850, 620)
root.resizable(True, True)
root.configure(bg="#F3F2FC")


# ==============================
# Colors
# ==============================

PURPLE = "#6C63FF"
PURPLE_DARK = "#5750D9"
PURPLE_LIGHT = "#EEEDFF"

BACKGROUND = "#F3F2FC"
WHITE = "#FFFFFF"

TEXT = "#1E1B2E"
TEXT_LIGHT = "#6B6880"


# ==============================
# Page Navigation Variables
# ==============================

login_window = None
about_window = None


# ==============================
# Login Navigation Functions
# ==============================

def close_login():
    """Close the login window and show the landing page again."""
    global login_window

    if login_window is not None:
        login_window.destroy()
        login_window = None

    root.deiconify()
    root.lift()
    root.after_idle(update_responsive_layout)


def open_login():
    """
    Open the login page defined in homepage.py.
    Show the landing page again when the login window closes.
    """
    global login_window

    if login_window is not None:
        try:
            if login_window.winfo_exists():
                login_window.lift()
                login_window.focus_force()
                return
        except tk.TclError:
            login_window = None

    root.withdraw()

    try:
        login_window = FeedbackTrackApp()
        login_window.protocol("WM_DELETE_WINDOW", close_login)

    except Exception as error:
        login_window = None
        root.deiconify()

        messagebox.showerror(
            "Login Error",
            f"Could not open the login page.\n\n{error}"
        )


# ==============================
# About Navigation Functions
# ==============================

def open_about():
    """
    Open the existing About page from about.py.
    The landing page remains open behind it.
    """
    global about_window

    if about_window is not None:
        try:
            if about_window.winfo_exists():
                about_window.lift()
                about_window.focus_force()
                return
        except tk.TclError:
            about_window = None

    try:
        about_window = tk.Toplevel(root)

        AboutPage(about_window)

        about_window.transient(root)
        about_window.lift()
        about_window.focus_force()

    except Exception as error:
        if about_window is not None:
            try:
                about_window.destroy()
            except tk.TclError:
                pass

        about_window = None

        messagebox.showerror(
            "About Error",
            f"Could not open the About page.\n\n{error}"
        )


# ==============================
# Get Started Function
# ==============================

def get_started():
    """The Get Started button opens the login page."""
    open_login()


# ==============================
# Responsive Layout Helper
# ==============================

resize_job = None
last_category_columns = None
last_responsive_width = None


def schedule_responsive_layout(event=None):
    """
    Schedule layout changes when the main window is resized.
    Ignore configure events from child widgets.
    """
    global resize_job

    if event is not None and event.widget is not root:
        return

    if resize_job is not None:
        try:
            root.after_cancel(resize_job)
        except tk.TclError:
            pass

    resize_job = root.after(60, update_responsive_layout)


def update_responsive_layout():
    """
    Adjust widget sizes, spacing, text wrapping, and category layout.
    Preserve the existing design and functionality.
    """
    global resize_job
    global last_category_columns
    global last_responsive_width

    resize_job = None

    if not root.winfo_exists():
        return

    window_width = root.winfo_width()
    window_height = root.winfo_height()

    if window_width <= 1 or window_height <= 1:
        return

    # Adjust the margins to suit the larger window.
    if window_width < 950:
        horizontal_margin = 20
        vertical_margin = 15
        card_margin = 20
    elif window_width < 1400:
        horizontal_margin = 30
        vertical_margin = 20
        card_margin = 30
    else:
        horizontal_margin = 40
        vertical_margin = 25
        card_margin = 40

    main_frame.pack_configure(
        padx=horizontal_margin,
        pady=vertical_margin
    )

    card.pack_configure(
        padx=card_margin,
        pady=(0, 15)
    )

    card_width = max(
        300,
        window_width
        - (horizontal_margin * 2)
        - (card_margin * 2)
        - 2
    )

    description.config(
        wraplength=max(260, card_width - 60)
    )

    # Responsive heading and icon sizes.
    if window_width < 950:
        heading_font = ("Segoe UI", 17, "bold")
        icon_font = ("Segoe UI Emoji", 28)
        button_padx = 22
    elif window_width < 1400:
        heading_font = ("Segoe UI", 22, "bold")
        icon_font = ("Segoe UI Emoji", 38)
        button_padx = 30
    else:
        heading_font = ("Segoe UI", 24, "bold")
        icon_font = ("Segoe UI Emoji", 42)
        button_padx = 34

    heading1.config(font=heading_font)
    heading2.config(font=heading_font)
    icon.config(font=icon_font)
    get_started_button.config(padx=button_padx)

    if window_height < 700:
        content.place_configure(
            relx=0.5,
            rely=0.46,
            anchor="center"
        )
    else:
        content.place_configure(
            relx=0.5,
            rely=0.48,
            anchor="center"
        )

    # Display all five categories in one row when space permits.
    if card_width < 540:
        category_columns = 3
    else:
        category_columns = 5

    if category_columns != last_category_columns:
        last_category_columns = category_columns

        for index, category in enumerate(category_labels):
            row = index // category_columns
            column = index % category_columns

            category.grid(
                row=row,
                column=column,
                padx=5,
                pady=4,
                sticky="nsew"
            )

        for column in range(5):
            category_frame.grid_columnconfigure(
                column,
                weight=0
            )

        for column in range(category_columns):
            category_frame.grid_columnconfigure(
                column,
                weight=1
            )

    footer_width = max(300, window_width - 40)

    if window_width < 950:
        footer_text.config(
            font=("Segoe UI", 8),
            wraplength=footer_width - 70
        )
        about_button.config(
            font=("Segoe UI", 9, "bold")
        )
    else:
        footer_text.config(
            font=("Segoe UI", 10),
            wraplength=footer_width - 80
        )
        about_button.config(
            font=("Segoe UI", 10, "bold")
        )

    last_responsive_width = window_width


# ==============================
# Main Container
# ==============================

main_frame = tk.Frame(
    root,
    bg=BACKGROUND
)

main_frame.pack(
    fill="both",
    expand=True,
    padx=40,
    pady=25
)


# ==============================
# Top Navigation Bar
# ==============================

top_bar = tk.Frame(
    main_frame,
    bg=BACKGROUND
)

top_bar.pack(
    fill="x",
    pady=(0, 25)
)


# ==============================
# Logo
# ==============================

logo_frame = tk.Frame(
    top_bar,
    bg=BACKGROUND
)

logo_frame.pack(side="left")

logo_icon = tk.Label(
    logo_frame,
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
    logo_frame,
    text="FeedbackTrack",
    font=("Segoe UI", 19, "bold"),
    fg=TEXT,
    bg=BACKGROUND
)

logo_text.pack(side="left")


# ==============================
# Main White Card
# ==============================

card = tk.Frame(
    main_frame,
    bg=WHITE,
    highlightbackground="#E0DEEB",
    highlightthickness=1
)

card.pack(
    fill="both",
    expand=True,
    padx=40,
    pady=(0, 15)
)


# ==============================
# Center Content
# ==============================

content = tk.Frame(
    card,
    bg=WHITE
)

content.place(
    relx=0.5,
    rely=0.48,
    anchor="center"
)


# ==============================
# Conversation / Speech Bubble Icon
# ==============================

icon = tk.Label(
    content,
    text="💬",
    font=("Segoe UI Emoji", 38),
    fg=TEXT,
    bg=WHITE
)

icon.pack(
    pady=(0, 18)
)


# ==============================
# Main Heading
# ==============================

heading_frame = tk.Frame(
    content,
    bg=WHITE
)

heading_frame.pack()

heading1 = tk.Label(
    heading_frame,
    text="Your Voice ",
    font=("Segoe UI", 22, "bold"),
    fg=TEXT,
    bg=WHITE
)

heading1.pack(side="left")

heading2 = tk.Label(
    heading_frame,
    text="Matters",
    font=("Segoe UI", 22, "bold"),
    fg=PURPLE,
    bg=WHITE
)

heading2.pack(side="left")


# ==============================
# Description
# ==============================

description = tk.Label(
    content,
    text=(
        "Share feedback about academics, food, hostel, or library life —\n"
        "and actually see what happens to it after you submit it."
    ),
    font=("Segoe UI", 12),
    fg=TEXT_LIGHT,
    bg=WHITE,
    justify="center",
    wraplength=700
)

description.pack(
    pady=(22, 22)
)


# ==============================
# Get Started Button
# ==============================

get_started_button = tk.Button(
    content,
    text="Get Started   →",
    command=get_started,
    font=("Segoe UI", 13, "bold"),
    fg=WHITE,
    bg=PURPLE,
    activeforeground=WHITE,
    activebackground=PURPLE_DARK,
    relief="flat",
    bd=0,
    padx=30,
    pady=11,
    cursor="hand2"
)

get_started_button.pack()


# ==============================
# Category Section
# ==============================

category_frame = tk.Frame(
    content,
    bg=WHITE
)

category_frame.pack(
    pady=(32, 0)
)

categories = [
    ("Academic", "🎓"),
    ("Food", "🍽"),
    ("Hostel", "🏠"),
    ("Library", "📚"),
    ("Other", "⭐")
]

category_labels = []

for name, emoji in categories:
    category = tk.Label(
        category_frame,
        text=f"{emoji} {name}",
        font=("Segoe UI", 10),
        fg=TEXT_LIGHT,
        bg=PURPLE_LIGHT,
        padx=12,
        pady=6
    )

    category_labels.append(category)

    category.grid(
        row=0,
        column=len(category_labels) - 1,
        padx=5,
        pady=4,
        sticky="nsew"
    )


# ==============================
# Footer
# ==============================

footer = tk.Frame(
    main_frame,
    bg=BACKGROUND
)

footer.pack(
    fill="x",
    pady=(2, 0)
)

footer_content = tk.Frame(
    footer,
    bg=BACKGROUND
)

footer_content.pack(
    anchor="center"
)

footer_text = tk.Label(
    footer_content,
    text="© 2026 FeedbackTrack · Made for Student Voices",
    font=("Segoe UI", 10),
    fg=TEXT_LIGHT,
    bg=BACKGROUND,
    justify="center"
)

footer_text.pack(
    side="left",
    padx=(0, 15)
)

about_button = tk.Button(
    footer_content,
    text="About",
    font=("Segoe UI", 10, "bold"),
    fg=PURPLE,
    bg=BACKGROUND,
    activeforeground=PURPLE_DARK,
    activebackground=BACKGROUND,
    relief="flat",
    bd=0,
    cursor="hand2",
    command=open_about
)

about_button.pack(side="left")


# ==============================
# Enable Responsive Layout
# ==============================

root.bind("<Configure>", schedule_responsive_layout)

root.after_idle(update_responsive_layout)


# ==============================
# Start Application
# ==============================

if __name__ == "__main__":
    root.mainloop()
