from .save_inspect_gui import JsonInspector
from argparse import ArgumentParser, Namespace
import sys
from tkinter import filedialog


def main():
    parser = ArgumentParser(description="Inspect JSON file with GUI")
    parser.add_argument("path", nargs="?")
    a: Namespace = parser.parse_args()
    if not a.path:
        a.path = filedialog.askopenfilename(title="Open JSON", filetypes=[("JSON files", ".json .json.gz")])
        if not a.path:
            sys.exit(0)
    try:
        JsonInspector(a.path).mainloop()
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
