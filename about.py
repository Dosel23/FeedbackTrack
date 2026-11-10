
import tkinter as tk


# ============================================================
# FeedbackTrack - About Page
# File name: about.py
#
# Features:
#   1. Uses the same FeedbackTrack colors and fonts
#   2. Rounded white information card
#   3. Three feedback stages: Submit, Reviewed, Resolved
#   4. Rounded purple Close button
#   5. No standard title bar or window controls
#   6. Responsive layout when resizing the window
#   7. Closes using the Close button or Escape key
#   8. Appears above other windows and in the screen centre
#   9. Works when opened from different application pages
# ============================================================


# ==============================
# Color Palette
# ==============================

BG_COLOR = "#F3F2FC"
PRIMARY_COLOR = "#6C63FF"
DARK_TEXT = "#1E1B2E"
LIGHT_TEXT = "#6B6880"
WHITE = "#FFFFFF"
TILE_COLOR = "#F3F2FC"


# ==============================
# Font Settings
# ==============================

FONT_FAMILY = "Segoe UI"

SMALL_FONT = (FONT_FAMILY, 11)
BODY_FONT = (FONT_FAMILY, 12)
HEADING_FONT = (FONT_FAMILY, 18, "bold")
STAGE_FONT = (FONT_FAMILY, 10, "bold")
ICON_FONT = ("Segoe UI Emoji", 17)


# ==============================
# Rounded Rectangle Helper
# ==============================

