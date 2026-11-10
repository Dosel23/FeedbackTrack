import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import os
from datetime import datetime, date

# Firebase connection; database problems are shown in simple language.
try:
    from firebase_config import db
    FIREBASE_IMPORT_ERROR = None
except Exception:
    db = None
    FIREBASE_IMPORT_ERROR = True


# ============================================================
# FeedbackTrack - Admin View Feedback Page
# Responsive design with a scrollable feedback table
# Styling matched with my_feedback.py
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
PURPLE_LIGHT = "#EEEDFF"

TEXT = "#1E1B2E"
TEXT_LIGHT = "#6B6880"

BORDER = "#E0DCFB"
CARD_BORDER = "#E2E0F0"

# Match the sidebar settings in my_feedback.py.
SIDEBAR_FONT_SIZE = 10
SIDEBAR_ICON_SIZE = 10


# ============================================================
# FORMAT FIRESTORE DATES AND TIMESTAMPS
# ============================================================

def format_feedback_date(raw_date):
    """
    Convert Firestore timestamps, datetime objects, Unix
    timestamps, and common date strings into a readable date.

    Date and time format:
    14 Oct 2026 02:35 PM

    Date-only values remain date-only.
    """

    if raw_date is None or raw_date == "":
        return "Date unavailable"

    if isinstance(raw_date, datetime):
        return raw_date.strftime("%d %b %Y %I:%M %p")

    if isinstance(raw_date, date):
        return raw_date.strftime("%d %b %Y")

    if hasattr(raw_date, "to_datetime"):
        try:
            converted_date = raw_date.to_datetime()

            if isinstance(converted_date, datetime):
                return converted_date.strftime(
                    "%d %b %Y %I:%M %p"
                )

            if isinstance(converted_date, date):
                return converted_date.strftime("%d %b %Y")

        except (ValueError, TypeError, OverflowError):
            pass

    if isinstance(raw_date, dict):

        seconds = raw_date.get(
            "seconds",
            raw_date.get("_seconds")
        )

        if seconds is not None:
            try:
                timestamp_value = float(seconds)

                if abs(timestamp_value) > 100000000000:
                    timestamp_value /= 1000

                return datetime.fromtimestamp(
                    timestamp_value
                ).strftime("%d %b %Y %I:%M %p")

            except (
                ValueError,
                TypeError,
                OverflowError,
                OSError
            ):
                pass

    if isinstance(raw_date, (int, float)) and not isinstance(
        raw_date, bool
    ):
        try:
            timestamp_value = float(raw_date)

            if abs(timestamp_value) > 100000000000:
                timestamp_value /= 1000

            return datetime.fromtimestamp(
                timestamp_value
            ).strftime("%d %b %Y %I:%M %p")

        except (
            ValueError,
            TypeError,
            OverflowError,
            OSError
        ):
            return "Date unavailable"

    if isinstance(raw_date, str):

        date_text = raw_date.strip()

        if not date_text:
            return "Date unavailable"

        try:
            parsed_date = datetime.fromisoformat(
                date_text.replace("Z", "+00:00")
            )

            if "T" in date_text or " " in date_text:
                return parsed_date.strftime(
                    "%d %b %Y %I:%M %p"
                )

            return parsed_date.strftime("%d %b %Y")

        except (ValueError, TypeError):
            pass

        date_formats = [
            ("%d %b %Y %I:%M %p", True),
            ("%d %B %Y %I:%M %p", True),
            ("%Y-%m-%d %H:%M:%S", True),
            ("%Y-%m-%d %H:%M", True),
            ("%d %b %Y %H:%M:%S", True),
            ("%d %b %Y %H:%M", True),
            ("%d %B %Y %H:%M:%S", True),
            ("%d %B %Y %H:%M", True),
            ("%d %b %Y", False),
            ("%d %B %Y", False),
            ("%Y-%m-%d", False),
            ("%Y/%m/%d", False),
            ("%d-%m-%Y", False),
            ("%d/%m/%Y", False),
        ]

        for date_format, includes_time in date_formats:
            try:
                parsed_date = datetime.strptime(
                    date_text,
                    date_format
                )

                if includes_time:
                    return parsed_date.strftime(
                        "%d %b %Y %I:%M %p"
                    )

                return parsed_date.strftime("%d %b %Y")

            except ValueError:
                continue

        return "Date unavailable"

    return "Date unavailable"


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

    def draw(self):

        self.delete("all")

        r = min(
            self.radius,
            self.width / 2,
            self.height / 2
        )

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

    def on_click(self):

        if self.command:
            self.command()


# ============================================================
# MAIN APPLICATION
# ============================================================

