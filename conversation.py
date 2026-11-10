
import tkinter as tk
from tkinter import messagebox
import sys
import os
from datetime import datetime

# Use the existing Firebase connection.
try:
    from firebase_config import db
except Exception as error:
    db = None
    FIREBASE_IMPORT_ERROR = str(error)
else:
    FIREBASE_IMPORT_ERROR = None


# ============================================================
# FeedbackTrack - Conversation Page
# Loads and saves the selected conversation using Firestore.
# ============================================================

BG_COLOR = "#F3F2FC"
PRIMARY_COLOR = "#6C63FF"
HOVER_COLOR = "#554BEF"
DARK_TEXT = "#1E1B2E"
LIGHT_TEXT = "#6B6880"
WHITE = "#FFFFFF"
BORDER_COLOR = "#E0DCFB"
BUBBLE_COLOR = "#F2F0FF"

FONT_FAMILY = "Segoe UI"
SMALL_FONT = (FONT_FAMILY, 10)
BODY_FONT = (FONT_FAMILY, 11)
BUTTON_FONT = (FONT_FAMILY, 10, "bold")


# ============================================================
# DATE FORMAT
# Uses the same timestamp format as Feedback Detail.
# Example: 14 Oct 2026 02:35 PM
# ============================================================

def format_reply_date(value):
    if not value:
        return ""

    # Firestore timestamps can be datetime objects.
    if hasattr(value, "strftime"):
        try:
            return value.strftime("%d %b %Y %I:%M %p")
        except (ValueError, TypeError):
            pass

    # Support existing date and timestamp strings.
    if isinstance(value, str):
        value = value.strip()

        if not value:
            return ""

        # Try formats that include the time first.
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

        # Date-only values should remain date-only.
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

        # Keep an unfamiliar saved date instead of hiding it.
        return value

    return str(value)


# ============================================================
# ROUNDED RECTANGLE
# ============================================================

