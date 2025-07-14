from typing import TYPE_CHECKING
from PyQt6 import QtCore

from signals import SearchSignals

if TYPE_CHECKING:
    from gui import JsonInspector


class SearchWorker(QtCore.QRunnable):
    def __init__(self, inspector: "JsonInspector", term: str):
        super().__init__()
        self.signals = SearchSignals()
        self.inspector: "JsonInspector" = inspector
        self.term: str = term

    def run(self) -> None:
        matches = self.inspector.find_paths_in_data(self.term)
        self.signals.finished.emit(matches)
