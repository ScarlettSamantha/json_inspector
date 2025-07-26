from typing import TYPE_CHECKING, Type
from PyQt6.QtWidgets import QCheckBox, QDialog, QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from helper import OSHelper
from settings import Settings

if TYPE_CHECKING:
    from manager import JsonManager


class SettingsDialog(QDialog):
    def __init__(self, manager: "JsonManager", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.settings: Type[Settings] = Settings.get_instance()
        self.manager: "JsonManager" = manager
        self.setWindowTitle("Settings")
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        row_one = QHBoxLayout()
        row_two = QHBoxLayout()

        self.json_file_association_checkbox = QCheckBox("Associate .json files with this app", self)
        self.json_file_association_checkbox.setChecked(OSHelper.is_association_registered())
        self.json_file_association_checkbox.toggled.connect(self._on_association_toggle)  # type: ignore

        row_one.addWidget(self.json_file_association_checkbox)

        self.monitoring_checkbox = QCheckBox("Enable file monitoring", self)
        self.monitoring_checkbox.setChecked(self.settings.monitoring_enabled())
        self.monitoring_checkbox.toggled.connect(self._on_monitoring_toggle)  # type: ignore

        row_two.addWidget(self.monitoring_checkbox)

        layout.addLayout(row_one)
        layout.addLayout(row_two)

        btn_close = QPushButton("Close", self)
        btn_close.clicked.connect(self.accept)  # type: ignore
        layout.addWidget(btn_close)

    def _on_monitoring_toggle(self, checked: bool) -> None:
        self.settings.set_monitoring_enabled(checked)
        if checked:
            self.manager.start_monitoring()
        else:
            self.manager.stop_monitoring()

    def _on_association_toggle(self, checked: bool) -> None:
        if checked:
            OSHelper.register_association()
        else:
            OSHelper.unregister_association()
