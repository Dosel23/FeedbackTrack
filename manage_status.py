import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import os
from datetime import datetime

# Use the existing Firebase connection.
try:
    from firebase_config import db
    FIREBASE_IMPORT_ERROR = None
except Exception as error:
    db = None
    FIREBASE_IMPORT_ERROR = error


# ============================================================
# FeedbackTrack - Manage Status Page
# Responsive layout with scrollable content
# Firebase-backed feedback, status updates, and conversations
# Styling matched with view_feedback.py
# ============================================================

# ------------------------- COLORS ---------------------------

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

STATUS_COLORS = {
    "New": ("#E9EDFF", "#526DFF"),
    "Reviewed": ("#FFF3D6", "#B9820C"),
    "Resolved": ("#DFF5EB", "#15956A"),
}

# Match the sidebar settings in view_feedback.py.
SIDEBAR_FONT_SIZE = 10
SIDEBAR_ICON_SIZE = 10


# ============================================================
# REUSABLE ROUNDED BUTTON
# ============================================================

class RoundedButton(tk.Canvas):
    """Canvas-based button that can be resized responsively."""

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

    def draw(self):
        """Redraw the rounded button."""

        self.delete("all")

        r = min(self.radius, self.width / 2, self.height / 2)
        w, h = self.width, self.height

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
        """Resize the button."""

        width, height = max(1, int(width)), max(1, int(height))

        if self.width == width and self.height == height:
            return

        self.width, self.height = width, height
        self.config(width=width, height=height)
        self.draw()

    def create_rounded_rectangle(self, x1, y1, x2, y2, radius, **kwargs):
        """Create a rounded rectangle using a smooth polygon."""

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

        return self.create_polygon(points, smooth=True, **kwargs)

    def on_click(self):
        """Run the button callback."""

        if self.command:
            self.command()


# ============================================================
# MAIN APPLICATION
# ============================================================

