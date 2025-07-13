from save_inspect_gui import JsonInspector

from argparse import ArgumentParser, Namespace
import sys
from PyQt6 import QtWidgets


def main() -> None:
    parser = ArgumentParser(description="Inspect JSON file with GUI")
    parser.add_argument("path", nargs="?")
    a: Namespace = parser.parse_args()

    app = QtWidgets.QApplication(sys.argv)

    if not a.path:
        a.path, _ = QtWidgets.QFileDialog.getOpenFileName(
            None, "Open JSON", filter="JSON files (*.json *.json.gz);;All files (*)"
        )
        if not a.path:
            sys.exit(0)

    win = JsonInspector(a.path)
    win.show()
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
