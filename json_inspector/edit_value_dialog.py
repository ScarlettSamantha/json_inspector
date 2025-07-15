from typing import Any, Tuple
from PyQt6 import QtWidgets
from PyQt6.QtGui import QIcon

from json_inspector.helper import Helper


class EditValueDialog(QtWidgets.QDialog):
    def __init__(self, parent: QtWidgets.QWidget, current_type: str, current_val: str) -> None:
        super().__init__(parent)
        self.application_icon = QIcon(str((Helper.assets_path() / "application_icon_512.png").resolve()))
        self.setWindowTitle("Edit Value")
        self.setWindowIcon(self.application_icon)
        self.result_value: Tuple[str, Any] = (current_type, current_val)

        self.setMinimumWidth(500)
        self.setMinimumHeight(150)

        layout = QtWidgets.QFormLayout(self)

        self.type_cb = QtWidgets.QComboBox(self)
        self.type_cb.addItems(["int", "float", "bool", "str", "NoneType"])  # type: ignore
        self.type_cb.setCurrentText(current_type)
        layout.addRow("Type:", self.type_cb)

        self.val_edit = QtWidgets.QLineEdit(str(current_val), self)
        layout.addRow("Value:", self.val_edit)

        btn_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self.accept)  # type: ignore
        btn_box.rejected.connect(self.reject)  # type: ignore
        layout.addRow(btn_box)

    def accept(self) -> None:  # type: ignore[override]
        t = self.type_cb.currentText()
        raw = self.val_edit.text().strip().replace("'", "").replace('"', "")
        if t == "int":
            val = int(raw)
        elif t == "float":
            val = float(raw)
        elif t == "bool":
            val = raw.lower() == "true"
        elif t == "NoneType":
            val = None
        else:
            val = raw
        self.result_value = (t, val)
        super().accept()
