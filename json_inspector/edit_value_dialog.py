from typing import Any, Optional
import json
import ast

from PyQt6 import QtWidgets, QtCore
from PyQt6.QtGui import QIcon, QRegularExpressionValidator
from PyQt6.QtCore import QRegularExpression
from PyQt6.QtWidgets import (
    QMessageBox,
    QStackedWidget,
    QLineEdit,
    QDoubleSpinBox,
    QTextEdit,
    QComboBox,
    QLabel,
    QDialogButtonBox,
)

from json_inspector.helper import Helper


class EditValueDialog(QtWidgets.QDialog):
    def __init__(
        self,
        parent: QtWidgets.QWidget,
        current_type: str,
        current_val: str,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit Value")
        self.setWindowIcon(QIcon(str((Helper.assets_path() / "application_icon_512.png").resolve())))
        self.setMinimumWidth(500)
        self.setMinimumHeight(200)

        self._raw_initial = current_val

        self._initial_val = self.attempt_cast(current_val, current_type)
        self._prev_type = current_type
        self._initializing = True
        self._last_val: Any = self._initial_val

        form = QtWidgets.QFormLayout(self)
        form.setFormAlignment(QtCore.Qt.AlignmentFlag.AlignTop)

        self.type_cb = QComboBox(self)
        self.type_cb.addItems(["int", "float", "bool", "str", "list", "dict", "NoneType"])  # type: ignore
        self.type_cb.setCurrentText(current_type)
        self.type_cb.currentTextChanged.connect(self._on_type_change)  # type: ignore
        form.addRow("Type:", self.type_cb)

        self.editor_stack = QStackedWidget(self)

        self.int_edit = QLineEdit(self)
        rx = QRegularExpression(r"^[+-]?\d+$")
        self.int_edit.setValidator(QRegularExpressionValidator(rx, self.int_edit))
        self.editor_stack.addWidget(self.int_edit)

        self.float_spin = QDoubleSpinBox(self)
        self.float_spin.setRange(-1e308, 1e308)
        self.float_spin.setDecimals(6)
        self.editor_stack.addWidget(self.float_spin)

        self.bool_cb = QComboBox(self)
        self.bool_cb.addItems(["True", "False"])  # type: ignore
        self.editor_stack.addWidget(self.bool_cb)

        self.text_edit = QTextEdit(self)
        self.text_edit.setMinimumHeight(100)
        self.editor_stack.addWidget(self.text_edit)

        self.list_view = QTextEdit(self)
        self.list_view.setReadOnly(True)
        self.list_view.setMinimumHeight(100)
        self.editor_stack.addWidget(self.list_view)

        self.dict_view = QTextEdit(self)
        self.dict_view.setReadOnly(True)
        self.dict_view.setMinimumHeight(100)
        self.editor_stack.addWidget(self.dict_view)

        self.none_lbl = QLabel("<no value>", self)
        self.none_lbl.setEnabled(False)
        self.editor_stack.addWidget(self.none_lbl)

        form.addRow("Value:", self.editor_stack)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        btns.accepted.connect(self.accept)  # type: ignore[no-untyped-call]
        btns.rejected.connect(self.reject)  # type: ignore[no-untyped-call]
        form.addRow(btns)
        self._ok_button = btns.button(QDialogButtonBox.StandardButton.Ok)

        self._on_type_change(current_type)
        self._initializing = False

    def _on_type_change(self, new_type: str) -> None:
        source = self._raw_initial if (self._initializing and new_type in ("list", "dict")) else self._last_val
        new_val = self.attempt_cast(source, new_type)
        self._last_val = new_val

        assert self._ok_button is not None, "OK button should not be None"

        if new_type == "int":
            self.editor_stack.setCurrentWidget(self.int_edit)
            self.int_edit.setText(str(new_val) if isinstance(new_val, int) else "0")
            self._ok_button.setEnabled(True)

        elif new_type == "float":
            self.editor_stack.setCurrentWidget(self.float_spin)
            self.float_spin.setValue(new_val if isinstance(new_val, float) else 0.0)
            self._ok_button.setEnabled(True)

        elif new_type == "bool":
            self.editor_stack.setCurrentWidget(self.bool_cb)
            self.bool_cb.setCurrentText("True" if bool(new_val) else "False")
            self._ok_button.setEnabled(True)

        elif new_type == "str":
            self.editor_stack.setCurrentWidget(self.text_edit)
            self.text_edit.setPlainText("" if new_val is None else str(new_val))
            self._ok_button.setEnabled(True)

        elif new_type == "list":
            self.editor_stack.setCurrentWidget(self.list_view)
            if self._initializing:
                self.list_view.setPlainText(self._raw_initial)
            else:
                self.list_view.setPlainText(self._pretty(new_val))
            self._ok_button.setEnabled(False)

        elif new_type == "dict":
            self.editor_stack.setCurrentWidget(self.dict_view)
            if self._initializing:
                self.dict_view.setPlainText(self._raw_initial)
            else:
                self.dict_view.setPlainText(self._pretty(new_val))
            self._ok_button.setEnabled(False)

        else:  # NoneType
            self.editor_stack.setCurrentWidget(self.none_lbl)
            self._ok_button.setEnabled(True)

        self._prev_type = new_type

    def _value_from_widget(self, t: str) -> Optional[Any]:
        if t == "int":
            txt = self.int_edit.text().strip()
            return int(txt) if txt else 0
        if t == "float":
            return self.float_spin.value()
        if t == "bool":
            return self.bool_cb.currentText() == "True"
        if t == "str":
            return self.text_edit.toPlainText()

        return self._last_val

    @staticmethod
    def _pretty(val: Any) -> str:
        try:
            return json.dumps(val, indent=2, ensure_ascii=False)
        except Exception:
            return repr(val)

    @staticmethod
    def attempt_cast(val: Any, target: str) -> Any:
        try:
            if target == "int":
                return int(val)
            if target == "float":
                return float(val)
            if target == "bool":
                return str(val).strip().lower() == "true"
            if target == "str":
                return "" if val is None else str(val)
            if target == "list":
                if isinstance(val, list):
                    return val  # type: ignore
                if isinstance(val, str):
                    try:
                        return json.loads(val)
                    except Exception:
                        return ast.literal_eval(val)
            if target == "dict":
                if isinstance(val, dict):
                    return val  # type: ignore
                if isinstance(val, str):
                    try:
                        return json.loads(val)
                    except Exception:
                        return ast.literal_eval(val)
        except Exception:
            pass

        return {  # type: ignore
            "int": 0,
            "float": 0.0,
            "bool": False,
            "str": "",
            "list": [],
            "dict": {},
            "NoneType": None,
        }[target]

    def accept(self) -> None:  # type: ignore[override]
        t = self.type_cb.currentText()
        out = self._value_from_widget(t)
        try:
            _ = {  # type: ignore
                "int": int,
                "float": float,
                "bool": bool,
                "str": str,
                "list": lambda x: list(x),  # type: ignore
                "dict": lambda x: dict(x),  # type: ignore
                "NoneType": lambda x: None,  # type: ignore
            }[t](out)  # type: ignore
        except Exception as e:
            QMessageBox.critical(
                self,
                "Invalid Value",
                f"Cannot convert “{out}” to {t}.\n\nDetails: {e}",
            )
            return

        self.result_value = (t, out)
        super().accept()
