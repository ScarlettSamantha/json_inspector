from typing import TYPE_CHECKING
from PyQt6 import QtCore

from signals import SearchSignals

if TYPE_CHECKING:
    from manager import JsonManager


class SearchWorker(QtCore.QRunnable):
    def __init__(self, manager: "JsonManager", term: str):
        super().__init__()
        self.signals = SearchSignals()
        self.manager: "JsonManager" = manager
        self.term: str = term

    def run(self) -> None:
        matches = self.manager.find_paths_in_data(self.term)
        self.signals.finished.emit(matches)
