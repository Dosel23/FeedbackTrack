import tkinter as tk
from tkinter import messagebox
import subprocess
import sys
import os
from datetime import datetime

# Import the existing Firestore database connection.
from firebase_config import db


# ============================================================
# FeedbackTrack - My Feedback Page
# ============================================================

# COLORS
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

# Match the Submit Feedback page.
SIDEBAR_FONT_SIZE = 10
SIDEBAR_ICON_SIZE = 10


# ============================================================
# FORMAT FEEDBACK TIMESTAMP
# ============================================================

def format_feedback_timestamp(value):

    if not value:
        return ""

    if hasattr(value, "strftime"):
        try:
            return value.strftime("%d %b %Y %I:%M %p")
        except (ValueError, TypeError, OSError):
            pass

    if isinstance(value, (int, float)):
        try:
            if value > 100000000000:
                value = value / 1000

            parsed_date = datetime.fromtimestamp(value)
            return parsed_date.strftime("%d %b %Y %I:%M %p")

        except (ValueError, TypeError, OSError, OverflowError):
            return str(value)

    if isinstance(value, str):

        value = value.strip()

        if not value:
            return ""

        formats_with_time = [
            "%d %b %Y %I:%M %p",
            "%d %b %Y %H:%M",
            "%d %b %Y %H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M%z",
        ]

        for date_format in formats_with_time:
            try:
                parsed_date = datetime.strptime(value, date_format)
                return parsed_date.strftime("%d %b %Y %I:%M %p")
            except ValueError:
                continue

        formats_without_time = [
            "%d %b %Y",
            "%Y-%m-%d",
        ]

        for date_format in formats_without_time:
            try:
                parsed_date = datetime.strptime(value, date_format)
                return parsed_date.strftime("%d %b %Y")
            except ValueError:
                continue

        return value

    return str(value)


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

    def draw(self):

        self.delete("all")

        radius = min(
            self.radius,
            self.width / 2,
            self.height / 2
        )

        width = self.width
        height = self.height

        if self.border_color:

            self.create_rounded_rectangle(
                0, 0, width, height, radius,
                fill=self.border_color,
                outline=""
            )

            self.create_rounded_rectangle(
                self.border_width,
                self.border_width,
                width - self.border_width,
                height - self.border_width,
                max(1, radius - self.border_width),
                fill=self.bg_color,
                outline=""
            )

        else:

            self.create_rounded_rectangle(
                0, 0, width, height, radius,
                fill=self.bg_color,
                outline=""
            )

        self.create_text(
            width / 2,
            height / 2,
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

        self.config(width=width, height=height)
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
# LOAD FEEDBACK FROM FIRESTORE
# Only load feedback belonging to the logged-in student.
# ============================================================

def load_feedback_from_database(user_uid):

    feedback_records = []

    if not user_uid:
        return feedback_records

    # Only ask Firestore for this student's own feedback (the security
    # rules reject queries that are not limited to the signed-in user).
    documents = (
        db.collection("feedback")
        .where("user_uid", "==", str(user_uid).strip())
        .stream()
    )

    for document in documents:

        record = document.to_dict() or {}

        # Read the owner UID saved with the feedback.
        owner_uid = (
            record.get("user_uid")
            or record.get("student_uid")
            or record.get("uid")
            or record.get("user_id")
            or record.get("userId")
            or record.get("student_id")
            or record.get("studentId")
            or ""
        )

        owner_uid = str(owner_uid).strip()

        # Skip records that do not belong to the current student.
        if owner_uid != str(user_uid).strip():
            continue

        created_at = record.get("created_at")

        timestamp_value = (
            created_at
            or record.get("timestamp")
            or record.get("submitted_at")
            or record.get("date", "")
        )

        feedback_date = format_feedback_timestamp(timestamp_value)

        replies = record.get("replies", [])

        if not isinstance(replies, list):
            replies = []

        reply_count = len(replies)

        if reply_count == 0:
            conversation_text = "No replies yet"
        elif reply_count == 1:
            conversation_text = "1 reply"
        else:
            conversation_text = f"{reply_count} replies"

        feedback_records.append({
            "document_id": document.id,
            "name": record.get("name", ""),
            "category": record.get("category", "Other"),
            "feedback": record.get("feedback", ""),
            "status": record.get("status", "New"),
            "conversation": conversation_text,
            "reply_count": reply_count,
            "replies": replies,
            "date": feedback_date or "Date unavailable",
            "created_at": created_at,
            "owner_uid": owner_uid
        })

    def sort_key(record):

        value = record.get("created_at")

        if hasattr(value, "timestamp"):
            try:
                return value.timestamp()
            except (ValueError, OSError):
                return 0

        return 0

    feedback_records.sort(key=sort_key, reverse=True)

    return feedback_records


# ============================================================
# MAIN APPLICATION
# ============================================================

class MyFeedbackApp(tk.Tk):

    def __init__(self):

        super().__init__()

        # Read the student UID.
        self.user_uid = (
            sys.argv[1].strip()
            if len(sys.argv) > 1 and sys.argv[1].strip()
            else os.environ.get(
                "FEEDBACKTRACK_STUDENT_UID", ""
            ).strip()
        )

        if not self.user_uid:
            self.user_uid = None
        else:
            os.environ["FEEDBACKTRACK_STUDENT_UID"] = self.user_uid

        print("My Feedback - Student UID:", repr(self.user_uid))

        # Window configuration.
        self.title("FeedbackTrack - My Feedback")
        self.geometry("1200x780")
        self.minsize(850, 620)
        self.configure(bg=BACKGROUND)
        self.resizable(True, True)

        self.child_process = None
        self.resize_job = None

        # About window references.
        self.about_window = None
        self.about_app = None

        # Conversation window references.
        self.conversation_window = None
        self.conversation_app = None
        self.open_conversation_document_id = None

        # Store feedback records and table widgets.
        self.feedback_data = []
        self.table_rows = []
        self.feedback_labels = []
        self.status_labels = []
        self.conversation_buttons = []
        self.date_labels = []
        self.header_labels = []

        # Keep each checkbox variable using its feedback document ID.
        self.selection_vars = {}

        # ====================================================
        # TOP NAVIGATION BAR
        # ====================================================

        navbar = tk.Frame(self, bg=BACKGROUND)
        navbar.pack(fill="x", padx=40, pady=(18, 8))
        self.navbar = navbar

        brand_frame = tk.Frame(navbar, bg=BACKGROUND)
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

        # ====================================================
        # MAIN CARD
        # ====================================================

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

        # ====================================================
        # SIDEBAR
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

        # Submit Feedback.
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

        # My Feedback - selected.
        feedback_menu = tk.Frame(sidebar_content, bg=PURPLE)
        feedback_menu.pack(fill="x", pady=(0, 8))

        feedback_icon = tk.Label(
            feedback_menu,
            text="📁",
            font=("Segoe UI Emoji", SIDEBAR_ICON_SIZE),
            fg=WHITE,
            bg=PURPLE
        )
        feedback_icon.pack(side="left", padx=(12, 7), pady=9)

        feedback_label = tk.Label(
            feedback_menu,
            text="My Feedback",
            font=("Segoe UI", SIDEBAR_FONT_SIZE, "bold"),
            fg=WHITE,
            bg=PURPLE
        )
        feedback_label.pack(side="left", pady=9)

        # My Account.
        account_menu = tk.Frame(
            sidebar_content,
            bg=LEFT_BACKGROUND,
            cursor="hand2"
        )
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
                lambda event: self.on_account()
            )

        # Logout.
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
        # MAIN CONTENT
        # ====================================================

        main_area = tk.Frame(card, bg=WHITE)
        main_area.grid(row=0, column=1, sticky="nsew")
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
            text="My Feedback",
            font=("Segoe UI", 21, "bold"),
            fg=TEXT,
            bg=WHITE
        )
        self.page_title.pack(anchor="nw")

        self.subtitle = tk.Label(
            content,
            text="Everything you've submitted, and where it stands.",
            font=("Segoe UI", 11),
            fg=TEXT_LIGHT,
            bg=WHITE
        )
        self.subtitle.pack(anchor="nw", pady=(4, 24))

        # ====================================================
        # SELECTION AND DELETE CONTROLS
        # ====================================================

        delete_toolbar = tk.Frame(content, bg=WHITE)
        delete_toolbar.pack(fill="x", pady=(0, 12))
        self.delete_toolbar = delete_toolbar

        self.selection_count_label = tk.Label(
            delete_toolbar,
            text="0 selected",
            font=("Segoe UI", 10),
            fg=TEXT_LIGHT,
            bg=WHITE
        )
        self.selection_count_label.pack(side="left")

        self.delete_button = RoundedButton(
            delete_toolbar,
            text="Delete Selected",
            width=145,
            height=36,
            radius=11,
            bg_color="#C83F4F",
            fg_color=WHITE,
            font=("Segoe UI", 9, "bold"),
            command=self.delete_selected_feedback
        )
        self.delete_button.pack(side="right")

        # ====================================================
        # TABLE CARD
        # ====================================================

        table_card = tk.Frame(
            content,
            bg=WHITE,
            highlightthickness=1,
            highlightbackground=BORDER
        )
        table_card.pack(fill="both", expand=True, anchor="n")
        self.table_card = table_card

        # Table headings.
        header = tk.Frame(table_card, bg=PURPLE_LIGHT)
        header.pack(fill="x")
        self.table_header = header

        header_texts = [
            "CATEGORY",
            "FEEDBACK",
            "STATUS",
            "CONVERSATION",
            "DATE",
            "SELECT"
        ]

        for column, heading in enumerate(header_texts):

            label = tk.Label(
                header,
                text=heading,
                font=("Segoe UI", 9, "bold"),
                fg=TEXT_LIGHT,
                bg=PURPLE_LIGHT,
                anchor="w"
            )

            label.grid(
                row=0,
                column=column,
                sticky="ew",
                padx=10,
                pady=12
            )

            self.header_labels.append(label)

        # ====================================================
        # SCROLLABLE FEEDBACK LIST
        # ====================================================

        scroll_area = tk.Frame(table_card, bg=WHITE)
        scroll_area.pack(fill="both", expand=True)
        self.scroll_area = scroll_area

        self.feedback_canvas = tk.Canvas(
            scroll_area,
            bg=WHITE,
            highlightthickness=0,
            bd=0
        )
        self.feedback_canvas.pack(
            side="left",
            fill="both",
            expand=True
        )

        self.feedback_scrollbar = tk.Scrollbar(
            scroll_area,
            orient="vertical",
            command=self.feedback_canvas.yview
        )
        self.feedback_scrollbar.pack(side="right", fill="y")

        self.feedback_canvas.configure(
            yscrollcommand=self.feedback_scrollbar.set
        )

        self.feedback_rows_frame = tk.Frame(
            self.feedback_canvas,
            bg=WHITE
        )

        self.canvas_window = self.feedback_canvas.create_window(
            (0, 0),
            window=self.feedback_rows_frame,
            anchor="nw"
        )

        self.feedback_rows_frame.bind(
            "<Configure>",
            self.update_scroll_region
        )

        self.feedback_canvas.bind(
            "<Configure>",
            self.resize_feedback_frame
        )

        self.feedback_canvas.bind(
            "<Enter>",
            self.enable_mousewheel
        )
        self.feedback_canvas.bind(
            "<Leave>",
            self.disable_mousewheel
        )

        self.feedback_rows_frame.bind(
            "<Enter>",
            self.enable_mousewheel
        )
        self.feedback_rows_frame.bind(
            "<Leave>",
            self.disable_mousewheel
        )

        # ====================================================
        # LOAD FEEDBACK
        # ====================================================

        try:
            self.feedback_data = load_feedback_from_database(
                self.user_uid
            )

        except Exception as error:

            self.feedback_data = []
            self.database_error = str(error)

            print("Error loading feedback from Firestore:", repr(error))

        else:
            self.database_error = None

        if self.database_error is not None:

            self.empty_message = tk.Label(
                self.feedback_rows_frame,
                text=(
                    "Unable to load feedback from the database.\n"
                    "Please check your Firebase configuration "
                    "and connection."
                ),
                font=("Segoe UI", 11),
                fg=TEXT_LIGHT,
                bg=WHITE,
                justify="center",
                wraplength=400,
                pady=24
            )
            self.empty_message.pack(fill="x")

        elif not self.feedback_data:

            self.empty_message = tk.Label(
                self.feedback_rows_frame,
                text="You haven't submitted any feedback yet.",
                font=("Segoe UI", 11),
                fg=TEXT_LIGHT,
                bg=WHITE,
                justify="center",
                pady=24
            )
            self.empty_message.pack(fill="x")

        else:

            self.empty_message = None
            self.create_feedback_rows()

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

        # Responsive layout.
        self.bind("<Configure>", self.schedule_responsive_layout)
        self.after_idle(self.update_responsive_layout)

        self.protocol("WM_DELETE_WINDOW", self.close_application)

    # ========================================================
    # UPDATE SELECTION COUNT
    # ========================================================

    def update_selection_count(self):

        selected_count = sum(
            1 for variable in self.selection_vars.values()
            if variable.get()
        )

        self.selection_count_label.config(
            text=f"{selected_count} selected"
        )

        if selected_count:
            self.delete_button.bg_color = "#C83F4F"
            self.delete_button.draw()
        else:
            self.delete_button.bg_color = "#B7B4C6"
            self.delete_button.draw()

    # ========================================================
    # DELETE SELECTED FEEDBACK
    # ========================================================

    def delete_selected_feedback(self):

        selected_ids = [
            document_id
            for document_id, variable in self.selection_vars.items()
            if variable.get()
        ]

        if not selected_ids:
            messagebox.showinfo(
                "Delete Feedback",
                "Please select at least one feedback record to delete.",
                parent=self
            )
            return

        if not self.user_uid:
            messagebox.showerror(
                "Delete Feedback",
                "Your student account could not be identified.\n\n"
                "Please log in again before deleting feedback.",
                parent=self
            )
            return

        warning_text = (
            f"Are you sure you want to permanently delete "
            f"{len(selected_ids)} selected feedback record(s)?\n\n"
            "This action cannot be undone."
        )

        answer = messagebox.askyesno(
            "Confirm Delete",
            warning_text,
            parent=self
        )

        if not answer:
            return

        deleted_ids = []
        failed_ids = []
        skipped_count = 0

        for document_id in selected_ids:

            try:
                # Retrieve the current Firestore document.
                feedback_document = (
                    db.collection("feedback")
                    .document(document_id)
                )

                document_snapshot = feedback_document.get()

                if not document_snapshot.exists:
                    skipped_count += 1
                    continue

                record = document_snapshot.to_dict() or {}

                # Check ownership directly in Firestore.
                owner_uid = (
                    record.get("user_uid")
                    or record.get("student_uid")
                    or record.get("uid")
                    or record.get("user_id")
                    or record.get("userId")
                    or record.get("student_id")
                    or record.get("studentId")
                    or ""
                )

                owner_uid = str(owner_uid).strip()

                # Do not delete if the owner cannot be verified.
                if owner_uid != str(self.user_uid).strip():
                    skipped_count += 1
                    continue

                # Delete only the verified feedback document.
                feedback_document.delete()
                deleted_ids.append(document_id)

            except Exception as error:
                failed_ids.append(document_id)

                print(
                    f"Could not delete feedback {document_id}: "
                    f"{repr(error)}"
                )

        # Remove successfully deleted records from the displayed list.
        if deleted_ids:

            self.feedback_data = [
                record
                for record in self.feedback_data
                if record["document_id"] not in deleted_ids
            ]

            self.refresh_feedback_rows()

        # Show the actual deletion result.
        if failed_ids or skipped_count:

            result_message = (
                f"{len(deleted_ids)} record(s) deleted successfully.\n"
                f"{skipped_count} record(s) skipped because their ownership "
                "could not be verified or they no longer exist.\n"
                f"{len(failed_ids)} record(s) could not be deleted."
            )

            if failed_ids:
                result_message += (
                    "\n\nPlease check your Firebase connection, "
                    "database configuration, and permissions."
                )

            messagebox.showwarning(
                "Delete Feedback Result",
                result_message,
                parent=self
            )

        elif deleted_ids:

            messagebox.showinfo(
                "Delete Feedback",
                f"{len(deleted_ids)} feedback record(s) "
                "deleted successfully.",
                parent=self
            )

    # ========================================================
    # REFRESH ROWS AFTER DELETION
    # ========================================================

    def refresh_feedback_rows(self):

        for widget in self.feedback_rows_frame.winfo_children():
            widget.destroy()

        self.table_rows.clear()
        self.feedback_labels.clear()
        self.status_labels.clear()
        self.conversation_buttons.clear()
        self.date_labels.clear()
        self.selection_vars.clear()

        if not self.feedback_data:

            self.empty_message = tk.Label(
                self.feedback_rows_frame,
                text="You haven't submitted any feedback yet.",
                font=("Segoe UI", 11),
                fg=TEXT_LIGHT,
                bg=WHITE,
                justify="center",
                pady=24
            )
            self.empty_message.pack(fill="x")

        else:

            self.empty_message = None
            self.create_feedback_rows()

        self.update_selection_count()
        self.update_scroll_region()
        self.after_idle(self.update_responsive_layout)

    # ========================================================
    # SCROLLING
    # ========================================================

    def update_scroll_region(self, event=None):

        self.feedback_canvas.configure(
            scrollregion=self.feedback_canvas.bbox("all")
        )

    def resize_feedback_frame(self, event):

        self.feedback_canvas.itemconfigure(
            self.canvas_window,
            width=event.width
        )

    def enable_mousewheel(self, event=None):

        self.bind_all("<MouseWheel>", self.on_mousewheel)
        self.bind_all("<Button-4>", self.on_mousewheel_linux)
        self.bind_all("<Button-5>", self.on_mousewheel_linux)

    def disable_mousewheel(self, event=None):

        self.unbind_all("<MouseWheel>")
        self.unbind_all("<Button-4>")
        self.unbind_all("<Button-5>")

    def on_mousewheel(self, event):

        self.feedback_canvas.yview_scroll(
            int(-1 * (event.delta / 120)),
            "units"
        )

    def on_mousewheel_linux(self, event):

        if event.num == 4:
            self.feedback_canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.feedback_canvas.yview_scroll(1, "units")

    # ========================================================
    # CREATE FEEDBACK ROWS
    # ========================================================

    def create_feedback_rows(self):

        for row_index, record in enumerate(self.feedback_data):

            category = record["category"]
            feedback = record["feedback"]
            status = record["status"]
            conversation = record["conversation"]
            reply_count = record.get("reply_count", 0)
            date = record["date"]
            document_id = record["document_id"]

            row = tk.Frame(
                self.feedback_rows_frame,
                bg=WHITE
            )
            row.pack(fill="x")
            self.table_rows.append(row)

            # Category badge.
            category_badge = tk.Label(
                row,
                text=category,
                font=("Segoe UI", 9, "bold"),
                fg=PURPLE,
                bg=PURPLE_LIGHT,
                padx=8,
                pady=4
            )
            category_badge.grid(
                row=0,
                column=0,
                sticky="w",
                padx=10,
                pady=12
            )

            # Feedback text.
            feedback_label = tk.Label(
                row,
                text=feedback,
                font=("Segoe UI", 11),
                fg=TEXT,
                bg=WHITE,
                anchor="w",
                justify="left",
                wraplength=220
            )
            feedback_label.grid(
                row=0,
                column=1,
                sticky="ew",
                padx=10,
                pady=12
            )
            self.feedback_labels.append(feedback_label)

            # Status badge.
            if str(status).lower() == "new":
                status_bg = "#EEF2FF"
                status_fg = "#526DFF"
            elif str(status).lower() == "reviewed":
                status_bg = "#FFF4D8"
                status_fg = "#C28A12"
            elif str(status).lower() == "resolved":
                status_bg = "#E2F6ED"
                status_fg = "#15956A"
            else:
                status_bg = "#F0EFF7"
                status_fg = TEXT_LIGHT

            status_badge = tk.Label(
                row,
                text=status,
                font=("Segoe UI", 9, "bold"),
                fg=status_fg,
                bg=status_bg,
                padx=9,
                pady=4
            )
            status_badge.grid(
                row=0,
                column=2,
                sticky="w",
                padx=8,
                pady=12
            )
            self.status_labels.append(status_badge)

            # Conversation button.
            if reply_count == 0:
                button_text = "No replies yet"
                button_fg = TEXT_LIGHT
                button_width = 105
            else:
                button_text = "●  " + conversation
                button_fg = PURPLE
                button_width = 125

            conversation_button = RoundedButton(
                row,
                text=button_text,
                width=button_width,
                height=32,
                radius=16,
                bg_color=WHITE,
                fg_color=button_fg,
                font=("Segoe UI", 9, "bold"),
                border_color=BORDER,
                border_width=1,
                command=lambda selected_record=record:
                    self.view_conversation(selected_record)
            )

            conversation_button.grid(
                row=0,
                column=3,
                sticky="w",
                padx=6,
                pady=8
            )
            self.conversation_buttons.append(conversation_button)

            # Date.
            date_label = tk.Label(
                row,
                text=date,
                font=("Segoe UI", 9),
                fg=TEXT_LIGHT,
                bg=WHITE,
                anchor="w"
            )
            date_label.grid(
                row=0,
                column=4,
                sticky="w",
                padx=8,
                pady=12
            )
            self.date_labels.append(date_label)

            # Checkbox for selecting this feedback record.
            selection_var = tk.BooleanVar(value=False)
            self.selection_vars[document_id] = selection_var

            selection_checkbox = tk.Checkbutton(
                row,
                variable=selection_var,
                command=self.update_selection_count,
                bg=WHITE,
                activebackground=WHITE,
                selectcolor=PURPLE_LIGHT,
                cursor="hand2",
                bd=0,
                highlightthickness=0
            )
            selection_checkbox.grid(
                row=0,
                column=5,
                sticky="w",
                padx=15,
                pady=12
            )

            # Separator.
            if row_index < len(self.feedback_data) - 1:

                separator = tk.Frame(
                    self.feedback_rows_frame,
                    bg=BORDER,
                    height=1
                )
                separator.pack(fill="x")

        self.feedback_rows_frame.update_idletasks()
        self.update_scroll_region()
        self.update_selection_count()

    # ========================================================
    # RESPONSIVE LAYOUT
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

    def update_responsive_layout(self):

        self.resize_job = None

        if not self.winfo_exists():
            return

        window_width = self.winfo_width()
        window_height = self.winfo_height()

        # Navbar and logo.
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

        # Main card margins.
        outer_padding = 16 if window_width < 850 else 30
        self.card_outer.pack_configure(padx=outer_padding)

        # Sidebar size and padding.
        if window_width < 950:
            sidebar_width = 190
            sidebar_padding = 10
        else:
            sidebar_width = 220
            sidebar_padding = 14

        self.sidebar.config(width=sidebar_width)
        self.sidebar_content.pack_configure(padx=sidebar_padding)

        # Keep sidebar font sizes consistent.
        for widget in self.sidebar_content.winfo_children():
            for child in widget.winfo_children():

                if not isinstance(child, tk.Label):
                    continue

                if child.cget("text") in (
                    "Submit Feedback",
                    "My Feedback",
                    "My Account",
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

                elif child.cget("text") in ("🖊", "📁", "👤", "↪"):
                    child.config(
                        font=("Segoe UI Emoji", SIDEBAR_ICON_SIZE)
                    )

        # Main content padding.
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

        # Title and subtitle.
        if window_width < 950:
            title_font_size = 18
            subtitle_gap = 14
        else:
            title_font_size = 21
            subtitle_gap = 24

        self.page_title.config(
            font=("Segoe UI", title_font_size, "bold")
        )
        self.subtitle.config(font=("Segoe UI", 11))
        self.subtitle.pack_configure(pady=(4, subtitle_gap))

        # Adjust the selection toolbar for different window sizes.
        if window_width < 950:
            self.delete_button.set_size(125, 34)
            self.delete_button.font = ("Segoe UI", 8, "bold")
            self.delete_button.draw()
            self.selection_count_label.config(
                font=("Segoe UI", 9)
            )
        else:
            self.delete_button.set_size(145, 36)
            self.delete_button.font = ("Segoe UI", 9, "bold")
            self.delete_button.draw()
            self.selection_count_label.config(
                font=("Segoe UI", 10)
            )

        # Responsive table columns.
        if window_width < 950:
            column_widths = [80, 1, 80, 110, 80, 55]
            column_paddings = [5, 5, 4, 3, 4, 5]
            feedback_wrap = 140
        else:
            column_widths = [110, 1, 115, 150, 110, 65]
            column_paddings = [12, 10, 10, 10, 10, 5]
            feedback_wrap = 260

        for column in range(6):

            if column == 1:
                minsize = 120 if window_width < 950 else 200
                weight = 1
            else:
                minsize = column_widths[column]
                weight = 0

            self.table_header.grid_columnconfigure(
                column,
                weight=weight,
                minsize=minsize
            )

            for row in self.table_rows:
                row.grid_columnconfigure(
                    column,
                    weight=weight,
                    minsize=minsize
                )

        for index, label in enumerate(self.header_labels):
            label.grid_configure(padx=column_paddings[index])
            label.config(font=("Segoe UI", 9, "bold"))

        for label in self.feedback_labels:
            label.config(
                wraplength=feedback_wrap,
                font=("Segoe UI", 11)
            )

        # Conversation button widths.
        if window_width < 950:
            default_button_width = 105
            button_font_size = 8
        else:
            default_button_width = 125
            button_font_size = 9

        for button, record in zip(
            self.conversation_buttons,
            self.feedback_data
        ):

            if record.get("reply_count", 0) == 0:
                button_width = 88 if window_width < 950 else 105
            else:
                button_width = default_button_width

            button.set_size(button_width, 32)
            button.font = (
                "Segoe UI",
                button_font_size,
                "bold"
            )
            button.draw()

        for label in self.status_labels:
            label.config(font=("Segoe UI", 9, "bold"))

        for label in self.date_labels:
            label.config(font=("Segoe UI", 9))

        row_padding_y = 8 if window_width < 950 else 12

        for label in (
            self.feedback_labels
            + self.status_labels
            + self.date_labels
        ):
            label.grid_configure(pady=row_padding_y)

        footer_font_size = 8 if window_width < 950 else 9
        self.footer_text.config(
            font=("Segoe UI", footer_font_size)
        )

        for widget in self.footer.winfo_children():
            if widget.cget("text") == "About":
                widget.config(font=("Segoe UI", 10, "bold"))

        self.after_idle(self.update_scroll_region)

    # ========================================================
    # NAVIGATION
    # ========================================================

    def on_submit_feedback(self):
        self.open_page("submit_feedback.py")

    def on_account(self):
        self.open_page("my_account.py")

    def on_login(self):
        self.open_page("homepage.py")

    def on_signup(self):
        self.open_page("signup.py")

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
    # CONVERSATION WINDOW
    # Open conversation.py above My Feedback without hiding it.
    # ========================================================

    def view_conversation(self, record=None):

        if record is None:
            messagebox.showerror(
                "Conversation",
                "The feedback record could not be identified.",
                parent=self
            )
            return

        document_id = record.get("document_id")

        if not document_id:
            messagebox.showerror(
                "Conversation",
                "The feedback document ID is missing.",
                parent=self
            )
            return

        # If this feedback's conversation is already open,
        # bring the same window to the front.
        if self.conversation_window is not None:

            try:
                if self.conversation_window.winfo_exists():

                    if (
                        self.open_conversation_document_id
                        == document_id
                    ):
                        self.conversation_window.lift()
                        self.conversation_window.attributes(
                            "-topmost", True
                        )
                        self.conversation_window.focus_force()
                        return

                    # Another feedback was selected.
                    # Close the old conversation before opening the new one.
                    self.conversation_window.destroy()

            except tk.TclError:
                pass

        self.conversation_window = None
        self.conversation_app = None
        self.open_conversation_document_id = None

        try:

            # Import the existing conversation interface.
            from conversation import ConversationPage

            # Create Conversation as a separate window belonging to
            # My Feedback. Do not hide or replace My Feedback.
            self.conversation_window = tk.Toplevel(self)
            self.conversation_window.transient(self)

            # conversation.py currently reads its document ID and UID
            # from sys.argv. Temporarily provide those values while
            # creating ConversationPage, then restore the original args.
            current_folder = os.path.dirname(
                os.path.abspath(__file__)
            )

            conversation_path = os.path.join(
                current_folder,
                "conversation.py"
            )

            if not os.path.isfile(conversation_path):
                self.conversation_window.destroy()
                self.conversation_window = None

                messagebox.showerror(
                    "Conversation Error",
                    "conversation.py was not found.\n\n"
                    "Please keep conversation.py and "
                    "my_feedback.py in the same folder.",
                    parent=self
                )
                return

            original_argv = sys.argv[:]

            try:

                sys.argv = [
                    conversation_path,
                    str(document_id),
                    self.user_uid or ""
                ]

                # This creates the existing conversation UI and loads
                # the selected feedback from Firestore.
                self.conversation_app = ConversationPage(
                    self.conversation_window
                )

            finally:
                # Do not change My Feedback's own command-line arguments.
                sys.argv = original_argv

            self.open_conversation_document_id = document_id

            # Keep the conversation above My Feedback.
            self.conversation_window.lift()
            self.conversation_window.attributes("-topmost", True)
            self.conversation_window.focus_force()

            # Clear the stored references when the window closes.
            self.conversation_window.bind(
                "<Destroy>",
                self.on_conversation_destroy,
                add="+"
            )

        except Exception as error:

            if self.conversation_window is not None:
                try:
                    if self.conversation_window.winfo_exists():
                        self.conversation_window.destroy()
                except tk.TclError:
                    pass

            self.conversation_window = None
            self.conversation_app = None
            self.open_conversation_document_id = None

            messagebox.showerror(
                "Conversation Error",
                f"Could not open the conversation.\n\n{error}",
                parent=self
            )

    def on_conversation_destroy(self, event=None):

        # Child widgets also produce Destroy events, so only clear
        # the references when the actual conversation window closes.
        if (
            event is not None
            and self.conversation_window is not None
            and event.widget is self.conversation_window
        ):
            self.conversation_window = None
            self.conversation_app = None
            self.open_conversation_document_id = None

    def no_replies(self):

        messagebox.showinfo(
            "Conversation",
            "There are no replies to this feedback yet.",
            parent=self
        )

    # ========================================================
    # OPEN OTHER PAGES
    # Other navigation continues using the existing subprocess method.
    # ========================================================

    def open_page(self, filename, extra_args=None):

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
                "Please keep the FeedbackTrack pages "
                "in the same folder.",
                parent=self
            )
            return

        try:

            command = [sys.executable, page_path]
            child_env = os.environ.copy()

            # Pass the logged-in student's UID to student pages.
            if filename not in ("homepage.py", "signup.py"):

                student_uid = (
                    self.user_uid
                    or child_env.get(
                        "FEEDBACKTRACK_STUDENT_UID", ""
                    ).strip()
                )

                if student_uid:
                    command.append(student_uid)
                    child_env["FEEDBACKTRACK_STUDENT_UID"] = student_uid

            else:

                child_env.pop(
                    "FEEDBACKTRACK_STUDENT_UID",
                    None
                )

            if filename == "conversation.py" and extra_args:
                command.extend(extra_args)

            self.child_process = subprocess.Popen(
                command,
                cwd=current_folder,
                env=child_env
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

            self.after_idle(self.update_responsive_layout)

        else:
            self.after(200, self.check_child_process)

    # ========================================================
    # CLOSE APPLICATION
    # ========================================================

    def close_application(self):

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

        # Close Conversation if it is still open.
        if self.conversation_window is not None:
            try:
                if self.conversation_window.winfo_exists():
                    self.conversation_window.destroy()
            except tk.TclError:
                pass

        self.conversation_window = None
        self.conversation_app = None
        self.open_conversation_document_id = None

        # Stop any other page opened as a subprocess.
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

    app = MyFeedbackApp()
    app.mainloop()