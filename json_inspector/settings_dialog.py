from PyQt6.QtWidgets import QCheckBox, QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from helper import OSHelper


class SettingsDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        row = QHBoxLayout()
        label = QLabel("Associate .json files with this app", self)

        self.checkbox = QCheckBox(self)
        self.checkbox.setChecked(OSHelper.is_association_registered())
        self.checkbox.toggled.connect(self._on_toggle)  # type: ignore

        row.addWidget(label)
        row.addWidget(self.checkbox)

        layout.addLayout(row)

        btn_close = QPushButton("Close", self)
        btn_close.clicked.connect(self.accept)  # type: ignore
        layout.addWidget(btn_close)

    def _on_toggle(self, checked: bool) -> None:
        if checked:
            OSHelper.register_association()
        else:
            OSHelper.unregister_association()