class ManageStatusApp(tk.Tk):

    def __init__(self):
        super().__init__()

        # Read the logged-in admin UID.
        self.user_uid = (
            sys.argv[1].strip()
            if len(sys.argv) > 1 and sys.argv[1].strip()
            else os.environ.get("FEEDBACKTRACK_ADMIN_UID", "").strip()
        )

        if not self.user_uid:
            self.user_uid = None
        else:
            os.environ["FEEDBACKTRACK_ADMIN_UID"] = self.user_uid

        print("Manage Status - Admin UID:", repr(self.user_uid))

        # Match view_feedback.py window settings.
        self.title("FeedbackTrack - Manage Status")
        self.geometry("1200x780")
        self.minsize(850, 620)
        self.configure(bg=BACKGROUND)
        self.resizable(True, True)

        self.child_process = None
        self.resize_job = None

        # Keep track of the About window and its application.
        self.about_window = None
        self.about_app = None

        self.current_window_width = 1200
        self.current_window_height = 780

        # Match view_feedback.py content spacing at standard size.
        self.content_pad_x = 34
        self.content_pad_y = 32

        self.status_buttons = {}
        self.feedback_data = []

        self.create_header()
        self.create_main_card()
        self.create_footer()

        self.bind("<Configure>", self.schedule_responsive_layout)
        self.after_idle(self.update_responsive_layout)

        self.protocol("WM_DELETE_WINDOW", self.close_application)

        self.load_feedback(show_error=True)

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    def create_header(self):
        # Match view_feedback.py header spacing.
        self.navbar = tk.Frame(self, bg=BACKGROUND)
        self.navbar.pack(fill="x", padx=40, pady=(18, 8))

        brand_frame = tk.Frame(self.navbar, bg=BACKGROUND)
        brand_frame.pack(side="left")

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

    # --------------------------------------------------------
    # MAIN CARD AND SIDEBAR
    # --------------------------------------------------------

    def create_main_card(self):
        self.card_outer = tk.Frame(self, bg=BACKGROUND)
        self.card_outer.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=(8, 10)
        )

        self.card = tk.Frame(
            self.card_outer,
            bg=WHITE,
            highlightthickness=1,
            highlightbackground=CARD_BORDER
        )
        self.card.pack(fill="both", expand=True)

        self.card.grid_columnconfigure(0, weight=0)
        self.card.grid_columnconfigure(1, weight=1)
        self.card.grid_rowconfigure(0, weight=1)

        self.create_sidebar()
        self.create_content()

    def create_sidebar(self):
        """Create sidebar navigation matching view_feedback.py."""

        self.sidebar = tk.Frame(
            self.card,
            bg=LEFT_BACKGROUND,
            width=220,
            highlightthickness=1,
            highlightbackground=CARD_BORDER
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        self.sidebar_content = tk.Frame(
            self.sidebar,
            bg=LEFT_BACKGROUND
        )
        self.sidebar_content.pack(fill="x", padx=14, pady=22)

        self.create_sidebar_item(
            self.sidebar_content,
            "📁",
            "View Feedback",
            command=self.on_view_feedback
        )

        self.create_sidebar_item(
            self.sidebar_content,
            "⚙",
            "Manage Status",
            selected=True
        )

        self.create_sidebar_item(
            self.sidebar_content,
            "👤",
            "Admin Account",
            command=self.on_admin_account
        )

        self.create_sidebar_item(
            self.sidebar_content,
            "↪",
            "Logout",
            command=self.on_logout
        )

    def create_sidebar_item(
        self,
        parent,
        icon,
        text,
        command=None,
        selected=False
    ):
        """Create one clickable sidebar item."""

        item_bg = PURPLE if selected else LEFT_BACKGROUND
        item_fg = WHITE if selected else TEXT_LIGHT

        item = tk.Frame(
            parent,
            bg=item_bg,
            cursor="hand2" if command else ""
        )
        item.pack(fill="x", pady=(0, 8))

        icon_label = tk.Label(
            item,
            text=icon,
            font=("Segoe UI Emoji", SIDEBAR_ICON_SIZE),
            fg=item_fg,
            bg=item_bg,
            cursor="hand2" if command else ""
        )
        icon_label.pack(side="left", padx=(12, 7), pady=9)

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
        text_label.pack(side="left", pady=9)

        if command:
            for widget in (item, icon_label, text_label):
                widget.bind(
                    "<Button-1>",
                    lambda event, action=command: action()
                )

    # --------------------------------------------------------
    # SCROLLABLE CONTENT
    # --------------------------------------------------------

    def create_content(self):
        self.main_area = tk.Frame(self.card, bg=WHITE)

        # EXTRA GAP: separate the content area from the sidebar.
        self.main_area.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(8, 0)
        )

        self.content_canvas = tk.Canvas(
            self.main_area,
            bg=WHITE,
            highlightthickness=0,
            bd=0
        )

        self.content_scrollbar = ttk.Scrollbar(
            self.main_area,
            orient="vertical",
            command=self.content_canvas.yview
        )

        self.content_canvas.configure(
            yscrollcommand=self.content_scrollbar.set
        )

        self.content_scrollbar.pack(side="right", fill="y")
        self.content_canvas.pack(side="left", fill="both", expand=True)

        self.content = tk.Frame(self.content_canvas, bg=WHITE)

        self.content_window = self.content_canvas.create_window(
            (self.content_pad_x, self.content_pad_y),
            window=self.content,
            anchor="nw"
        )

        self.content.bind("<Configure>", self.update_scroll_region)

        self.content_canvas.bind(
            "<Configure>",
            self.resize_content_window
        )

        self.content_canvas.bind("<Enter>", self.bind_mousewheel)
        self.content_canvas.bind("<Leave>", self.unbind_mousewheel)
        self.content.bind("<Enter>", self.bind_mousewheel)
        self.content.bind("<Leave>", self.unbind_mousewheel)

        # Match view_feedback.py title and subtitle sizes.
        self.page_title = tk.Label(
            self.content,
            text="Manage Status",
            font=("Segoe UI", 21, "bold"),
            fg=TEXT,
            bg=WHITE
        )
        self.page_title.pack(anchor="nw")

        self.subtitle = tk.Label(
            self.content,
            text="Update the status of submitted student feedback.",
            font=("Segoe UI", 11),
            fg=TEXT_LIGHT,
            bg=WHITE
        )
        self.subtitle.pack(anchor="nw", pady=(4, 24))

        self.cards_frame = tk.Frame(self.content, bg=WHITE)
        self.cards_frame.pack(fill="x", anchor="n")

    def update_scroll_region(self, event=None):
        """Include the complete content frame in the scroll area."""

        if (
            hasattr(self, "content_canvas")
            and self.content_canvas.winfo_exists()
        ):
            self.content_canvas.configure(
                scrollregion=self.content_canvas.bbox("all")
            )

    def resize_content_window(self, event):
        """Resize the embedded frame while keeping responsive margins."""

        if event.width <= 0:
            return

        available_width = max(
            1,
            event.width - (2 * self.content_pad_x)
        )

        self.content_canvas.coords(
            self.content_window,
            self.content_pad_x,
            self.content_pad_y
        )

        self.content_canvas.itemconfigure(
            self.content_window,
            width=available_width
        )

        self.after_idle(self.update_scroll_region)

    def bind_mousewheel(self, event=None):
        """Enable mouse-wheel scrolling."""

        self.bind_all("<MouseWheel>", self.on_mousewheel)
        self.bind_all("<Button-4>", self.on_mousewheel_linux)
        self.bind_all("<Button-5>", self.on_mousewheel_linux)

    def unbind_mousewheel(self, event=None):
        """Remove mouse-wheel bindings."""

        self.unbind_all("<MouseWheel>")
        self.unbind_all("<Button-4>")
        self.unbind_all("<Button-5>")

    def on_mousewheel(self, event):
        """Handle Windows and macOS mouse-wheel events."""

        if self.content_canvas.winfo_exists():
            self.content_canvas.yview_scroll(
                int(-1 * (event.delta / 120)),
                "units"
            )

    def on_mousewheel_linux(self, event):
        """Handle Linux mouse-wheel events."""

        if event.num == 4:
            self.content_canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.content_canvas.yview_scroll(1, "units")

    # --------------------------------------------------------
    # REPLY FORMATTING
    # --------------------------------------------------------

    @staticmethod
    def format_reply_date(reply):
        """
        Display reply dates using a 12-hour clock with AM/PM.
        """

        date_value = reply.get("created_at") or reply.get("date") or ""

        if not date_value:
            return ""

        # Firestore Timestamp or Python datetime.
        if hasattr(date_value, "strftime"):
            try:
                return date_value.strftime("%d %b %Y %I:%M %p")
            except (ValueError, TypeError, AttributeError):
                pass

        date_text = str(date_value).strip()

        if not date_text:
            return ""

        # Convert ISO timestamps into a readable AM/PM date.
        try:
            iso_text = date_text

            if iso_text.endswith("Z"):
                iso_text = iso_text[:-1] + "+00:00"

            parsed_date = datetime.fromisoformat(iso_text)

            if "T" in date_text or " " in date_text:
                return parsed_date.strftime("%d %b %Y %I:%M %p")

            return parsed_date.strftime("%d %b %Y")

        except (ValueError, TypeError, OverflowError):
            pass

        formats = [
            "%d %b %Y %I:%M:%S %p",
            "%d %b %Y %I:%M %p",
            "%d %b %Y %H:%M:%S",
            "%d %b %Y %H:%M",
            "%d %b %Y",
            "%Y-%m-%d %I:%M:%S %p",
            "%Y-%m-%d %I:%M %p",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%d/%m/%Y %I:%M:%S %p",
            "%d/%m/%Y %I:%M %p",
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y %H:%M",
            "%d/%m/%Y"
        ]

        for date_format in formats:
            try:
                parsed_date = datetime.strptime(
                    date_text,
                    date_format
                )

                if "%H" in date_format or "%I" in date_format:
                    return parsed_date.strftime("%d %b %Y %I:%M %p")

                return parsed_date.strftime("%d %b %Y")

            except ValueError:
                continue

        if "T" in date_text and len(date_text) >= 16:
            try:
                parsed_date = datetime.strptime(
                    date_text[:16],
                    "%Y-%m-%dT%H:%M"
                )
                return parsed_date.strftime("%d %b %Y %I:%M %p")
            except ValueError:
                pass

        return date_text

    @staticmethod
    def get_reply_text(reply):
        """Support both message and text fields."""

        return str(
            reply.get("message")
            or reply.get("text")
            or ""
        ).strip()

    @staticmethod
    def get_reply_sender(reply, student_name):
        """Display student replies using the student's name or Anonymous."""

        sender_value = (
            reply.get("sender")
            or reply.get("role")
            or ""
        )

        sender = str(sender_value).strip().lower()

        if (
            sender in (
                "admin",
                "administrator",
                "staff",
                "moderator",
                "admin_reply",
                "admin_reply_message"
            )
            or sender.startswith("admin ")
            or sender.startswith("admin·")
            or sender.startswith("admin ·")
            or sender.startswith("admin_")
            or sender.startswith("admin-")
        ):
            return "Admin"

        if not sender:
            return "Admin"

        name = str(student_name or "").strip()

        if not name or name.lower() in (
            "anonymous",
            "unknown",
            "none",
            "null"
        ):
            return "Anonymous"

        if sender in (
            "student",
            "user",
            "you",
            "anonymous",
            "student_reply",
            "student reply",
            "student-response",
            "student_response"
        ) or "student" in sender:
            return name

        return name

    # --------------------------------------------------------
    # FIRESTORE DATABASE
    # --------------------------------------------------------

    def load_feedback(self, show_error=True):
        """Load every feedback document from Firestore."""

        if db is None:
            self.feedback_data = []
            self.refresh_feedback_cards()

            if show_error:
                detail = (
                    f"\n\nDetails: {FIREBASE_IMPORT_ERROR}"
                    if FIREBASE_IMPORT_ERROR else ""
                )

                messagebox.showerror(
                    "Firebase Connection Error",
                    "Could not connect to Firebase. Check firebase_config.py "
                    "and serviceAccountKey.json." + detail,
                    parent=self
                )
            return

        try:
            records = []

            for document in db.collection("feedback").stream():
                data = document.to_dict() or {}

                status = data.get("status", "New")
                if status not in STATUS_COLORS:
                    status = "New"

                replies = data.get("replies", [])
                if not isinstance(replies, list):
                    replies = []

                anonymous = (
                    data.get("is_anonymous", False)
                    or data.get("anonymous", False)
                )

                student_name = (
                    "Anonymous"
                    if anonymous
                    else str(data.get("name") or "Anonymous")
                )

                records.append({
                    "id": document.id,
                    "name": student_name,
                    "category": str(data.get("category", "Other")),
                    "feedback": str(
                        data.get("feedback", data.get("message", ""))
                    ),
                    "status": status,
                    "date": str(data.get("date", "")),
                    "created_at": data.get("created_at"),
                    "replies": replies
                })

            print("\n" + "=" * 55)
            print("TOTAL FEEDBACK LOADED FROM FIRESTORE:", len(records))

            for record in records:
                print(
                    record["id"],
                    "|",
                    record["name"],
                    "|",
                    record["category"],
                    "|",
                    record["feedback"]
                )

            print("=" * 55 + "\n")

            # Show newest feedback first.
            records.sort(
                key=lambda item: self.timestamp_sort_key(
                    item.get("created_at")
                ),
                reverse=True
            )

            self.feedback_data = records
            self.refresh_feedback_cards()

        except Exception as error:
            print("Error loading feedback:", error)

            if show_error:
                messagebox.showerror(
                    "Database Error",
                    f"Could not load feedback from Firestore.\n\n{error}",
                    parent=self
                )

    @staticmethod
    def timestamp_sort_key(value):
        """Convert Firestore timestamps into sortable numbers."""

        try:
            return value.timestamp()
        except Exception:
            return 0

    def change_status(self, index, status):
        """Save the selected status to Firestore."""

        item = self.feedback_data[index]

        if item.get("status") == status:
            return

        if db is None or not item.get("id"):
            messagebox.showerror(
                "Database Error",
                "This feedback record is not connected to Firestore.",
                parent=self
            )
            return

        try:
            db.collection("feedback").document(item["id"]).update({
                "status": status
            })

            item["status"] = status
            self.refresh_feedback_cards()

        except Exception as error:
            messagebox.showerror(
                "Status Update Failed",
                f"Could not save the status to Firestore.\n\n{error}",
                parent=self
            )

    def send_reply(self, index, text_widget, placeholder):
        """Save an administrator reply to the selected feedback."""

        reply_text = text_widget.get("1.0", "end-1c").strip()

        if not reply_text or reply_text == placeholder:
            messagebox.showwarning(
                "Reply",
                "Please enter a reply before sending.",
                parent=self
            )
            return

        item = self.feedback_data[index]

        if db is None or not item.get("id"):
            messagebox.showerror(
                "Database Error",
                "This feedback record is not connected to Firestore.",
                parent=self
            )
            return

        try:
            document_ref = (
                db.collection("feedback")
                .document(item["id"])
            )

            # Read the latest document so student replies are preserved.
            snapshot = document_ref.get()

            if not snapshot.exists:
                messagebox.showerror(
                    "Feedback Not Found",
                    "This feedback record no longer exists.",
                    parent=self
                )
                return

            record = snapshot.to_dict() or {}
            replies = record.get("replies", [])

            if not isinstance(replies, list):
                replies = []

            now = datetime.now()

            new_reply = {
                "sender": "Admin",
                "message": reply_text,
                "text": reply_text,
                "date": now.strftime("%d %b %Y"),
                "created_at": now
            }

            replies.append(new_reply)

            document_ref.update({
                "replies": replies
            })

            item["replies"] = replies
            self.refresh_feedback_cards()

        except Exception as error:
            messagebox.showerror(
                "Reply Failed",
                f"Could not save your reply to Firestore.\n\n{error}",
                parent=self
            )

    # --------------------------------------------------------
    # FEEDBACK CARDS AND STATUS
    # --------------------------------------------------------

    def refresh_feedback_cards(self):
        """Create one card for every feedback record."""

        if (
            not hasattr(self, "cards_frame")
            or not self.cards_frame.winfo_exists()
        ):
            return

        for widget in self.cards_frame.winfo_children():
            widget.destroy()

        self.status_buttons = {}

        if not self.feedback_data:
            tk.Label(
                self.cards_frame,
                text="No feedback found in the database.",
                font=("Segoe UI", 11),
                fg=TEXT_LIGHT,
                bg=WHITE
            ).pack(anchor="w", pady=12)

        else:
            for index, item in enumerate(self.feedback_data):
                self.create_feedback_card(index, item)

        self.update_idletasks()
        self.update_scroll_region()

        print("TOTAL FEEDBACK RECORDS:", len(self.feedback_data))
        print(
            "FEEDBACK CARDS CREATED:",
            len(self.cards_frame.winfo_children())
        )

        self.after_idle(self.update_scroll_region)

    def create_feedback_card(self, index, item):
        """Create a feedback card with status and conversation."""

        card = tk.Frame(
            self.cards_frame,
            bg=WHITE,
            highlightthickness=1,
            highlightbackground=BORDER
        )
        card.pack(fill="x", pady=(0, 24))

        inner = tk.Frame(card, bg=WHITE)
        inner.pack(fill="x", padx=16, pady=14)

        tk.Label(
            inner,
            text=item["category"],
            font=("Segoe UI", 9, "bold"),
            fg=PURPLE_DARK,
            bg=PURPLE_LIGHT,
            anchor="w",
            padx=10,
            pady=4
        ).pack(anchor="w")

        wrap = max(180, self.current_window_width - 390)

        tk.Label(
            inner,
            text=item["feedback"],
            font=("Segoe UI", 10),
            fg=TEXT,
            bg=WHITE,
            anchor="w",
            justify="left",
            wraplength=wrap
        ).pack(anchor="w", fill="x", pady=(7, 3))

        tk.Label(
            inner,
            text=f"Submitted by {item['name']} · {item['date']}",
            font=("Segoe UI", 9),
            fg=TEXT_LIGHT,
            bg=WHITE,
            anchor="w"
        ).pack(anchor="w")

        tk.Label(
            inner,
            text="Update status",
            font=("Segoe UI", 10, "bold"),
            fg=TEXT,
            bg=WHITE,
            anchor="w"
        ).pack(anchor="w", pady=(12, 7))

        stages = tk.Frame(inner, bg=WHITE)
        stages.pack(anchor="w", fill="x", pady=(0, 12))

        options = [
            ("🆕 New", "New"),
            ("👀 Reviewed", "Reviewed"),
            ("✅ Resolved", "Resolved")
        ]

        self.status_buttons[index] = {}

        for label, status in options:
            selected = item["status"] == status
            status_bg, status_fg = STATUS_COLORS[status]

            button = RoundedButton(
                stages,
                text=label,
                width=100 if status != "Reviewed" else 112,
                height=34,
                radius=17,
                bg_color=status_bg if selected else WHITE,
                fg_color=status_fg if selected else TEXT_LIGHT,
                font=("Segoe UI", 9, "bold"),
                border_color=None if selected else BORDER,
                command=lambda i=index, s=status:
                    self.change_status(i, s)
            )

            button.pack(side="left", padx=(0, 8), pady=(0, 4))
            self.status_buttons[index][status] = button

        tk.Frame(
            inner,
            bg="#F0EEF8",
            height=1
        ).pack(fill="x", pady=(2, 12))

        tk.Label(
            inner,
            text=f"🗨  Conversation with {item['name']}",
            font=("Segoe UI", 10, "bold"),
            fg=TEXT,
            bg=WHITE,
            anchor="w"
        ).pack(anchor="w", pady=(0, 8))

        # Original student feedback.
        original = tk.Frame(inner, bg="#F3F1FC")
        original.pack(fill="x", pady=(0, 8))

        tk.Label(
            original,
            text=f"{item['name']} · {item['date']}",
            font=("Segoe UI", 9, "bold"),
            fg=TEXT_LIGHT,
            bg="#F3F1FC",
            anchor="w"
        ).pack(anchor="w", padx=12, pady=(9, 3))

        tk.Label(
            original,
            text=item["feedback"],
            font=("Segoe UI", 10),
            fg=TEXT,
            bg="#F3F1FC",
            anchor="w",
            justify="left",
            wraplength=wrap
        ).pack(anchor="w", padx=12, pady=(0, 9), fill="x")

        # Display student and admin replies in the same conversation.
        replies = item.get("replies", [])

        if replies:
            for reply in replies:

                if isinstance(reply, dict):
                    reply_message = self.get_reply_text(reply)

                    if not reply_message:
                        continue

                    sender_name = self.get_reply_sender(
                        reply,
                        item.get("name", "Anonymous")
                    )

                    reply_date = self.format_reply_date(reply)

                else:
                    # Keep old plain-text replies visible.
                    reply_message = str(reply).strip()
                    sender_name = "Admin"
                    reply_date = ""

                    if not reply_message:
                        continue

                heading = sender_name

                if reply_date:
                    heading += f" · {reply_date}"

                if sender_name == "Admin":
                    bubble_color = "#EDEBFF"
                    heading_color = PURPLE_DARK
                    side = "e"
                else:
                    bubble_color = "#F3F1FC"
                    heading_color = TEXT_LIGHT
                    side = "w"

                reply_box = tk.Frame(
                    inner,
                    bg=bubble_color
                )
                reply_box.pack(
                    anchor=side,
                    fill="x",
                    pady=(0, 7)
                )

                tk.Label(
                    reply_box,
                    text=heading,
                    font=("Segoe UI", 9, "bold"),
                    fg=heading_color,
                    bg=bubble_color,
                    anchor="w"
                ).pack(anchor="w", padx=12, pady=(8, 3))

                tk.Label(
                    reply_box,
                    text=reply_message,
                    font=("Segoe UI", 10),
                    fg=TEXT,
                    bg=bubble_color,
                    anchor="w",
                    justify="left",
                    wraplength=wrap
                ).pack(anchor="w", padx=12, pady=(0, 8), fill="x")

        else:
            tk.Label(
                inner,
                text="No replies yet.",
                font=("Segoe UI", 9, "italic"),
                fg=TEXT_LIGHT,
                bg=WHITE,
                anchor="w"
            ).pack(anchor="w", pady=(0, 10))

        # Administrator reply box.
        reply_row = tk.Frame(inner, bg=WHITE)
        reply_row.pack(fill="x")

        reply_text = tk.Text(
            reply_row,
            height=2,
            wrap="word",
            font=("Segoe UI", 10),
            fg=TEXT,
            bg=WHITE,
            relief="solid",
            bd=1,
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=PURPLE
        )
        reply_text.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 8)
        )

        placeholder = (
            f"Reply to {item['name']} — how you solved it, "
            "or why you can't..."
        )

        reply_text.insert("1.0", placeholder)
        reply_text.config(fg=TEXT_LIGHT)

        def clear_placeholder(event):
            if reply_text.get("1.0", "end-1c") == placeholder:
                reply_text.delete("1.0", "end")
                reply_text.config(fg=TEXT)

        def restore_placeholder(event):
            if not reply_text.get("1.0", "end-1c").strip():
                reply_text.insert("1.0", placeholder)
                reply_text.config(fg=TEXT_LIGHT)

        reply_text.bind("<FocusIn>", clear_placeholder)
        reply_text.bind("<FocusOut>", restore_placeholder)

        RoundedButton(
            reply_row,
            text="Send",
            width=64,
            height=34,
            radius=10,
            bg_color=PURPLE,
            fg_color=WHITE,
            font=("Segoe UI", 10, "bold"),
            command=lambda i=index, widget=reply_text, hint=placeholder:
                self.send_reply(i, widget, hint)
        ).pack(side="right", anchor="s")

    # --------------------------------------------------------
    # RESPONSIVE LAYOUT
    # Match view_feedback.py breakpoints and spacing.
    # --------------------------------------------------------

    def schedule_responsive_layout(self, event=None):
        """Schedule a layout update after resizing."""

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

    def update_responsive_layout(self):
        """Adjust the layout to match View Feedback."""

        self.resize_job = None

        if not self.winfo_exists():
            return

        window_width = self.winfo_width()
        window_height = self.winfo_height()

        if window_width < 200:
            return

        self.current_window_width = window_width
        self.current_window_height = window_height

        # 1. NAVBAR AND LOGO
        if window_width < 850:
            navbar_padding = 20
            logo_font_size = 16
        else:
            navbar_padding = 30
            logo_font_size = 19

        self.navbar.pack_configure(padx=navbar_padding)

        self.logo_text.config(
            font=("Segoe UI", logo_font_size, "bold")
        )

        self.logo_icon.config(
            font=("Segoe UI Emoji", logo_font_size)
        )

        # 2. MAIN CARD MARGINS
        outer_padding = 16 if window_width < 850 else 30

        self.card_outer.pack_configure(padx=outer_padding)

        # 3. SIDEBAR WIDTH AND PADDING
        if window_width < 950:
            sidebar_width = 190
            sidebar_padding = 10
        else:
            sidebar_width = 220
            sidebar_padding = 14

        self.sidebar.config(width=sidebar_width)

        self.sidebar_content.pack_configure(
            padx=sidebar_padding
        )

        # Keep sidebar fonts matched with View Feedback.
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

        # 4. MAIN CONTENT PADDING
        self.content_pad_x = (
            18 if window_width < 950 else 34
        )

        if window_height < 700:
            self.content_pad_y = 16
        elif window_width < 950:
            self.content_pad_y = 22
        else:
            self.content_pad_y = 32

        self.resize_content_window(
            type("CanvasSize", (), {
                "width": self.content_canvas.winfo_width()
            })()
        )

        # 5. TITLE AND SUBTITLE
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

                # 6. FOOTER
        footer_font_size = 10

        self.footer_text.config(
            font=("Segoe UI", footer_font_size)
        )

        for widget in self.footer.winfo_children():
            if widget.cget("text") == "About":
                widget.config(
                    font=("Segoe UI", 10, "bold")
                )

        self.after_idle(self.update_scroll_region)

    # --------------------------------------------------------
    # FOOTER
    # Match view_feedback.py
    # --------------------------------------------------------

    def create_footer(self):
        self.footer = tk.Frame(self, bg=BACKGROUND)
        self.footer.pack(side="bottom", pady=(0, 12))

        self.footer_text = tk.Label(
            self.footer,
            text="© 2026 FeedbackTrack · Made for Student Voices   ",
            font=("Segoe UI", 9),
            fg="#8D8A9F",
            bg=BACKGROUND
        )
        self.footer_text.pack(side="left")

        about = tk.Label(
            self.footer,
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

    # --------------------------------------------------------
    # PAGE NAVIGATION
    # --------------------------------------------------------

    def open_page(self, filename, user_uid=None):
        """Open another page and preserve the admin UID."""

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
                "Please keep the FeedbackTrack pages in the same folder.",
                parent=self
            )
            return

        try:
            command = [sys.executable, page_path]
            child_env = os.environ.copy()

            admin_pages = (
                "view_feedback.py",
                "manage_status.py",
                "admin_account.py"
            )

            admin_uid = (
                user_uid
                or self.user_uid
                or child_env.get(
                    "FEEDBACKTRACK_ADMIN_UID", ""
                ).strip()
            )

            if filename in admin_pages and admin_uid:
                admin_uid = str(admin_uid).strip()
                command.append(admin_uid)
                child_env["FEEDBACKTRACK_ADMIN_UID"] = admin_uid

            if filename in ("homepage.py", "signup.py"):
                child_env.pop("FEEDBACKTRACK_ADMIN_UID", None)

            self.child_process = subprocess.Popen(
                command,
                cwd=current_folder,
                env=child_env
            )

            self.withdraw()
            self.check_child_process()

        except OSError as error:
            self.child_process = None

            messagebox.showerror(
                "Navigation Error",
                f"Could not open {filename}.\n\n{error}",
                parent=self
            )

    def check_child_process(self):
        """Check whether an opened page has closed."""

        if not self.winfo_exists() or self.child_process is None:
            return

        if self.child_process.poll() is not None:
            self.child_process = None

            self.deiconify()
            self.lift()

            self.load_feedback(show_error=False)
            self.after_idle(self.update_responsive_layout)

        else:
            self.after(200, self.check_child_process)

    def on_login(self):
        self.open_page("homepage.py")

    def on_signup(self):
        self.open_page("signup.py")

    def on_view_feedback(self):
        self.open_page(
            "view_feedback.py",
            user_uid=self.user_uid
        )

    def on_admin_account(self):
        self.open_page(
            "admin_account.py",
            user_uid=self.user_uid
        )

    def on_logout(self):
        """Confirm before returning to the login page."""

        if messagebox.askyesno(
            "Logout",
            "Are you sure you want to logout?",
            parent=self
        ):
            self.open_page("homepage.py")

    # --------------------------------------------------------
    # ABOUT
    # Open About inside a Toplevel window, like submit_feedback.py.
    # --------------------------------------------------------

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

            # Create About as a child window of Manage Status.
            self.about_window = tk.Toplevel(self)

            # Keep About associated with this main window.
            self.about_window.transient(self)

            # Build the existing About page inside the child window.
            self.about_app = AboutPage(self.about_window)

            # Show About above Manage Status.
            self.about_window.lift()
            self.about_window.focus_force()

            # Clear saved references when About is destroyed.
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
        """Clear references when the About Toplevel is destroyed."""

        if (
            event is not None
            and self.about_window is not None
            and event.widget is self.about_window
        ):
            self.about_window = None
            self.about_app = None

    # --------------------------------------------------------
    # APPLICATION SHUTDOWN
    # --------------------------------------------------------

    def close_application(self):
        """Close the application safely."""

        if self.resize_job is not None:
            try:
                self.after_cancel(self.resize_job)
            except tk.TclError:
                pass

        self.unbind_all("<MouseWheel>")
        self.unbind_all("<Button-4>")
        self.unbind_all("<Button-5>")

        # Close About before destroying the main application.
        if self.about_window is not None:
            try:
                if self.about_window.winfo_exists():
                    self.about_window.destroy()
            except tk.TclError:
                pass

        self.about_window = None
        self.about_app = None

        if (
            self.child_process is not None
            and self.child_process.poll() is None
        ):
            try:
                self.child_process.terminate()
            except OSError:
                pass

        self.destroy()


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

if __name__ == "__main__":
    app = ManageStatusApp()
    app.mainloop()