def create_rounded_rectangle(
    canvas, x1, y1, x2, y2, radius=18, **kwargs
):
    """Draw a rounded rectangle on a Tkinter Canvas."""

    radius = max(
        0,
        min(radius, (x2 - x1) / 2, (y2 - y1) / 2)
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


# ==============================
# Rounded Button
# ==============================

class RoundedButton(tk.Canvas):
    """A custom rounded button for FeedbackTrack."""

    def __init__(
        self,
        parent,
        text="Close",
        command=None,
        width=78,
        height=38,
        bg_color=PRIMARY_COLOR,
        text_color=WHITE,
        hover_color="#554BEF",
        font=(FONT_FAMILY, 10, "bold")
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
        self.font = font

        self.button_shape = create_rounded_rectangle(
            self,
            1, 1,
            width - 1, height - 1,
            radius=12,
            fill=self.bg_color,
            outline=self.bg_color
        )

        self.button_text = self.create_text(
            width / 2,
            height / 2,
            text=self.text,
            fill=self.text_color,
            font=self.font
        )

        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)

    def on_enter(self, event=None):

        self.itemconfigure(
            self.button_shape,
            fill=self.hover_color,
            outline=self.hover_color
        )

    def on_leave(self, event=None):

        self.itemconfigure(
            self.button_shape,
            fill=self.bg_color,
            outline=self.bg_color
        )

    def on_click(self, event=None):

        if self.command:
            self.command()


# ==============================
# About Page Application
# ==============================

class AboutPage:

    def __init__(self, root):

        self.root = root

        # ------------------------------
        # Window Configuration
        # ------------------------------

        self.root.title("FeedbackTrack - About")

        # Initial window size.
        self.window_width = 460
        self.window_height = 430

        # Hide the window while setting its position.
        # This prevents it from appearing at the left first.
        self.root.withdraw()

        self.root.geometry(
            f"{self.window_width}x{self.window_height}"
        )

        # Minimum window size.
        self.root.minsize(380, 360)

        # Remove the standard title bar.
        self.root.overrideredirect(True)

        # Allow resizing.
        self.root.resizable(True, True)

        self.root.configure(bg=BG_COLOR)

        # Keep About in front while it is open.
        self.root.attributes("-topmost", True)

        # ------------------------------
        # Main Canvas
        # ------------------------------

        self.canvas = tk.Canvas(
            self.root,
            bg=BG_COLOR,
            highlightthickness=0,
            bd=0
        )

        self.canvas.pack(
            fill="both",
            expand=True
        )

        # ------------------------------
        # Feedback Stages
        # ------------------------------

        self.stages = [
            {"icon": "📝", "title": "Submit"},
            {"icon": "👀", "title": "Reviewed"},
            {"icon": "✅", "title": "Resolved"}
        ]

        # ------------------------------
        # Description
        # ------------------------------

        self.description = (
            "FeedbackTrack lets students submit feedback "
            "about college life and follow it through three "
            "simple stages, so nothing gets submitted and "
            "forgotten."
        )

        # ------------------------------
        # Close Button
        # ------------------------------

        self.close_button = RoundedButton(
            self.root,
            text="Close",
            command=self.close_page,
            width=78,
            height=38
        )

        self.close_window = self.canvas.create_window(
            72,
            368,
            window=self.close_button,
            width=78,
            height=38
        )

        # Redraw the page whenever the window changes size.
        self.canvas.bind(
            "<Configure>",
            self.draw_page
        )

        # Allow Escape to close the page.
        self.root.bind(
            "<Escape>",
            self.close_page
        )

        # Position and display the window in one opening step.
        # The window stays hidden until its position is set.
        self.root.after_idle(self.show_centered_window)

    # ==============================
    # Position and Show the Window
    # ==============================

    def show_centered_window(self):

        try:
            if not self.root.winfo_exists():
                return

            # Process pending layout requests while hidden.
            self.root.update_idletasks()

            # Calculate the centre using the screen dimensions.
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()

            x = max(
                0,
                (screen_width - self.window_width) // 2
            )

            y = max(
                0,
                (screen_height - self.window_height) // 2
            )

            # Set the final position before showing the window.
            self.root.geometry(
                f"{self.window_width}x{self.window_height}+{x}+{y}"
            )

            # Process the position while the window is hidden.
            self.root.update_idletasks()

            # Show About only after its position is ready.
            self.root.deiconify()
            self.root.lift()
            self.root.attributes("-topmost", True)

        except tk.TclError:
            pass

    # ==============================
    # Draw / Redraw Page
    # ==============================

    def draw_page(self, event=None):

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        if width < 100 or height < 100:
            return

        self.canvas.delete("page_content")

        # ------------------------------
        # Calculate Responsive Positions
        # ------------------------------

        side_padding = min(
            33,
            max(15, width * 0.07)
        )

        content_width = max(
            1,
            width - (side_padding * 2)
        )

        scale_y = height / 424

        label_y = max(25, 43 * scale_y)
        heading_y = max(52, 81 * scale_y)

        tile_y1 = max(80, 108 * scale_y)
        tile_y2 = max(
            tile_y1 + 50,
            185 * scale_y
        )

        icon_y = tile_y1 + (
            tile_y2 - tile_y1
        ) * 0.38

        title_y = tile_y1 + (
            tile_y2 - tile_y1
        ) * 0.73

        description_y = tile_y2 + max(
            16,
            23 * scale_y
        )

        # ------------------------------
        # Main White Card
        # ------------------------------

        create_rounded_rectangle(
            self.canvas,
            3, 3,
            width - 3, height - 3,
            radius=20,
            fill=WHITE,
            outline=WHITE,
            tags="page_content"
        )

        # ------------------------------
        # About Label
        # ------------------------------

        self.canvas.create_text(
            side_padding,
            label_y,
            text="About",
            anchor="w",
            fill=DARK_TEXT,
            font=SMALL_FONT,
            tags="page_content"
        )

        # ------------------------------
        # Main Heading
        # ------------------------------

        self.canvas.create_text(
            side_padding,
            heading_y,
            text="How FeedbackTrack Works",
            anchor="w",
            fill=DARK_TEXT,
            font=HEADING_FONT,
            tags="page_content"
        )

        # ------------------------------
        # Feedback Stage Tiles
        # ------------------------------

        tile_gap = min(
            12,
            max(6, width * 0.025)
        )

        tile_width = (
            content_width - (2 * tile_gap)
        ) / 3

        for index, stage in enumerate(self.stages):

            x1 = side_padding + index * (
                tile_width + tile_gap
            )

            x2 = x1 + tile_width

            create_rounded_rectangle(
                self.canvas,
                x1, tile_y1,
                x2, tile_y2,
                radius=14,
                fill=TILE_COLOR,
                outline=TILE_COLOR,
                tags="page_content"
            )

            self.canvas.create_text(
                (x1 + x2) / 2,
                icon_y,
                text=stage["icon"],
                fill=DARK_TEXT,
                font=ICON_FONT,
                tags="page_content"
            )

            self.canvas.create_text(
                (x1 + x2) / 2,
                title_y,
                text=stage["title"],
                fill=DARK_TEXT,
                font=STAGE_FONT,
                tags="page_content"
            )

        # ------------------------------
        # Description Text
        # ------------------------------

        self.canvas.create_text(
            side_padding,
            description_y,
            text=self.description,
            anchor="nw",
            width=content_width,
            fill=DARK_TEXT,
            font=BODY_FONT,
            justify="left",
            tags="page_content"
        )

        # ------------------------------
        # Reposition the Close Button
        # ------------------------------

        button_x = side_padding + 39
        button_y = height - 42

        self.canvas.coords(
            self.close_window,
            button_x,
            button_y
        )

        self.canvas.itemconfigure(
            self.close_window,
            width=78,
            height=38
        )

    # ==============================
    # Close the About Page
    # ==============================

    def close_page(self, event=None):

        try:
            if self.root.winfo_exists():
                self.root.destroy()

        except tk.TclError:
            pass


# ==============================
# Run the Application
# ==============================

if __name__ == "__main__":

    root = tk.Tk()

    app = AboutPage(root)

    root.mainloop()
