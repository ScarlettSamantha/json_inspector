from PyQt6 import QtCore, QtWidgets

from signals import WorkerSignals
from helper import Helper
from typing import Any, Tuple, Union


class LoadChildrenWorker(QtCore.QRunnable):
    def __init__(self, parent_item: QtWidgets.QTreeWidgetItem, obj: Any, path: Tuple[Union[str, int], ...]):
        super().__init__()
        self.signals = WorkerSignals()
        self.parent_item: QtWidgets.QTreeWidgetItem = parent_item
        self.obj = obj
        self.path = path

    def run(self) -> None:
        items = Helper.prepare_items(self.obj)

        self.signals.loaded.emit(self.parent_item, items, self.path)
