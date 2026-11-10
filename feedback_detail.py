
import tkinter as tk
from tkinter import messagebox
import sys
import os
from datetime import datetime

# Use the existing Firebase connection.
try:
    from firebase_config import db
    FIREBASE_IMPORT_ERROR = None
except Exception as error:
    db = None
    FIREBASE_IMPORT_ERROR = str(error)


# ============================================================
# FeedbackTrack - Admin Feedback Detail Popup
# Displays the selected feedback from the Firestore database.
# ============================================================


# Colours matching conversation.py
BG_COLOR = "#F3F2FC"
PRIMARY_COLOR = "#6C63FF"
HOVER_COLOR = "#554BEF"

DARK_TEXT = "#1E1B2E"
LIGHT_TEXT = "#6B6880"

WHITE = "#FFFFFF"
BORDER_COLOR = "#E0DCFB"
BUBBLE_COLOR = "#F2F0FF"
BADGE_COLOR = "#EEEDFF"

FONT_FAMILY = "Segoe UI"

SMALL_FONT = (FONT_FAMILY, 10)
BODY_FONT = (FONT_FAMILY, 11)
BUTTON_FONT = (FONT_FAMILY, 10, "bold")


# ============================================================
# ROUNDED RECTANGLE
# ============================================================

def create_rounded_rectangle(
    canvas, x1, y1, x2, y2, radius=15, **kwargs
):
    """Draw a rounded rectangle on a Canvas."""

    radius = min(
        radius,
        max(1, (x2 - x1) / 2),
        max(1, (y2 - y1) / 2)
    )

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
        **kwargs
    )


# ============================================================
# ROUNDED BUTTON
# ============================================================

class RoundedButton(tk.Canvas):

    def __init__(
        self,
        parent,
        text="Button",
        command=None,
        width=80,
        height=38,
        bg_color=PRIMARY_COLOR,
        text_color=WHITE,
        hover_color=HOVER_COLOR,
        border_color=None,
        font=BUTTON_FONT,
        radius=12
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
        self.text = text
        self.width = width
        self.height = height
        self.bg_color = bg_color
        self.text_color = text_color
        self.hover_color = hover_color
        self.border_color = border_color
        self.font = font
        self.radius = radius

        self.draw_button()

        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)

    def draw_button(self):
        """Draw the button with rounded corners."""

        self.delete("all")

        create_rounded_rectangle(
            self,
            1, 1,
            self.width - 1,
            self.height - 1,
            radius=self.radius,
            fill=self.bg_color,
            outline=self.bg_color
        )

        self.create_text(
            self.width / 2,
            self.height / 2,
            text=self.text,
            fill=self.text_color,
            font=self.font
        )

    def set_size(self, width, height):
        """Resize the button when the window changes size."""

        self.width = max(1, int(width))
        self.height = max(1, int(height))

        self.config(
            width=self.width,
            height=self.height
        )

        self.draw_button()

    def on_enter(self, event=None):
        self.itemconfigure(
            1,
            fill=self.hover_color,
            outline=self.hover_color
        )

    def on_leave(self, event=None):
        self.draw_button()

    def on_click(self, event=None):
        if self.command:
            self.command()


# ============================================================
# FEEDBACK DETAIL PAGE
# ============================================================