class ViewFeedbackApp(tk.Tk):

    def __init__(self):

        super().__init__()

        # ====================================================
        # LOGGED-IN ADMIN UID
        # ====================================================

        self.user_uid = (
            sys.argv[1]
            if len(sys.argv) > 1
            else None
        )

        # ====================================================
        # WINDOW SETTINGS
        # Match my_feedback.py
        # ====================================================

        self.title("FeedbackTrack - View Feedback")
        self.geometry("1200x780")
        self.minsize(850, 620)
        self.configure(bg=BACKGROUND)
        self.resizable(True, True)

        self.child_process = None
        self.resize_job = None
        self.feedback_refresh_job = None

        # About window references.
        self.about_window = None
        self.about_app = None

        # Feedback detail popup references.
        self.feedback_detail_window = None
        self.feedback_detail_app = None

        # ====================================================
        # FEEDBACK DATA FROM FIRESTORE
        # ====================================================

        self.feedback_data = []

        # Prevent unnecessary table rebuilding.
        self._last_table_signature = None

        self.load_feedback(show_error=False)

        # ====================================================
        # BUILD THE PAGE
        # ====================================================

        self.create_header()
        self.create_main_card()
        self.create_footer()

        self.bind(
            "<Configure>",
            self.schedule_responsive_layout
        )

        self.after_idle(self.update_responsive_layout)

        self.schedule_feedback_refresh()

        self.protocol(
            "WM_DELETE_WINDOW",
            self.close_application
        )

    # ========================================================
    # HEADER
    # Match my_feedback.py
    # ========================================================

    def create_header(self):

        navbar = tk.Frame(self, bg=BACKGROUND)

        navbar.pack(
            fill="x",
            padx=40,
            pady=(18, 8)
        )

        self.navbar = navbar

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

        self.logo_icon.pack(
            side="left",
            padx=(0, 8)
        )

        self.logo_text = tk.Label(
            brand_frame,
            text="FeedbackTrack",
            font=("Segoe UI", 19, "bold"),
            fg=TEXT,
            bg=BACKGROUND
        )

        self.logo_text.pack(side="left")

    # ========================================================
    # MAIN WHITE CARD
    # ========================================================

    def create_main_card(self):

        card_outer = tk.Frame(self, bg=BACKGROUND)

        card_outer.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=(8, 10)
        )

        self.card_outer = card_outer

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

        self.create_sidebar()
        self.create_content()

    # ========================================================
    # SIDEBAR
    # Match my_feedback.py
    # ========================================================

    def create_sidebar(self):

        sidebar = tk.Frame(
            self.card,
            bg=LEFT_BACKGROUND,
            width=220,
            highlightthickness=1,
            highlightbackground=CARD_BORDER
        )

        sidebar.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        sidebar.grid_propagate(False)

        self.sidebar = sidebar

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

        self.create_sidebar_item(
            sidebar_content,
            icon="📁",
            text="View Feedback",
            selected=True
        )

        self.create_sidebar_item(
            sidebar_content,
            icon="⚙",
            text="Manage Status",
            command=self.on_manage_status
        )

        self.create_sidebar_item(
            sidebar_content,
            icon="👤",
            text="Admin Account",
            command=self.on_admin_account
        )

        self.create_sidebar_item(
            sidebar_content,
            icon="↪",
            text="Logout",
            command=self.on_logout
        )

    # ========================================================
    # SIDEBAR ITEM
    # ========================================================

    def create_sidebar_item(
        self,
        parent,
        icon,
        text,
        command=None,
        selected=False
    ):

        item_bg = PURPLE if selected else LEFT_BACKGROUND
        item_fg = WHITE if selected else TEXT_LIGHT

        item = tk.Frame(
            parent,
            bg=item_bg,
            cursor="hand2" if command else ""
        )

        item.pack(
            fill="x",
            pady=(0, 8)
        )

        icon_label = tk.Label(
            item,
            text=icon,
            font=("Segoe UI Emoji", SIDEBAR_ICON_SIZE),
            fg=item_fg,
            bg=item_bg,
            cursor="hand2" if command else ""
        )

        icon_label.pack(
            side="left",
            padx=(12, 7),
            pady=9
        )

        text_label = tk.Label(
            item,
            text=text,
            font=(
                "Segoe UI",
                SIDEBAR_FONT_SIZE,
                "bold" if selected else "normal"
            ),
            fg=item_fg,
            bg=item_bg,
            cursor="hand2" if command else ""
        )

        text_label.pack(
            side="left",
            pady=9
        )

        if command:

            for widget in (item, icon_label, text_label):

                widget.bind(
                    "<Button-1>",
                    lambda event, action=command: action()
                )

    # ========================================================
    # MAIN CONTENT
    # Match my_feedback.py spacing and fonts
    # ========================================================

    def create_content(self):

        main_area = tk.Frame(self.card, bg=WHITE)

        main_area.grid(
            row=0,
            column=1,
            sticky="nsew"
        )

        self.main_area = main_area

        content = tk.Frame(main_area, bg=WHITE)

        content.pack(
            fill="both",
            expand=True,
            padx=34,
            pady=32
        )

        self.content = content

        self.page_title = tk.Label(
            content,
            text="Feedback Tracker",
            font=("Segoe UI", 21, "bold"),
            fg=TEXT,
            bg=WHITE
        )

        self.page_title.pack(anchor="nw")

        self.subtitle = tk.Label(
            content,
            text="View and manage all submitted feedback.",
            font=("Segoe UI", 11),
            fg=TEXT_LIGHT,
            bg=WHITE
        )

        self.subtitle.pack(
            anchor="nw",
            pady=(4, 24)
        )

        self.create_filters()

        # ====================================================
        # SCROLLABLE TABLE AREA
        # ====================================================

        self.table_border = tk.Frame(
            content,
            bg=WHITE,
            highlightthickness=1,
            highlightbackground=BORDER,
            bd=0
        )

        self.table_border.pack(
            fill="both",
            expand=True,
            anchor="n"
        )

        self.table_canvas = tk.Canvas(
            self.table_border,
            bg=WHITE,
            highlightthickness=0,
            bd=0
        )

        self.table_scrollbar = ttk.Scrollbar(
            self.table_border,
            orient="vertical",
            command=self.table_canvas.yview
        )

        self.table_canvas.configure(
            yscrollcommand=self.table_scrollbar.set
        )

        self.table_scrollbar.pack(
            side="right",
            fill="y"
        )

        self.table_canvas.pack(
            side="left",
            fill="both",
            expand=True
        )

        self.table_inner = tk.Frame(
            self.table_canvas,
            bg=WHITE
        )

        self.table_window = self.table_canvas.create_window(
            (0, 0),
            window=self.table_inner,
            anchor="nw"
        )

        self.table_inner.bind(
            "<Configure>",
            self.update_table_scroll_region
        )

        self.table_canvas.bind(
            "<Configure>",
            self.resize_table_inner
        )

        self.table_canvas.bind(
            "<Enter>",
            self.bind_table_mousewheel
        )

        self.table_canvas.bind(
            "<Leave>",
            self.unbind_table_mousewheel
        )

        self.refresh_table()

    # ========================================================
    # FILTERS AND SEARCH
    # ========================================================

    def create_filters(self):

        filter_frame = tk.Frame(self.content, bg=WHITE)

        filter_frame.pack(
            fill="x",
            pady=(0, 18)
        )

        self.filter_frame = filter_frame

        self.category_var = tk.StringVar(
            value="All Categories"
        )

        self.category_filter = ttk.Combobox(
            filter_frame,
            textvariable=self.category_var,
            values=[
                "All Categories",
                "Academic",
                "Food",
                "Hostel",
                "Library",
                "Other"
            ],
            state="readonly",
            width=14,
            font=("Segoe UI", 9)
        )

        self.category_filter.pack(
            side="left",
            padx=(0, 10),
            ipady=5
        )

        self.category_filter.bind(
            "<<ComboboxSelected>>",
            lambda event: self.refresh_table()
        )

        self.status_var = tk.StringVar(
            value="All Status"
        )

        self.status_filter = ttk.Combobox(
            filter_frame,
            textvariable=self.status_var,
            values=[
                "All Status",
                "New",
                "Reviewed",
                "Resolved"
            ],
            state="readonly",
            width=13,
            font=("Segoe UI", 9)
        )

        self.status_filter.pack(
            side="left",
            padx=(0, 10),
            ipady=5
        )

        self.status_filter.bind(
            "<<ComboboxSelected>>",
            lambda event: self.refresh_table()
        )

        self.search_var = tk.StringVar()

        self.search_entry = tk.Entry(
            filter_frame,
            textvariable=self.search_var,
            font=("Segoe UI", 10),
            fg=TEXT_LIGHT,
            bg=WHITE,
            relief="solid",
            bd=1,
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=PURPLE
        )

        self.search_entry.pack(
            side="left",
            fill="x",
            expand=True,
            ipady=8
        )

        self.search_entry.insert(
            0,
            "Search feedback..."
        )

        self.search_entry.bind(
            "<FocusIn>",
            self.clear_search_hint
        )

        self.search_entry.bind(
            "<FocusOut>",
            self.restore_search_hint
        )

        self.search_var.trace_add(
            "write",
            lambda *args: self.refresh_table()
        )

    # ========================================================
    # SEARCH PLACEHOLDER
    # ========================================================

    def clear_search_hint(self, event=None):

        if self.search_var.get() == "Search feedback...":

            self.search_var.set("")
            self.search_entry.config(fg=TEXT)

    def restore_search_hint(self, event=None):

        if not self.search_var.get().strip():

            self.search_var.set("Search feedback...")
            self.search_entry.config(fg=TEXT_LIGHT)

    # ========================================================
    # SCROLLABLE TABLE HELPERS
    # ========================================================

    def update_table_scroll_region(self, event=None):

        if hasattr(self, "table_canvas"):
            self.table_canvas.configure(
                scrollregion=self.table_canvas.bbox("all")
            )

    def resize_table_inner(self, event):

        if hasattr(self, "table_window"):
            self.table_canvas.itemconfigure(
                self.table_window,
                width=event.width
            )

        if hasattr(self, "table_inner"):
            self.update_table_scroll_region()

    def on_table_mousewheel(self, event):

        if event.delta:
            self.table_canvas.yview_scroll(
                int(-1 * (event.delta / 120)),
                "units"
            )

    def on_table_mousewheel_linux(self, event):

        if event.num == 4:
            self.table_canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.table_canvas.yview_scroll(1, "units")

    def bind_table_mousewheel(self, event=None):

        self.table_canvas.bind_all(
            "<MouseWheel>",
            self.on_table_mousewheel
        )

        self.table_canvas.bind_all(
            "<Button-4>",
            self.on_table_mousewheel_linux
        )

        self.table_canvas.bind_all(
            "<Button-5>",
            self.on_table_mousewheel_linux
        )

    def unbind_table_mousewheel(self, event=None):

        self.table_canvas.unbind_all("<MouseWheel>")
        self.table_canvas.unbind_all("<Button-4>")
        self.table_canvas.unbind_all("<Button-5>")

    # ========================================================
    # RESPONSIVE TABLE COLUMN WIDTHS
    # ========================================================

    def get_table_column_widths(self):

        window_width = self.winfo_width()

        if window_width < 200:
            window_width = 1200

        if window_width < 950:

            return {
                0: 28,
                1: 58,
                2: 82,
                3: 1,
                4: 78,
                5: 86,
                6: 88
            }

        elif window_width < 1200:

            return {
                0: 32,
                1: 68,
                2: 90,
                3: 1,
                4: 88,
                5: 95,
                6: 95
            }

        else:

            return {
                0: 38,
                1: 80,
                2: 120,
                3: 1,
                4: 115,
                5: 120,
                6: 105
            }

    # ========================================================
    # LOAD FEEDBACK FROM FIRESTORE
    # ========================================================

    def load_feedback(self, show_error=True):
        """Load feedback records from Firestore."""

        if db is None:
            self.feedback_data = []

            if show_error:
                messagebox.showerror(
                    "Database Not Available",
                    "Feedback couldn't be loaded because the database "
                    "connection isn't available. Please check the "
                    "Firebase setup or contact the administrator."
                )

            return False

        try:
            records = []

            for document in db.collection("feedback").stream():

                data = document.to_dict() or {}

                raw_date = data.get("created_at")

                if raw_date is None or raw_date == "":
                    raw_date = data.get("timestamp")

                if raw_date is None or raw_date == "":
                    raw_date = data.get("submitted_at")

                if raw_date is None or raw_date == "":
                    raw_date = data.get("date")

                date_text = format_feedback_date(raw_date)

                records.append({
                    "id": document.id,
                    "name": str(data.get("name", "Anonymous")),
                    "category": str(data.get("category", "Other")),
                    "feedback": str(data.get("feedback", "")),
                    "status": str(data.get("status", "New")),
                    "date": date_text
                })

            self.feedback_data = records

            return True

        except Exception as error:
            print("Feedback load error:", repr(error))
            self.feedback_data = []

            if show_error:
                messagebox.showerror(
                    "Unable to Load Feedback",
                    "We couldn't load feedback from the database. "
                    "Please check your internet connection and try "
                    "again. If the problem continues, contact the "
                    "administrator."
                )

            return False

    # ========================================================
    # AUTOMATIC DATABASE REFRESH
    # ========================================================

    def schedule_feedback_refresh(self):

        if self.winfo_exists():
            self.feedback_refresh_job = self.after(
                5000,
                self.refresh_feedback_from_database
            )

    def refresh_feedback_from_database(self):

        self.feedback_refresh_job = None

        if not self.winfo_exists():
            return

        if self.load_feedback(show_error=False):
            self.refresh_table()

        self.schedule_feedback_refresh()

    # ========================================================
    # REFRESH TABLE
    # Avoid unnecessary rebuilding and preserve scrolling.
    # ========================================================

    def refresh_table(self):

        if not hasattr(self, "table_inner"):
            return

        category_selected = self.category_var.get()
        status_selected = self.status_var.get()
        search_text = self.search_var.get().strip().lower()

        if search_text == "search feedback...":
            search_text = ""

        filtered_data = []

        for index, item in enumerate(self.feedback_data):

            if (
                category_selected != "All Categories"
                and item["category"] != category_selected
            ):
                continue

            if (
                status_selected != "All Status"
                and item["status"] != status_selected
            ):
                continue

            searchable_text = (
                item["name"] + " " +
                item["category"] + " " +
                item["feedback"] + " " +
                item["status"] + " " +
                item["date"]
            ).lower()

            if search_text and search_text not in searchable_text:
                continue

            filtered_data.append((index, item))

        column_widths = self.get_table_column_widths()
        narrow_layout = self.winfo_width() < 950

        # A signature identifies the data and layout currently displayed.
        # The five-second refresh will not rebuild unchanged rows.
        table_signature = (
            tuple(
                (
                    data_index,
                    item["id"],
                    item["name"],
                    item["category"],
                    item["feedback"],
                    item["status"],
                    item["date"]
                )
                for data_index, item in filtered_data
            ),
            category_selected,
            status_selected,
            search_text,
            tuple(sorted(column_widths.items())),
            narrow_layout
        )

        if table_signature == self._last_table_signature:
            return

        # Remember the scrollbar position before rebuilding.
        try:
            scroll_position = self.table_canvas.yview()[0]
        except (tk.TclError, IndexError):
            scroll_position = 0.0

        self._last_table_signature = table_signature

        for widget in self.table_inner.winfo_children():
            widget.destroy()

        table = tk.Frame(
            self.table_inner,
            bg=WHITE
        )

        table.pack(
            fill="x",
            expand=True
        )

        for column, width in column_widths.items():

            table.grid_columnconfigure(
                column,
                minsize=width,
                weight=1 if column == 3 else 0
            )

        headings = [
            "#",
            "NAME",
            "CATEGORY",
            "FEEDBACK",
            "STATUS",
            "DATE",
            "ACTIONS"
        ]

        # ----------------------------------------------------
        # TABLE HEADER
        # ----------------------------------------------------

        for column, heading in enumerate(headings):

            header_label = tk.Label(
                table,
                text=heading,
                font=("Segoe UI", 9, "bold"),
                fg=TEXT_LIGHT,
                bg=PURPLE_LIGHT,
                anchor="w",
                padx=5 if narrow_layout else 10,
                pady=12
            )

            header_label.grid(
                row=0,
                column=column,
                sticky="nsew"
            )

        tk.Frame(
            table,
            bg=BORDER,
            height=1
        ).grid(
            row=1,
            column=0,
            columnspan=7,
            sticky="ew"
        )

        if not filtered_data:

            tk.Label(
                table,
                text="No feedback found.",
                font=("Segoe UI", 11),
                fg=TEXT_LIGHT,
                bg=WHITE
            ).grid(
                row=2,
                column=0,
                columnspan=7,
                sticky="ew",
                pady=25
            )

            self.table_inner.update_idletasks()
            self.update_table_scroll_region()

            # Restore the position when possible.
            self.after_idle(
                lambda position=scroll_position:
                self.restore_table_scroll(position)
            )

            return

        # ----------------------------------------------------
        # FEEDBACK ROWS
        # ----------------------------------------------------

        for row_index, (data_index, item) in enumerate(filtered_data):

            data_row = 2 + row_index * 2
            row_padding = 5 if narrow_layout else 10

            # Row number.
            tk.Label(
                table,
                text=str(row_index + 1),
                font=("Segoe UI", 9),
                fg=TEXT,
                bg=WHITE,
                anchor="w"
            ).grid(
                row=data_row,
                column=0,
                sticky="ew",
                padx=row_padding,
                pady=12
            )

            # Student name.
            tk.Label(
                table,
                text=item["name"],
                font=("Segoe UI", 10),
                fg=TEXT,
                bg=WHITE,
                anchor="w"
            ).grid(
                row=data_row,
                column=1,
                sticky="ew",
                padx=row_padding,
                pady=12
            )

            # Category badge.
            tk.Label(
                table,
                text=item["category"],
                font=("Segoe UI", 9, "bold"),
                fg=PURPLE_DARK,
                bg=PURPLE_LIGHT,
                padx=5 if narrow_layout else 8,
                pady=4
            ).grid(
                row=data_row,
                column=2,
                sticky="w",
                padx=row_padding,
                pady=11
            )

            # Shorten long feedback so the table stays organized.
            feedback_text = item["feedback"]

            if len(feedback_text) > 30:
                feedback_text = feedback_text[:27] + "..."

            tk.Label(
                table,
                text=feedback_text,
                font=("Segoe UI", 10),
                fg=TEXT,
                bg=WHITE,
                anchor="w"
            ).grid(
                row=data_row,
                column=3,
                sticky="ew",
                padx=row_padding,
                pady=12
            )

            # Status colours.
            status_colors = {
                "New": ("#E9EDFF", "#526DFF"),
                "Reviewed": ("#FFF3D6", "#B9820C"),
                "Resolved": ("#DFF5EB", "#15956A")
            }

            status_bg, status_fg = status_colors.get(
                item["status"],
                (PURPLE_LIGHT, PURPLE_DARK)
            )

            tk.Label(
                table,
                text=item["status"],
                font=("Segoe UI", 9, "bold"),
                fg=status_fg,
                bg=status_bg,
                padx=5 if narrow_layout else 9,
                pady=4
            ).grid(
                row=data_row,
                column=4,
                sticky="w",
                padx=row_padding,
                pady=11
            )

            # Date and time.
            tk.Label(
                table,
                text=item["date"],
                font=("Segoe UI", 9),
                fg=TEXT_LIGHT,
                bg=WHITE,
                anchor="w"
            ).grid(
                row=data_row,
                column=5,
                sticky="ew",
                padx=row_padding,
                pady=12
            )

            # Actions.
            actions = tk.Frame(
                table,
                bg=WHITE
            )

            actions.grid(
                row=data_row,
                column=6,
                sticky="w",
                padx=2 if narrow_layout else 5,
                pady=9
            )

            # View button.
            tk.Button(
                actions,
                text="👁",
                font=("Segoe UI Emoji", 10),
                bg=WHITE,
                fg=TEXT,
                activebackground=WHITE,
                relief="flat",
                bd=0,
                cursor="hand2",
                padx=1 if narrow_layout else 3,
                command=lambda i=data_index: self.view_feedback(i)
            ).pack(side="left", padx=1)

            # Edit button opens the Manage Status page.
            tk.Button(
                actions,
                text="🖊",
                font=("Segoe UI Emoji", 10),
                bg=WHITE,
                fg="#FF765E",
                activebackground=WHITE,
                relief="flat",
                bd=0,
                cursor="hand2",
                padx=1 if narrow_layout else 3,
                command=self.on_manage_status
            ).pack(side="left", padx=1)

            # Delete button.
            tk.Button(
                actions,
                text="🗑️",
                font=("Segoe UI Emoji", 10),
                bg=WHITE,
                fg="#A7A3B3",
                activebackground=WHITE,
                relief="flat",
                bd=0,
                cursor="hand2",
                padx=1 if narrow_layout else 3,
                command=lambda i=data_index: self.delete_feedback(i)
            ).pack(side="left", padx=1)

            # Separator underneath each row.
            tk.Frame(
                table,
                bg=BORDER,
                height=1
            ).grid(
                row=data_row + 1,
                column=0,
                columnspan=7,
                sticky="ew"
            )

        self.table_inner.update_idletasks()
        self.update_table_scroll_region()

        # Restore the previous scrollbar position after layout settles.
        self.after_idle(
            lambda position=scroll_position:
            self.restore_table_scroll(position)
        )

    def restore_table_scroll(self, position):

        try:
            if self.winfo_exists():
                self.update_table_scroll_region()
                self.table_canvas.yview_moveto(position)
        except tk.TclError:
            pass

    # ========================================================
    # RESPONSIVE LAYOUT - SCHEDULE UPDATE
    # ========================================================

    def schedule_responsive_layout(self, event=None):

        if event is not None and event.widget is not self:
            return

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
    # RESPONSIVE LAYOUT - UPDATE
    # Match my_feedback.py
    # ========================================================

    def update_responsive_layout(self):

        self.resize_job = None

        if not self.winfo_exists():
            return

        window_width = self.winfo_width()
        window_height = self.winfo_height()

        if window_width < 200:
            return

        # ----------------------------------------------------
        # 1. NAVBAR AND LOGO
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
        # 2. MAIN CARD MARGINS
        # ----------------------------------------------------

        outer_padding = 16 if window_width < 850 else 30

        self.card_outer.pack_configure(
            padx=outer_padding
        )

        # ----------------------------------------------------
        # 3. SIDEBAR SIZE AND PADDING
        # ----------------------------------------------------

        if window_width < 950:
            sidebar_width = 190
            sidebar_padding = 10
        else:
            sidebar_width = 220
            sidebar_padding = 14

        self.sidebar.config(
            width=sidebar_width
        )

        self.sidebar_content.pack_configure(
            padx=sidebar_padding
        )

        # Keep sidebar font sizes consistent.
        for widget in self.sidebar_content.winfo_children():

            for child in widget.winfo_children():

                if not isinstance(child, tk.Label):
                    continue

                if child.cget("text") in (
                    "View Feedback",
                    "Manage Status",
                    "Admin Account",
                    "Logout"
                ):

                    is_selected = child.cget("bg") == PURPLE

                    child.config(
                        font=(
                            "Segoe UI",
                            SIDEBAR_FONT_SIZE,
                            "bold" if is_selected else "normal"
                        )
                    )

                elif child.cget("text") in ("📁", "⚙", "👤", "↪"):

                    child.config(
                        font=(
                            "Segoe UI Emoji",
                            SIDEBAR_ICON_SIZE
                        )
                    )

        # ----------------------------------------------------
        # 4. MAIN CONTENT SPACING
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # 5. TITLE AND SUBTITLE
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

        self.subtitle.config(
            font=("Segoe UI", 11)
        )

        self.subtitle.pack_configure(
            pady=(4, subtitle_gap)
        )

        # ----------------------------------------------------
        # 6. FILTER SPACING
        # ----------------------------------------------------

        filter_bottom_padding = (
            12 if window_width < 950 else 18
        )

        self.filter_frame.pack_configure(
            pady=(0, filter_bottom_padding)
        )

                # ----------------------------------------------------
        # 7. FOOTER
        # ----------------------------------------------------

        footer_font_size = 10

        self.footer_text.config(
            font=("Segoe UI", footer_font_size)
        )

        for widget in self.footer.winfo_children():
            if widget.cget("text") == "About":
                widget.config(
                    font=("Segoe UI", 10, "bold")
                )

        # Refresh only if the table's data or column layout changed.
        self.refresh_table()
        self.update_table_scroll_region()

    # ========================================================
    # VIEW FEEDBACK
    # Opens the existing feedback_detail.py page on top.
    # Keeps View Feedback open underneath.
    # ========================================================

    def view_feedback(self, index):

        item = self.feedback_data[index]

        # If the detail popup is already open, bring it forward.
        if self.feedback_detail_window is not None:

            try:
                if self.feedback_detail_window.winfo_exists():
                    self.feedback_detail_window.lift()
                    self.feedback_detail_window.attributes(
                        "-topmost", True
                    )
                    self.feedback_detail_window.focus_force()
                    return

            except tk.TclError:
                pass

        self.feedback_detail_window = None
        self.feedback_detail_app = None

        try:

            from feedback_detail import FeedbackDetailPage

            detail_window = tk.Toplevel(self)
            self.feedback_detail_window = detail_window

            detail_window.transient(self)

            # The existing detail page reads the selected document
            # ID from sys.argv[1], so temporarily supply that ID.
            original_argv = sys.argv[:]

            try:

                if len(sys.argv) > 1:
                    sys.argv[1] = item["id"]
                else:
                    sys.argv.append(item["id"])

                self.feedback_detail_app = FeedbackDetailPage(
                    detail_window
                )

            finally:

                sys.argv[:] = original_argv

            detail_window.lift()
            detail_window.attributes("-topmost", True)
            detail_window.focus_force()

            detail_window.bind(
                "<Destroy>",
                self.on_feedback_detail_destroy,
                add="+"
            )

        except Exception as error:

            if self.feedback_detail_window is not None:

                try:
                    if self.feedback_detail_window.winfo_exists():
                        self.feedback_detail_window.destroy()

                except tk.TclError:
                    pass

            self.feedback_detail_window = None
            self.feedback_detail_app = None

            messagebox.showerror(
                "Feedback Detail Error",
                f"Could not open the feedback details.\n\n{error}",
                parent=self
            )

    def on_feedback_detail_destroy(self, event=None):

        if (
            event is not None
            and self.feedback_detail_window is not None
            and event.widget is self.feedback_detail_window
        ):
            self.feedback_detail_window = None
            self.feedback_detail_app = None

    # ========================================================
    # EDIT FEEDBACK
    # ========================================================

    def edit_feedback(self, index):

        item = self.feedback_data[index]

        edit_window = tk.Toplevel(self)
        edit_window.title("Edit Feedback")
        edit_window.geometry("380x330")
        edit_window.resizable(False, False)
        edit_window.configure(bg=WHITE)
        edit_window.transient(self)
        edit_window.grab_set()

        tk.Label(
            edit_window,
            text="Edit Feedback",
            font=("Segoe UI", 15, "bold"),
            fg=TEXT,
            bg=WHITE
        ).pack(
            anchor="w",
            padx=24,
            pady=(22, 12)
        )

        tk.Label(
            edit_window,
            text=f"Student: {item['name']}",
            font=("Segoe UI", 10),
            fg=TEXT_LIGHT,
            bg=WHITE
        ).pack(
            anchor="w",
            padx=24,
            pady=4
        )

        tk.Label(
            edit_window,
            text="Feedback:",
            font=("Segoe UI", 9, "bold"),
            fg=TEXT,
            bg=WHITE
        ).pack(
            anchor="w",
            padx=24,
            pady=(12, 4)
        )

        tk.Label(
            edit_window,
            text=item["feedback"],
            font=("Segoe UI", 9),
            fg=TEXT_LIGHT,
            bg=WHITE,
            wraplength=320,
            justify="left"
        ).pack(
            anchor="w",
            padx=24
        )

        tk.Label(
            edit_window,
            text="Update Status:",
            font=("Segoe UI", 9, "bold"),
            fg=TEXT,
            bg=WHITE
        ).pack(
            anchor="w",
            padx=24,
            pady=(14, 5)
        )

        status_var = tk.StringVar(
            value=item["status"]
        )

        ttk.Combobox(
            edit_window,
            textvariable=status_var,
            values=["New", "Reviewed", "Resolved"],
            state="readonly",
            font=("Segoe UI", 9),
            width=22
        ).pack(
            anchor="w",
            padx=24
        )

        def save_status():

            new_status = status_var.get()

            if db is None:
                messagebox.showerror(
                    "Status Not Saved",
                    "The database connection isn't available, "
                    "so this change wasn't saved.",
                    parent=edit_window
                )
                return

            try:
                db.collection("feedback").document(item["id"]).update(
                    {"status": new_status}
                )

                self.feedback_data[index]["status"] = new_status

                # Invalidate the table signature because the status changed.
                self._last_table_signature = None

                self.refresh_table()
                edit_window.destroy()

                messagebox.showinfo(
                    "Status Updated",
                    "The feedback status has been saved.",
                    parent=self
                )

            except Exception as error:
                print("Status update error:", repr(error))

                messagebox.showerror(
                    "Unable to Update Status",
                    "We couldn't save this status change. Please "
                    "check your internet connection and try again.",
                    parent=edit_window
                )

        RoundedButton(
            edit_window,
            text="Save Changes",
            width=135,
            height=38,
            bg_color=PURPLE,
            fg_color=WHITE,
            command=save_status
        ).pack(
            anchor="w",
            padx=24,
            pady=20
        )

    # ========================================================
    # DELETE FEEDBACK
    # ========================================================

    def delete_feedback(self, index):

        item = self.feedback_data[index]

        answer = messagebox.askyesno(
            "Delete Feedback",
            f"Are you sure you want to delete the feedback "
            f"submitted by {item['name']}?",
            parent=self
        )

        if answer:

            if db is None:
                messagebox.showerror(
                    "Feedback Not Deleted",
                    "The database connection isn't available, "
                    "so this feedback was not deleted.",
                    parent=self
                )
                return

            try:
                db.collection("feedback").document(item["id"]).delete()

                self.feedback_data.pop(index)

                # Invalidate the signature because a record was removed.
                self._last_table_signature = None

                self.refresh_table()

                messagebox.showinfo(
                    "Feedback Deleted",
                    "The feedback was deleted successfully.",
                    parent=self
                )

            except Exception as error:
                print("Feedback delete error:", repr(error))

                messagebox.showerror(
                    "Unable to Delete Feedback",
                    "We couldn't delete this feedback. Please "
                    "check your internet connection and try again.",
                    parent=self
                )

    # ========================================================
    # FOOTER
    # Match my_feedback.py
    # ========================================================

    def create_footer(self):

        footer = tk.Frame(
            self,
            bg=BACKGROUND
        )

        footer.pack(
            side="bottom",
            pady=(0, 12)
        )

        self.footer = footer

        self.footer_text = tk.Label(
            footer,
            text="© 2026 FeedbackTrack · Made for Student Voices   ",
            font=("Segoe UI", 9),
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

    # ========================================================
    # OPEN ANOTHER PAGE
    # ========================================================

    def open_page(self, filename, user_uid=None):

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
                "in the same folder.",
                parent=self
            )

            return

        try:

            command = [sys.executable, page_path]

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

            self.deiconify()
            self.lift()
            self.focus_force()

            messagebox.showerror(
                "Navigation Error",
                f"Could not open {filename}.\n\n{error}",
                parent=self
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

            self.deiconify()
            self.lift()
            self.focus_force()

            self.after_idle(
                self.update_responsive_layout
            )

        else:

            self.after(
                200,
                self.check_child_process
            )

    # ========================================================
    # SIDEBAR NAVIGATION
    # ========================================================

    def on_manage_status(self):

        self.open_page(
            "manage_status.py",
            user_uid=self.user_uid
        )

    def on_admin_account(self):

        self.open_page(
            "admin_account.py",
            user_uid=self.user_uid
        )

    def on_logout(self):

        answer = messagebox.askyesno(
            "Logout",
            "Are you sure you want to logout?",
            parent=self
        )

        if answer:
            self.open_page("homepage.py")

    # ========================================================
    # ABOUT WINDOW
    # Opens About above View Feedback without hiding this page.
    # Uses the existing AboutPage from about.py.
    # ========================================================

    def on_about(self):

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

    def on_about_destroy(self, event=None):

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

        # Cancel automatic database refresh.
        if self.feedback_refresh_job is not None:

            try:
                self.after_cancel(self.feedback_refresh_job)
            except tk.TclError:
                pass

        # Cancel pending resize update.
        if self.resize_job is not None:

            try:
                self.after_cancel(self.resize_job)
            except tk.TclError:
                pass

        # Close About if it is still open.
        if self.about_window is not None:

            try:
                if self.about_window.winfo_exists():
                    self.about_window.destroy()
            except tk.TclError:
                pass

        self.about_window = None
        self.about_app = None

        # Close the feedback detail popup if it is still open.
        if self.feedback_detail_window is not None:

            try:
                if self.feedback_detail_window.winfo_exists():
                    self.feedback_detail_window.destroy()
            except tk.TclError:
                pass

        self.feedback_detail_window = None
        self.feedback_detail_app = None

        # Remove mouse-wheel bindings.
        try:
            self.table_canvas.unbind_all("<MouseWheel>")
            self.table_canvas.unbind_all("<Button-4>")
            self.table_canvas.unbind_all("<Button-5>")
        except tk.TclError:
            pass

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

    app = ViewFeedbackApp()
    app.mainloop()
