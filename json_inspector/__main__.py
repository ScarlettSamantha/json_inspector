#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

from PyQt6.QtGui import QGuiApplication, QIcon, QWindow

sys.path.insert(0, os.path.dirname(__file__))

from manager import JsonManager

from argparse import ArgumentParser, Namespace
from PyQt6 import QtWidgets
from helper import Helper


def main() -> None:
    parser = ArgumentParser(description="Inspect JSON file with GUI")
    parser.add_argument("path", nargs="?")
    a: Namespace = parser.parse_args()

    app = QtWidgets.QApplication(sys.argv)
    icon = QIcon(str((Helper.assets_path() / "application_icon_512.png").resolve()))
    app.setWindowIcon(icon)
    app.setDesktopFileName("Json Inspector")
    QGuiApplication.setDesktopFileName("Json Inspector")

    manager = JsonManager(a.path if a.path else None)
    win = manager.gui
    win.show()
    win.setWindowIcon(icon)
    QGuiApplication.setWindowIcon(icon)
    QGuiApplication.setApplicationName("Json Inspector")
    QGuiApplication.setDesktopFileName("Json Inspector")
    wh: QWindow | None = win.windowHandle()  # for wayland support
    if wh:
        wh.setIcon(icon)
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