class FeedbackDetailPage:

    def __init__(self, root):

        self.root = root
        self.root.title("FeedbackTrack - Feedback Details")

        # Keep the same window dimensions as conversation.py.
        self.window_width = 460
        self.window_height = 430

        self.root.geometry("460x430")
        self.root.minsize(460, 430)
        self.root.resizable(True, True)

        # Remove the normal title bar to match the screenshot.
        self.root.overrideredirect(True)
        self.root.configure(bg=BG_COLOR)

        self.center_window()

        # The feedback document ID is passed from View Feedback.
        self.document_id = (
            sys.argv[1].strip()
            if len(sys.argv) > 1
            else ""
        )

        # Default values shown while loading the selected record.
        self.category = "Loading..."
        self.student_name = "Student"
        self.feedback_date = "Date unavailable"
        self.feedback_message = "Loading feedback..."
        self.replies = []
        self.database_error = None

        # Get the selected feedback from Firestore.
        self.load_feedback()

        # Main drawing canvas.
        self.canvas = tk.Canvas(
            self.root,
            bg=BG_COLOR,
            highlightthickness=0,
            bd=0
        )
        self.canvas.pack(fill="both", expand=True)

        # Close button matching the screenshot.
        self.close_button = RoundedButton(
            self.root,
            text="Close",
            command=self.close_page,
            width=78,
            height=39,
            bg_color=PRIMARY_COLOR,
            text_color=WHITE,
            hover_color=HOVER_COLOR,
            font=BUTTON_FONT,
            radius=12
        )

        # Place the button on the canvas.
        self.close_window = self.canvas.create_window(
            0, 0,
            window=self.close_button,
            anchor="nw"
        )

        # Redraw the layout if the window is resized.
        self.canvas.bind("<Configure>", self.draw_page)

        # Allow Escape to close the popup.
        self.root.bind("<Escape>", self.close_page)

    # ========================================================
    # CENTRE WINDOW
    # ========================================================

    def center_window(self):

        def position_window():
            try:
                if not self.root.winfo_exists():
                    return

                self.root.update_idletasks()

                screen_width = self.root.winfo_screenwidth()
                screen_height = self.root.winfo_screenheight()

                x = (screen_width - self.window_width) // 2
                y = (screen_height - self.window_height) // 2

                self.root.geometry(
                    f"{self.window_width}x{self.window_height}+{x}+{y}"
                )

                self.root.lift()

            except tk.TclError:
                pass

        # Position the popup after Tkinter finishes setting it up.
        self.root.after_idle(position_window)

    # ========================================================
    # FORMAT DATABASE TIMESTAMP
    # ========================================================

    def format_date(self, value):
        """Format dates and timestamps like Manage Status."""

        if value is None or value == "":
            return "Date unavailable"

        # Firestore Timestamp and datetime objects.
        if hasattr(value, "strftime"):
            return value.strftime("%d %b %Y %I:%M %p")

        # Support timestamps stored as numbers.
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            try:
                timestamp = float(value)

                # Convert milliseconds to seconds if necessary.
                if abs(timestamp) > 100000000000:
                    timestamp /= 1000

                return datetime.fromtimestamp(timestamp).strftime(
                    "%d %b %Y %I:%M %p"
                )
            except (ValueError, TypeError, OverflowError, OSError):
                return str(value)

        # Support Firestore timestamp dictionaries.
        if isinstance(value, dict):
            seconds = value.get("seconds", value.get("_seconds"))

            if seconds is not None:
                try:
                    timestamp = float(seconds)
                    parsed_date = datetime.fromtimestamp(timestamp)

                    return parsed_date.strftime(
                        "%d %b %Y %I:%M %p"
                    )
                except (ValueError, TypeError, OverflowError, OSError):
                    return str(value)

        # Support dates and timestamps stored as strings.
        if isinstance(value, str):
            value = value.strip()

            if not value:
                return "Date unavailable"

            # Try ISO format first.
            try:
                parsed_date = datetime.fromisoformat(
                    value.replace("Z", "+00:00")
                )

                return parsed_date.strftime("%d %b %Y %I:%M %p")

            except ValueError:
                pass

            # Try common date and timestamp formats.
            formats = [
                "%d %b %Y %H:%M:%S",
                "%d %b %Y %H:%M",
                "%d %b %Y %I:%M %p",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M",
                "%d/%m/%Y %H:%M:%S",
                "%d/%m/%Y %H:%M",
                "%d %b %Y",
                "%Y-%m-%d",
                "%d/%m/%Y"
            ]

            for date_format in formats:
                try:
                    parsed_date = datetime.strptime(
                        value,
                        date_format
                    )

                    # Keep the timestamp format consistent.
                    if (
                        "%H" in date_format
                        or "%I" in date_format
                    ):
                        return parsed_date.strftime(
                            "%d %b %Y %I:%M %p"
                        )

                    return parsed_date.strftime("%d %b %Y")

                except ValueError:
                    continue

            # Keep the original value if its format is unknown.
            return value

        return str(value)

    # ========================================================
    # LOAD THE SELECTED FEEDBACK
    # ========================================================

    def load_feedback(self):

        if db is None:
            self.database_error = (
                "Firebase could not be initialized."
            )
            self.category = "Other"
            self.feedback_message = (
                "Unable to connect to the database."
            )
            return

        if not self.document_id:
            self.database_error = (
                "No feedback document ID was provided."
            )
            self.category = "Other"
            self.feedback_message = (
                "Please open this page from View Feedback."
            )
            return

        try:
            # Retrieve only the feedback selected by the admin.
            document_ref = (
                db.collection("feedback")
                .document(self.document_id)
            )

            document = document_ref.get()

            if not document.exists:
                self.database_error = (
                    "The selected feedback could not be found."
                )
                self.category = "Other"
                self.feedback_message = (
                    "This feedback record no longer exists."
                )
                return

            record = document.to_dict() or {}

            # Read the feedback category.
            self.category = str(
                record.get("category") or "Other"
            )

            # Read the feedback message.
            self.feedback_message = str(
                record.get("feedback")
                or record.get("message")
                or record.get("description")
                or "No feedback message was saved."
            )

            # Read the submission timestamp.
            date_value = (
                record.get("created_at")
                or record.get("timestamp")
                or record.get("submitted_at")
                or record.get("date")
            )

            self.feedback_date = self.format_date(date_value)

            # Try common student-name field names.
            self.student_name = str(
                record.get("student_name")
                or record.get("full_name")
                or record.get("name")
                or record.get("username")
                or record.get("student")
                or "Student"
            )

            # If the feedback only stores a student UID,
            # try retrieving the student's profile from users.
            if self.student_name == "Student":

                student_uid = (
                    record.get("user_uid")
                    or record.get("student_uid")
                    or record.get("uid")
                    or record.get("userId")
                    or ""
                )

                if student_uid:
                    try:
                        user_doc = (
                            db.collection("users")
                            .document(student_uid)
                            .get()
                        )

                        if user_doc.exists:
                            user_data = user_doc.to_dict() or {}

                            self.student_name = str(
                                user_data.get("full_name")
                                or user_data.get("name")
                                or user_data.get("username")
                                or "Student"
                            )

                    except Exception as profile_error:
                        # Keep showing the feedback even if the
                        # student's profile cannot be retrieved.
                        print(
                            "Student profile loading error:",
                            profile_error
                        )

            # Read saved replies, if any.
            replies = record.get("replies", [])

            if isinstance(replies, list):
                self.replies = replies
            else:
                self.replies = []

            # Support older records that use a conversation field.
            old_conversation = record.get("conversation")

            if (
                not self.replies
                and isinstance(old_conversation, str)
                and old_conversation.strip()
                and old_conversation.strip().lower()
                    != "no replies yet"
            ):
                self.replies = [{
                    "sender": "Admin",
                    "message": old_conversation
                }]

        except Exception as error:
            self.database_error = str(error)
            self.category = "Other"
            self.feedback_message = (
                "Unable to load the selected feedback."
            )

            print("Feedback detail loading error:", error)

    # ========================================================
    # DRAW THE PAGE
    # ========================================================

    def draw_page(self, event=None):

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        if width < 100 or height < 100:
            return

        self.canvas.delete("page_content")

        # Main white card with rounded corners.
        create_rounded_rectangle(
            self.canvas,
            3, 3,
            width - 3, height - 3,
            radius=19,
            fill=WHITE,
            outline=WHITE,
            tags="page_content"
        )

        # Keep the same comfortable margins as conversation.py.
        margin = max(22, min(28, width * 0.06))
        content_width = max(150, width - 2 * margin)

        # ----------------------------------------------------
        # Category badge
        # ----------------------------------------------------

        badge_y = max(24, height * 0.075)
        badge_height = 23

        create_rounded_rectangle(
            self.canvas,
            margin,
            badge_y,
            width - margin,
            badge_y + badge_height,
            radius=9,
            fill=BADGE_COLOR,
            outline=BADGE_COLOR,
            tags="page_content"
        )

        self.canvas.create_text(
            margin + 11,
            badge_y + badge_height / 2,
            text=self.category,
            anchor="w",
            fill=PRIMARY_COLOR,
            font=(FONT_FAMILY, 9, "bold"),
            tags="page_content"
        )

        # ----------------------------------------------------
        # Main feedback quotation
        # ----------------------------------------------------

        description_y = badge_y + badge_height + 13

        if self.database_error:
            quote_text = self.feedback_message
            quote_color = "#B42318"
        else:
            quote_text = f'"{self.feedback_message}"'
            quote_color = DARK_TEXT

        self.canvas.create_text(
            margin,
            description_y,
            text=quote_text,
            anchor="nw",
            width=content_width,
            fill=quote_color,
            font=(FONT_FAMILY, 11),
            justify="left",
            tags="page_content"
        )

        # Measure the text to position the next section.
        self.canvas.update_idletasks()

        quote_items = self.canvas.find_withtag("page_content")
        quote_item = quote_items[-1] if quote_items else None

        if quote_item:
            quote_box = self.canvas.bbox(quote_item)
            quote_bottom = (
                quote_box[3] if quote_box else description_y + 20
            )
        else:
            quote_bottom = description_y + 20

        # ----------------------------------------------------
        # Student name
        # ----------------------------------------------------

        submitted_y = quote_bottom + 8

        self.canvas.create_text(
            margin,
            submitted_y,
            text=f"Submitted by {self.student_name}",
            anchor="nw",
            width=content_width,
            fill=LIGHT_TEXT,
            font=(FONT_FAMILY, 9),
            tags="page_content"
        )

        # ----------------------------------------------------
        # Original feedback bubble
        # ----------------------------------------------------

        bubble_y = submitted_y + 29
        bubble_x1 = margin

        # Similar width to the bubble in the reference picture.
        bubble_width = min(content_width, width * 0.65)
        bubble_x2 = bubble_x1 + bubble_width

        # Wrap the feedback text inside the bubble.
        text_width = max(100, bubble_width - 24)

        self.canvas.create_text(
            bubble_x1 + 12,
            bubble_y + 33,
            text=self.feedback_message,
            anchor="nw",
            width=text_width,
            fill=DARK_TEXT,
            font=(FONT_FAMILY, 9),
            justify="left",
            tags="page_content"
        )

        # Measure the feedback message so the bubble fits it.
        self.canvas.update_idletasks()

        text_items = self.canvas.find_withtag("page_content")
        message_item = text_items[-1] if text_items else None

        if message_item:
            message_box = self.canvas.bbox(message_item)
            message_bottom = (
                message_box[3]
                if message_box
                else bubble_y + 55
            )
        else:
            message_bottom = bubble_y + 55

        bubble_height = max(
            66,
            message_bottom - bubble_y + 10
        )

        # Draw the bubble behind its text.
        bubble = create_rounded_rectangle(
            self.canvas,
            bubble_x1,
            bubble_y,
            bubble_x2,
            bubble_y + bubble_height,
            radius=14,
            fill=BUBBLE_COLOR,
            outline="#E9E5FC",
            tags="page_content"
        )

        # Place the bubble behind the message and date.
        self.canvas.tag_lower(bubble, "page_content")
        self.canvas.tag_raise(bubble)

        # Redraw the message above the bubble.
        self.canvas.create_text(
            bubble_x1 + 12,
            bubble_y + 33,
            text=self.feedback_message,
            anchor="nw",
            width=text_width,
            fill=DARK_TEXT,
            font=(FONT_FAMILY, 9),
            justify="left",
            tags="page_content"
        )

        # Student name and date inside the bubble.
        self.canvas.create_text(
            bubble_x1 + 12,
            bubble_y + 14,
            text=f"{self.student_name} · {self.feedback_date}",
            anchor="w",
            fill=LIGHT_TEXT,
            font=(FONT_FAMILY, 8, "bold"),
            tags="page_content"
        )

        # ----------------------------------------------------
        # Reply status
        # ----------------------------------------------------

        replies_y = bubble_y + bubble_height + 12

        if self.database_error:
            reply_status = "Feedback details could not be loaded."
            reply_color = "#B42318"

        elif not self.replies:
            reply_status = "No replies yet."
            reply_color = LIGHT_TEXT

        else:
            reply_status = "Replies available in Manage Status."
            reply_color = LIGHT_TEXT

        self.canvas.create_text(
            margin,
            replies_y,
            text=reply_status,
            anchor="nw",
            fill=reply_color,
            font=(FONT_FAMILY, 9, "italic"),
            tags="page_content"
        )

        # Short instruction shown in the reference picture.
        if not self.database_error:
            self.canvas.create_text(
                margin,
                replies_y + 28,
                text="To reply, use Manage Status.",
                anchor="nw",
                fill=LIGHT_TEXT,
                font=(FONT_FAMILY, 8),
                tags="page_content"
            )

        # ----------------------------------------------------
        # Close button
        # ----------------------------------------------------

        close_width = min(78, content_width)
        close_height = 39

        # Keep the button near the bottom-left of the card.
        close_x = margin
        close_y = height - 64

        self.close_button.set_size(
            close_width,
            close_height
        )

        self.canvas.coords(
            self.close_window,
            close_x,
            close_y
        )

    # ========================================================
    # CLOSE PAGE
    # ========================================================

    def close_page(self, event=None):
        self.root.destroy()


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    root = tk.Tk()
    app = FeedbackDetailPage(root)
    root.mainloop()