def create_rounded_rectangle(canvas, x1, y1, x2, y2, radius=15, **kwargs):
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
        self.delete("all")

        if self.border_color:
            create_rounded_rectangle(
                self, 1, 1,
                self.width - 1, self.height - 1,
                radius=self.radius,
                fill=self.border_color,
                outline=self.border_color
            )

            create_rounded_rectangle(
                self, 2, 2,
                self.width - 2, self.height - 2,
                radius=max(1, self.radius - 1),
                fill=self.bg_color,
                outline=self.bg_color
            )
        else:
            create_rounded_rectangle(
                self, 1, 1,
                self.width - 1, self.height - 1,
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
        self.width = max(1, int(width))
        self.height = max(1, int(height))

        self.config(
            width=self.width,
            height=self.height
        )

        self.draw_button()

    def on_enter(self, event=None):
        if not self.border_color:
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
# CONVERSATION PAGE
# ============================================================

class ConversationPage:
    def __init__(self, root):
        self.root = root
        self.root.title("FeedbackTrack - Conversation")

        self.window_width = 460
        self.window_height = 430

        self.root.geometry("460x430")
        self.root.minsize(460, 430)
        self.root.overrideredirect(True)
        self.root.resizable(True, True)
        self.root.configure(bg=BG_COLOR)

        self.center_window()

        # Receive the selected feedback document ID.
        self.document_id = (
            sys.argv[1].strip()
            if len(sys.argv) > 1
            else ""
        )

        # Receive the logged-in student's UID.
        self.user_uid = (
            sys.argv[2].strip()
            if len(sys.argv) > 2 and sys.argv[2].strip()
            else os.environ.get(
                "FEEDBACKTRACK_STUDENT_UID", ""
            ).strip()
        )

        self.category = "Loading..."
        self.feedback_date = ""
        self.feedback_message = "Loading feedback..."
        self.replies = []
        self.database_error = None

        # The sender name shown for this student's replies.
        self.student_display_name = "Anonymous"

        # Load the selected feedback from Firestore.
        self.load_conversation()

        # Main canvas.
        self.canvas = tk.Canvas(
            self.root,
            bg=BG_COLOR,
            highlightthickness=0,
            bd=0
        )
        self.canvas.pack(fill="both", expand=True)

        # Reply text field.
        self.reply_frame = tk.Frame(
            self.root,
            bg=WHITE,
            highlightthickness=1,
            highlightbackground=BORDER_COLOR
        )

        self.reply_text = tk.Text(
            self.reply_frame,
            font=BODY_FONT,
            fg=DARK_TEXT,
            bg=WHITE,
            relief="flat",
            bd=0,
            wrap="word",
            undo=True,
            padx=8,
            pady=7,
            height=2,
            insertbackground=PRIMARY_COLOR
        )
        self.reply_text.pack(
            fill="both",
            expand=True,
            padx=3,
            pady=3
        )

        # Send button.
        self.send_button = RoundedButton(
            self.root,
            text="Send",
            command=self.send_reply,
            width=64,
            height=34,
            bg_color=PRIMARY_COLOR,
            text_color=WHITE,
            hover_color=HOVER_COLOR,
            font=BUTTON_FONT,
            radius=10
        )

        # Close button.
        self.close_button = RoundedButton(
            self.root,
            text="Close",
            command=self.close_page,
            width=360,
            height=40,
            bg_color=WHITE,
            text_color=LIGHT_TEXT,
            hover_color=WHITE,
            border_color=BORDER_COLOR,
            font=(FONT_FAMILY, 10, "bold"),
            radius=12
        )

        # Position the widgets on the canvas.
        self.reply_window = self.canvas.create_window(
            0, 0,
            window=self.reply_frame,
            anchor="nw"
        )

        self.send_window = self.canvas.create_window(
            0, 0,
            window=self.send_button,
            anchor="nw"
        )

        self.close_window = self.canvas.create_window(
            0, 0,
            window=self.close_button,
            anchor="nw"
        )

        self.canvas.bind("<Configure>", self.draw_page)
        self.root.bind("<Escape>", self.close_page)
        self.root.bind("<Control-Return>", self.send_reply)

        self.reply_text.focus_set()

    # ========================================================
    # CENTRE WINDOW
    # ========================================================

    def center_window(self):
        # Update the window information before calculating its position.
        self.root.update_idletasks()

        # Get the full screen dimensions.
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Use the existing conversation window dimensions.
        window_width = self.window_width
        window_height = self.window_height

        # Calculate the centre position of the screen.
        x = max(0, (screen_width - window_width) // 2)
        y = max(0, (screen_height - window_height) // 2)

        # Place the conversation window in the centre.
        self.root.geometry(
            f"{window_width}x{window_height}+{x}+{y}"
        )

        # Apply the new position immediately.
        self.root.update_idletasks()

    # ========================================================
    # FIND THE STUDENT'S DISPLAY NAME
    # ========================================================

    def get_student_display_name(self, record):
        # If the feedback was explicitly marked anonymous,
        # do not reveal the student's profile name.
        anonymous_value = (
            record.get("is_anonymous")
            if "is_anonymous" in record
            else record.get(
                "anonymous",
                record.get(
                    "isAnonymous",
                    record.get("anonymous_feedback", False)
                )
            )
        )

        if isinstance(anonymous_value, str):
            anonymous_value = (
                anonymous_value.strip().lower()
                in ("true", "yes", "1")
            )

        if anonymous_value is True:
            return "Anonymous"

        # Prefer a name saved directly with the feedback.
        possible_names = [
            record.get("student_name"),
            record.get("full_name"),
            record.get("display_name"),
            record.get("name"),
        ]

        for name in possible_names:
            if isinstance(name, str) and name.strip():
                cleaned_name = name.strip()

                if cleaned_name.lower() == "anonymous":
                    return "Anonymous"

                return cleaned_name

        # If the feedback record has no name, check the
        # student's Firestore profile using the document UID.
        owner_uid = (
            record.get("user_uid")
            or record.get("student_uid")
            or record.get("uid")
            or record.get("userId")
            or self.user_uid
        )

        if db is not None and owner_uid:
            try:
                profile_snapshot = (
                    db.collection("users")
                    .document(owner_uid)
                    .get()
                )

                if profile_snapshot.exists:
                    profile = profile_snapshot.to_dict() or {}

                    profile_name = (
                        profile.get("full_name")
                        or profile.get("display_name")
                        or profile.get("name")
                    )

                    if (
                        isinstance(profile_name, str)
                        and profile_name.strip()
                    ):
                        return profile_name.strip()

            except Exception as error:
                # The conversation can still work if the
                # profile lookup fails.
                print("Student profile lookup error:", error)

        # Do not display a username or UID as a real name.
        return "Anonymous"

    # ========================================================
    # LOAD THE SELECTED FEEDBACK
    # ========================================================

    def load_conversation(self):
        if db is None:
            self.database_error = (
                "Firebase could not be initialized. "
                + str(FIREBASE_IMPORT_ERROR or "")
            )
            self.feedback_message = (
                "Unable to connect to the database."
            )
            return

        if not self.document_id:
            self.database_error = (
                "No feedback document ID was provided."
            )
            self.feedback_message = (
                "Please open this page from My Feedback."
            )
            return

        try:
            document = (
                db.collection("feedback")
                .document(self.document_id)
                .get()
            )

            if not document.exists:
                self.database_error = (
                    "The selected feedback could not be found."
                )
                self.feedback_message = (
                    "This feedback record no longer exists."
                )
                return

            record = document.to_dict() or {}

            # Check ownership when the document has a student UID.
            owner_uid = (
                record.get("user_uid")
                or record.get("student_uid")
                or record.get("uid")
                or record.get("userId")
                or ""
            )

            if (
                self.user_uid
                and owner_uid
                and owner_uid != self.user_uid
            ):
                self.database_error = (
                    "This feedback does not belong to "
                    "the logged-in student."
                )
                self.feedback_message = (
                    "You cannot open this feedback."
                )
                return

            self.category = record.get("category", "Other")

            self.feedback_message = (
                record.get("feedback")
                or record.get("message")
                or "No feedback message was saved."
            )

            # Get the student's name for replies.
            self.student_display_name = (
                self.get_student_display_name(record)
            )

            # Prefer the actual timestamp when available.
            # This allows the date to include hours and minutes.
            date_value = (
                record.get("created_at")
                or record.get("timestamp")
                or record.get("submitted_at")
                or record.get("date", "")
            )

            if date_value:
                self.feedback_date = format_reply_date(date_value)
            else:
                self.feedback_date = "Date unavailable"

            # Replies are stored as a list of dictionaries.
            replies = record.get("replies", [])

            if isinstance(replies, list):
                self.replies = replies
            else:
                self.replies = []

            # Support the older conversation field.
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
                    "text": old_conversation,
                    "date": ""
                }]

        except Exception as error:
            self.database_error = str(error)
            self.feedback_message = (
                "Unable to load the selected feedback."
            )
            print("Conversation loading error:", error)

    # ========================================================
    # DRAW THE PAGE
    # ========================================================

    def draw_page(self, event=None):
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        if width < 100 or height < 100:
            return

        self.canvas.delete("page_content")

        # Main white card.
        create_rounded_rectangle(
            self.canvas,
            3, 3,
            width - 3, height - 3,
            radius=19,
            fill=WHITE,
            outline=WHITE,
            tags="page_content"
        )

        margin = max(22, min(28, width * 0.06))
        content_width = max(150, width - 2 * margin)

        # Category badge.
        badge_y = max(24, height * 0.075)
        badge_height = 23

        create_rounded_rectangle(
            self.canvas,
            margin,
            badge_y,
            width - margin,
            badge_y + badge_height,
            radius=9,
            fill="#EEEDFF",
            outline="#EEEDFF",
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

        # Description.
        description_y = badge_y + badge_height + 12

        self.canvas.create_text(
            margin,
            description_y,
            text="Your feedback and conversation with the admin.",
            anchor="nw",
            width=content_width,
            fill=LIGHT_TEXT,
            font=(FONT_FAMILY, 9),
            justify="left",
            tags="page_content"
        )

        # Original feedback bubble.
        bubble_y = description_y + 31
        bubble_x1 = margin
        bubble_x2 = width - margin
        bubble_height = 67

        create_rounded_rectangle(
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

        self.canvas.create_text(
            bubble_x1 + 12,
            bubble_y + 14,
            text=f"You · {self.feedback_date}",
            anchor="w",
            fill=LIGHT_TEXT,
            font=(FONT_FAMILY, 8, "bold"),
            tags="page_content"
        )

        self.canvas.create_text(
            bubble_x1 + 12,
            bubble_y + 38,
            text=self.feedback_message,
            anchor="nw",
            width=max(100, bubble_x2 - bubble_x1 - 24),
            fill=DARK_TEXT,
            font=(FONT_FAMILY, 9),
            tags="page_content"
        )

        # Show saved replies in the conversation area.
        replies_y = bubble_y + bubble_height + 10

        if self.database_error:
            display_text = "Database error: " + self.database_error
            display_color = "#B42318"

        elif not self.replies:
            display_text = "No replies yet."
            display_color = LIGHT_TEXT

        else:
            # Keep the newest replies visible in this compact window.
            visible_replies = self.replies[-3:]
            reply_lines = []

            for item in visible_replies:
                if isinstance(item, dict):
                    # Support both old and new reply field names.
                    sender = item.get("sender", "Admin")
                    message = item.get(
                        "message",
                        item.get("text", "")
                    )

                    # Prefer a full timestamp before a date-only value.
                    # Manage Status stores the full admin timestamp in
                    # "created_at" and a date-only value in "date".
                    reply_date = ""
                    date_only_fallback = ""

                    timestamp_fields = (
                        "created_at",
                        "timestamp",
                        "submitted_at",
                        "replied_at",
                        "sent_at",
                        "updated_at",
                        "date",
                    )

                    for field in timestamp_fields:
                        timestamp_value = item.get(field)

                        if not timestamp_value:
                            continue

                        formatted_date = format_reply_date(
                            timestamp_value
                        )

                        if not formatted_date:
                            continue

                        # A full timestamp includes AM or PM.
                        if (
                            " AM" in formatted_date
                            or " PM" in formatted_date
                        ):
                            reply_date = formatted_date
                            break

                        # Keep a date-only value as a fallback in case
                        # this older reply has no full timestamp saved.
                        if not date_only_fallback:
                            date_only_fallback = formatted_date

                    if not reply_date:
                        reply_date = date_only_fallback

                    # Replace the old generic Student label
                    # with the student's display name.
                    if (
                        isinstance(sender, str)
                        and sender.strip().lower() == "student"
                    ):
                        sender = self.student_display_name

                    # Manage Status replies may not have a sender
                    # field, so they continue to display as Admin.
                    if not sender:
                        sender = "Admin"

                    line = f"{sender}: {message}"

                    if reply_date:
                        line += f"  ({reply_date})"

                    reply_lines.append(line)

                else:
                    reply_lines.append(str(item))

            display_text = "\n".join(reply_lines)
            display_color = DARK_TEXT

            if len(self.replies) > 3:
                display_text = (
                    f"Showing the latest 3 of "
                    f"{len(self.replies)} replies.\n"
                    + display_text
                )

        # Reserve space above the reply box.
        bottom_margin = max(22, height * 0.07)
        close_height = 40
        close_y = height - bottom_margin - close_height

        reply_height = 58
        reply_y = close_y - 15 - reply_height

        available_reply_height = max(
            25,
            reply_y - replies_y - 8
        )

        self.canvas.create_text(
            margin,
            replies_y,
            text=display_text,
            anchor="nw",
            width=content_width,
            fill=display_color,
            font=(FONT_FAMILY, 9),
            justify="left",
            tags="page_content"
        )

        # Reply text field.
        send_width = min(68, max(58, content_width * 0.22))
        send_height = 34
        gap = 8

        reply_width = max(
            100,
            content_width - send_width - gap
        )

        self.canvas.coords(
            self.reply_window,
            margin,
            reply_y
        )

        self.canvas.itemconfigure(
            self.reply_window,
            width=reply_width,
            height=reply_height
        )

        self.send_button.set_size(
            send_width,
            send_height
        )

        self.canvas.coords(
            self.send_window,
            margin + reply_width + gap,
            reply_y + (reply_height - send_height) / 2
        )

        self.close_button.set_size(
            int(content_width),
            close_height
        )

        self.canvas.coords(
            self.close_window,
            margin,
            close_y
        )

    # ========================================================
    # SAVE A REPLY TO FIRESTORE
    # ========================================================

    def send_reply(self, event=None):
        reply = self.reply_text.get(
            "1.0", "end-1c"
        ).strip()

        if not reply:
            messagebox.showwarning(
                "Empty Reply",
                "Please write a reply before sending.",
                parent=self.root
            )
            self.reply_text.focus_set()
            return "break"

        if db is None or self.database_error:
            messagebox.showerror(
                "Database Error",
                "The conversation could not be saved because "
                "the feedback record was not loaded successfully.",
                parent=self.root
            )
            return "break"

        try:
            document_ref = (
                db.collection("feedback")
                .document(self.document_id)
            )

            # Read the latest document before updating it.
            snapshot = document_ref.get()

            if not snapshot.exists:
                messagebox.showerror(
                    "Feedback Not Found",
                    "This feedback record no longer exists.",
                    parent=self.root
                )
                return "break"

            record = snapshot.to_dict() or {}

            # Check ownership before saving a reply.
            owner_uid = (
                record.get("user_uid")
                or record.get("student_uid")
                or record.get("uid")
                or record.get("userId")
                or ""
            )

            if (
                self.user_uid
                and owner_uid
                and owner_uid != self.user_uid
            ):
                messagebox.showerror(
                    "Access Denied",
                    "You cannot reply to this feedback.",
                    parent=self.root
                )
                return "break"

            current_replies = record.get("replies", [])

            if not isinstance(current_replies, list):
                current_replies = []

            # Save the reply date and time with AM/PM.
            # Keep "text" and "date" for compatibility with
            # the existing Manage Status reply structure.
            new_reply = {
                "sender": self.student_display_name,
                "text": reply,
                "date": datetime.now().strftime(
                    "%d %b %Y %I:%M %p"
                )
            }

            current_replies.append(new_reply)

            document_ref.update({
                "replies": current_replies
            })

            self.replies = current_replies
            self.reply_text.delete("1.0", "end")
            self.draw_page()
            self.reply_text.focus_set()

        except Exception as error:
            print("Error saving conversation reply:", error)

            messagebox.showerror(
                "Could Not Send Reply",
                "Your reply could not be saved to the database.\n\n"
                "Please check your Firebase connection and try again.",
                parent=self.root
            )

        return "break"

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
    app = ConversationPage(root)
    root.mainloop()
