"""Graphical (Tkinter) dialog for choosing which pages to test.

Used by the ``run_playwright_tests`` launcher scripts when invoked in
GUI mode. The page list comes from ``test_config.py``, so it stays in
sync with the CLI mode and with whichever site the config targets.

On success, prints the selected page names (comma separated) to stdout
so the calling shell/batch script can capture them, e.g.:

    PAGE_SELECTION="$(python gui_page_selector.py)"

Exits with status 1 and no output if the dialog is cancelled or closed
without selecting any page.
"""

import sys
import tkinter as tk
from tkinter import ttk

import test_config as config


def main() -> int:
    root = tk.Tk()
    root.title("Select pages to test")

    page_names = list(config.PAGE_PATHS.keys())
    selections = {name: tk.BooleanVar(value=True) for name in page_names}

    ttk.Label(root, text="Choose the pages to run tests against:", padding=10).pack(
        anchor="w"
    )

    for name in page_names:
        ttk.Checkbutton(root, text=name, variable=selections[name]).pack(
            anchor="w", padx=20
        )

    result: list[str] = []

    def on_run() -> None:
        result.extend(name for name in page_names if selections[name].get())
        root.destroy()

    def on_cancel() -> None:
        root.destroy()

    button_row = ttk.Frame(root, padding=10)
    button_row.pack(fill="x")
    ttk.Button(button_row, text="Run selected", command=on_run).pack(side="left")
    ttk.Button(button_row, text="Cancel", command=on_cancel).pack(side="left", padx=10)

    root.protocol("WM_DELETE_WINDOW", on_cancel)
    root.mainloop()

    if not result:
        return 1

    print(",".join(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
