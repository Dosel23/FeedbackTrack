
import os
import runpy
import sys


def _base_dir():
    return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))


def main():
    base = _base_dir()
    if base not in sys.path:
        sys.path.insert(0, base)

    arguments = sys.argv[1:]
    if arguments and arguments[0].lower().endswith(".py"):
        script = arguments[0]
        extra = arguments[1:]
    else:
        script = os.path.join(base, "landing.py")
        extra = []

    if not os.path.isabs(script) and not os.path.isfile(script):
        script = os.path.join(base, script)
    script = os.path.abspath(script)
    if not os.path.isfile(script):
        try:
            from tkinter import Tk, messagebox
            root = Tk()
            root.withdraw()
            messagebox.showerror("FeedbackTrack", f"Could not find the page:\n{script}")
        except Exception:
            print("Page not found:", script)
        sys.exit(1)

    os.chdir(os.path.dirname(script))
    sys.argv = [script] + extra
    runpy.run_path(script, run_name="__main__")


if __name__ == "__main__":
    main()
