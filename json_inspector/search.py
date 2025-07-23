from typing import List, Tuple, Union, TYPE_CHECKING
from PyQt6 import QtWidgets, QtCore
from search_worker import SearchWorker

if TYPE_CHECKING:
    from manager import JsonManager


class Search(QtCore.QObject):
    def __init__(self, manager: "JsonManager", threadpool: QtCore.QThreadPool) -> None:
        super().__init__()
        self._manager: "JsonManager" = manager
        self._gui = manager.gui
        self._threadpool: QtCore.QThreadPool = threadpool
        self._matches: List[Tuple[Union[str, int], ...]] = []
        self._current_index: int = -1

    def perform_search(self, term: str) -> None:
        term = term.strip().lower()
        if not term:
            return self.clear()

        dlg = QtWidgets.QProgressDialog("Searching…", None, 0, 0, self._gui)
        dlg.setWindowTitle("Please wait")
        dlg.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
        dlg.setCancelButton(None)
        dlg.setMinimumDuration(0)
        dlg.show()

        worker = SearchWorker(self._manager, term)
        worker.signals.finished.connect(lambda matches: self._on_search_finished(matches, dlg))  # type: ignore
        self._threadpool.start(worker)  #    type: ignore

    def clear(self) -> None:
        self._matches.clear()
        self._current_index = -1
        self._gui.match_label.setText("0/0")
        self._gui.tree.clearSelection()

    def step(self, delta: int) -> None:
        if not self._matches:
            return
        self._current_index = (self._current_index + (delta or 1)) % len(self._matches)
        self._goto_current()

    def _on_search_finished(
        self,
        matches: List[Tuple[Tuple[Union[str, int], ...], str]],
        dlg: QtWidgets.QProgressDialog,
    ) -> None:
        dlg.close()
        self._matches = [path for path, _ in matches]
        total = len(self._matches)
        self._current_index = -1
        self._gui.match_label.setText(f"0/{total}")
        if total:
            self.step(0)

    def _goto_current(self) -> None:
        idx = self._current_index
        path = self._matches[idx]
        item: QtWidgets.QTreeWidgetItem | None = self._gui.item_for_path(path=path)
        if not item:
            return

        parent: QtWidgets.QTreeWidgetItem | None = item.parent()
        while parent:
            self._gui.tree.expandItem(parent)
            parent = parent.parent()

        self._gui.tree.setCurrentItem(item)
        self._gui.tree.scrollToItem(item)
        self._gui.match_label.setText(f"{idx + 1}/{len(self._matches)}")
