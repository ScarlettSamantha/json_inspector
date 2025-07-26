import json
from typing import TYPE_CHECKING, Any, Dict, List, Tuple, Union
from edit_value_dialog import EditValueDialog
from about_dialog import AboutDialog
from load_children_worker import LoadChildrenWorker
from settings_dialog import SettingsDialog
from helper import Helper, OSHelper
from search import Search

if TYPE_CHECKING:
    from manager import JsonManager

from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtCore import QModelIndex

COLOR_MAP: Dict[str, str] = {
    "int": "#b58900",
    "float": "#2aa198",
    "bool": "#d33682",
    "str": "#859900",
    "NoneType": "#657b83",
    "dict": "#dc322f",
    "list": "#dc322f",
    "tuple": "#dc322f",
    "set": "#dc322f",
}


class Gui(QtWidgets.QMainWindow):
    def __init__(self, manager: "JsonManager") -> None:
        super().__init__()
        self.manager: "JsonManager" = manager
        self._current_path = manager.path
        self.application_icon = QtGui.QIcon(str((Helper.assets_path() / "application_icon_512.png").resolve()))
        self._cache: Dict[Tuple[Union[str, int], ...], List[Any]] = {}
        self._threadpool: QtCore.QThreadPool | None = QtCore.QThreadPool.globalInstance()
        self._active_workers: list[LoadChildrenWorker] = []

    def load(self) -> None:
        self.setWindowTitle(f"Json Inspector <{self._current_path}>")

        QtCore.QCoreApplication.setApplicationName("Json Inspector")
        QtGui.QGuiApplication.setDesktopFileName("Json Inspector")
        QtGui.QGuiApplication.setWindowIcon(self.application_icon)

        assert self._threadpool is not None, "Thread pool should not be None"

        self._build_ui()

        self._search_controller = Search(self.manager, self._threadpool)

        self.search_btn.clicked.connect(lambda: self._search_controller.perform_search(self.search_edit.text()))  # type: ignore
        self.clear_btn.clicked.connect(self._search_controller.clear)  # type: ignore
        self.prev_btn.clicked.connect(lambda: self._search_controller.step(-1))  # type: ignore
        self.next_btn.clicked.connect(lambda: self._search_controller.step(+1))  # type: ignore

        self.footer_update_clock = QtCore.QTimer(self)
        self.footer_update_clock.timeout.connect(self.update_footer)  # type: ignore
        self.footer_update_clock.start(5000)

        self.setWindowIcon(self.application_icon)
        self.resize(1400, 800)

        self.tree.itemExpanded.connect(self._on_item_expanded)  # type: ignore

        self.populate_tree()

    def _build_ui(self) -> None:
        menu_bar: QtWidgets.QMenuBar | None = self.menuBar()

        assert menu_bar is not None, "Menu bar should not be None"

        file_menu: QtWidgets.QMenu | None = menu_bar.addMenu("File")
        view_menu: QtWidgets.QMenu | None = menu_bar.addMenu("View")
        settings_menu: QtWidgets.QMenu | None = menu_bar.addMenu("Settings")
        about_menu: QtWidgets.QMenu | None = menu_bar.addMenu("About")

        assert file_menu is not None, "File menu should not be None"

        open_action: QtGui.QAction | None = file_menu.addAction("Open…")  # type: ignore
        open_action.setShortcut("Ctrl+O")  # type: ignore
        open_action.triggered.connect(self.open_file)  # type: ignore

        save_action: QtGui.QAction | None = file_menu.addAction("Save")  # type: ignore
        save_action.setShortcut("Ctrl+S")  # type: ignore
        save_action.triggered.connect(self._save_file)  # type: ignore

        save_as_action: QtGui.QAction | None = file_menu.addAction("Save As…")  # type: ignore
        save_as_action.setShortcut("Ctrl+Shift+S")  # type: ignore
        save_as_action.triggered.connect(self._save_as_file)  # type: ignore

        file_menu.addSeparator()

        exit_action: QtGui.QAction | None = file_menu.addAction("Exit")  # type: ignore
        exit_action.setShortcut("Ctrl+Q")  # type: ignore
        exit_action.triggered.connect(self.close)  # type: ignore

        assert view_menu is not None, "View menu should not be None"

        reload_action: QtGui.QAction | None = view_menu.addAction("Reload")  # type: ignore
        reload_action.setShortcut("Ctrl+R")  # type: ignore
        reload_action.triggered.connect(self.reload)  # type: ignore

        clear_action: QtGui.QAction | None = view_menu.addAction("Clear")  # type: ignore
        clear_action.setShortcut("Ctrl+Alt+C")  # type: ignore # We use Ctrl+Alt+C to avoid issues when terminal people who use Ctrl+Shift+C as copy.
        clear_action.triggered.connect(self.clear)  # type: ignore

        view_menu.addSeparator()

        expand_all_action: QtGui.QAction | None = view_menu.addAction("Expand All")  # type: ignore
        expand_all_action.triggered.connect(lambda: self.tree.expandRecursively(QModelIndex(), 20))  # type: ignore

        collapse_all_action: QtGui.QAction | None = view_menu.addAction("Collapse All")  # type: ignore
        collapse_all_action.setShortcut("Ctrl+Shift+E")  # type: ignore
        collapse_all_action.triggered.connect(lambda: self.tree.collapseAll())  # type: ignore

        settings_action: QtGui.QAction | None = settings_menu.addAction("Settings…")  # type: ignore
        settings_action.setShortcut("Ctrl+P")  # type: ignore
        settings_action.triggered.connect(lambda: SettingsDialog(self).exec())  # type: ignore

        about_action = about_menu.addAction("About")  # type: ignore
        about_action.triggered.connect(self.show_about_dialog)  # type: ignore

        tool_bar = QtWidgets.QToolBar()
        self.addToolBar(tool_bar)

        self.search_edit = QtWidgets.QLineEdit()
        self.search_edit.setPlaceholderText("Find key or value…")
        self.search_edit.returnPressed.connect(lambda: self._search_controller.perform_search(self.search_edit.text()))  # type: ignore
        tool_bar.addWidget(self.search_edit)

        self.search_btn = QtWidgets.QPushButton("Search")
        tool_bar.addWidget(self.search_btn)

        self.clear_btn = QtWidgets.QPushButton("Clear")
        tool_bar.addWidget(self.clear_btn)

        self.prev_btn = QtWidgets.QPushButton("◀")
        tool_bar.addWidget(self.prev_btn)

        self.next_btn = QtWidgets.QPushButton("▶")
        tool_bar.addWidget(self.next_btn)

        self.match_label = QtWidgets.QLabel("0/0")
        tool_bar.addWidget(self.match_label)

        splitter = QtWidgets.QSplitter(self)
        self.setCentralWidget(splitter)

        self.tree = QtWidgets.QTreeWidget()
        self.tree.setHeaderLabels(["Key", "Type"])  # type: ignore
        self.tree.header().resizeSection(0, 300)  # type: ignore
        self.tree.itemSelectionChanged.connect(slot=self._on_select)  # type: ignore
        splitter.addWidget(self.tree)

        self.prop_table = QtWidgets.QTableWidget()
        self.prop_table.setColumnCount(3)
        self.prop_table.setHorizontalHeaderLabels(["Key", "Type", "Value"])  # type: ignore
        self.prop_table.horizontalHeader().setStretchLastSection(True)  # type: ignore
        self.prop_table.itemDoubleClicked.connect(self._on_prop_double_click)  # type: ignore
        splitter.addWidget(self.prop_table)
        splitter.setSizes([500, 1000])  #    type: ignore
        self.footer = QtWidgets.QStatusBar()
        self.setStatusBar(self.footer)

        self.loaded_label = QtWidgets.QLabel(f"Loaded {self.manager.get_total_count()} items")
        self.footer.addWidget(self.loaded_label, 1)

        self.memory_usage_label = QtWidgets.QLabel(f"Memory Usage: {OSHelper.get_memory_usage_human()}")
        self.footer.addPermanentWidget(self.memory_usage_label)

    def update_footer(self) -> None:
        total = self.manager.get_total_count(cache=True)
        self.loaded_label.setText(f"Loaded {total} items")
        self.memory_usage_label.setText(f"Memory Usage: {OSHelper.get_memory_usage_human()}")

    def show_about_dialog(self) -> None:
        dlg = AboutDialog(self)
        dlg.exec()

    def populate_tree(self) -> None:
        self.tree.clear()
        root = QtWidgets.QTreeWidgetItem(["root", type(self.manager.data).__name__])
        self.tree.addTopLevelItem(root)
        if isinstance(self.manager.data, (dict, list, tuple, set)):
            placeholder = QtWidgets.QTreeWidgetItem(["Loading...", ""])
            root.addChild(placeholder)
            root.setChildIndicatorPolicy(QtWidgets.QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator)
        self.tree.expandItem(root)

    def _current_obj_from_item(self, item: QtWidgets.QTreeWidgetItem) -> Any:
        keys: List[Union[str, int]] = []
        tmp: QtWidgets.QTreeWidgetItem | None = item

        while tmp is not None and tmp.parent() is not None:
            keys.insert(0, tmp.text(0))
            tmp = tmp.parent()

        return self._get_obj_by_path(tuple(keys))

    def _on_item_expanded(self, item: QtWidgets.QTreeWidgetItem) -> None:
        if item.data(0, QtCore.Qt.ItemDataRole.UserRole) is True:  # type: ignore
            return

        if item.childCount() == 1 and (child := item.child(0)) is not None and child.text(0) == "Loading...":
            item.takeChild(0)

            path: List[str] = []
            tmp = item
            assert tmp is not None, "Item should not be None"

            while tmp is not None and tmp.parent() is not None:
                path.insert(0, tmp.text(0))
                tmp: QtWidgets.QTreeWidgetItem | None = tmp.parent()
            path_tuple: Tuple[str, ...] = tuple(path)

            if path_tuple in self._cache:
                self._add_children(item, self._cache[path_tuple])
                item.setData(0, QtCore.Qt.ItemDataRole.UserRole, True)
                return

            worker = LoadChildrenWorker(item, obj=self._current_obj_from_item(item), path=path_tuple)
            self._active_workers.append(worker)

            def _cleanup_and_dispatch(
                _sig_parent: QtWidgets.QTreeWidgetItem,
                items: List[Tuple[Union[str, int], str, str, bool]],
                path: Tuple[Union[str, int], ...],
                wrk: LoadChildrenWorker = worker,
                parent: QtWidgets.QTreeWidgetItem = item,
            ) -> None:
                try:
                    self._on_children_loaded(parent, items, path)
                finally:
                    self._active_workers.remove(wrk)

            worker.signals.loaded.connect(_cleanup_and_dispatch, QtCore.Qt.ConnectionType.QueuedConnection)  # type: ignore
            self._threadpool.start(worker)  # type: ignore

    @QtCore.pyqtSlot(object, list, tuple)  # type: ignore
    def _on_children_loaded(
        self,
        parent_item: QtWidgets.QTreeWidgetItem,
        items: List[Tuple[Union[str, int], str, str, bool]],
        path_tuple: Tuple[Union[str, int], ...],
    ) -> None:
        self._add_children(parent_item, items)
        parent_item.setData(0, QtCore.Qt.ItemDataRole.UserRole, True)

        for key, typ, val, is_cont in items:  # type: ignore
            if is_cont:
                child_path = path_tuple + (key,)
                child_obj = self._get_obj_by_path(child_path)
                w = LoadChildrenWorker(parent_item.child(key if isinstance(key, int) else 0), child_obj, child_path)  # type: ignore
                w.signals.loaded.connect(self._on_cache_only, QtCore.Qt.ConnectionType.QueuedConnection)  # type: ignore
                self._threadpool.start(w)  # type: ignore

    @QtCore.pyqtSlot(object, list, tuple)  # type: ignore[no-untyped-def]
    def _on_cache_only(
        self,
        parent_item: QtWidgets.QTreeWidgetItem,
        items: List[Tuple[Union[str, int], str, str, bool]],
        path_tuple: Tuple[Union[str, int], ...],
    ) -> None:
        self._cache[path_tuple] = items

    def _add_children(
        self, parent_item: QtWidgets.QTreeWidgetItem, items: List[Tuple[Union[str, int], str, str, bool]]
    ) -> None:
        for key, typ, displayed, is_cont in items:
            child = QtWidgets.QTreeWidgetItem([str(key), typ])

            child.setData(0, QtCore.Qt.ItemDataRole.UserRole, displayed if not is_cont else "")
            if typ in COLOR_MAP:
                c = QtGui.QColor(COLOR_MAP[typ])
                brush = QtGui.QBrush(c)
                child.setForeground(0, brush)
                child.setForeground(1, brush)

            if is_cont:
                placeholder = QtWidgets.QTreeWidgetItem(["Loading...", "", ""])
                child.addChild(placeholder)
                child.setChildIndicatorPolicy(QtWidgets.QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator)

            try:
                parent_item.addChild(child)
            except RuntimeError as e:
                print(f"Error adding child {key} to parent: {e}")
                continue

    def _get_obj_by_path(self, path: Tuple[Union[str, int], ...]) -> Any:
        obj = self.manager.data
        for k in path:
            if isinstance(obj, dict):
                obj = obj[k]  # type: ignore[index]
            else:
                obj = obj[int(k)]  # type: ignore[index]
        return obj  # type: ignore[return-value]

    def _on_select(self) -> None:
        items: List[QtWidgets.QTreeWidgetItem] = self.tree.selectedItems()
        if not items:
            return
        item: QtWidgets.QTreeWidgetItem = items[0]
        obj = self._current_obj_from_item(item)
        self._populate_properties(obj)

    def _populate_properties(self, obj: Any) -> None:
        self.prop_table.clearContents()
        self.prop_table.setRowCount(0)
        if isinstance(obj, dict):
            for i, (k, v) in enumerate(obj.items()):  # type: ignore
                self.prop_table.insertRow(i)
                self.prop_table.setItem(i, 0, QtWidgets.QTableWidgetItem(str(k)))  # type: ignore
                self.prop_table.setItem(i, 1, QtWidgets.QTableWidgetItem(type(v).__name__))  # type: ignore
                self.prop_table.setItem(i, 2, QtWidgets.QTableWidgetItem(str(v)))  # type: ignore

        elif isinstance(obj, (list, tuple, set)):
            for i, v in enumerate(obj):  # type: ignore
                self.prop_table.insertRow(i)
                self.prop_table.setItem(i, 0, QtWidgets.QTableWidgetItem(str(i)))
                self.prop_table.setItem(i, 1, QtWidgets.QTableWidgetItem(type(v).__name__))  # type: ignore
                self.prop_table.setItem(i, 2, QtWidgets.QTableWidgetItem(str(v)))  # type: ignore

        else:
            self.prop_table.insertRow(0)
            self.prop_table.setItem(0, 0, QtWidgets.QTableWidgetItem("value"))
            self.prop_table.setItem(0, 1, QtWidgets.QTableWidgetItem(type(obj).__name__))
            self.prop_table.setItem(0, 2, QtWidgets.QTableWidgetItem(str(obj)))

    def _on_prop_double_click(self, item: QtWidgets.QTableWidgetItem) -> None:
        row = item.row()

        key_item: QtWidgets.QTableWidgetItem | None = self.prop_table.item(row, 0)
        type_item: QtWidgets.QTableWidgetItem | None = self.prop_table.item(row, 1)
        val_item: QtWidgets.QTableWidgetItem | None = self.prop_table.item(row, 2)

        if not key_item or not type_item or not val_item:
            return

        cur_type = type_item.text()
        cur_val = val_item.text()
        dlg = EditValueDialog(self, cur_type, cur_val)

        if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            new_type, new_val = dlg.result_value
            type_item.setText(new_type)
            val_item.setText(str(new_val))

            parent_obj = self._current_obj_from_item(self.tree.selectedItems()[0])
            key_raw = key_item.text()
            key = int(key_raw) if isinstance(parent_obj, list) else key_raw

            if isinstance(parent_obj, dict):
                parent_obj[key] = new_val

            elif isinstance(parent_obj, list):
                parent_obj[key] = new_val  # type: ignore[index]

    def open_file(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open File", "", "JSON files (*.json *.gz);;All files (*)"
        )
        if not path:
            return

        self.manager.load(path)

        self.setWindowTitle(f"Json Inspector <{self.manager.path}>")
        self.setWindowIcon(self.application_icon)
        self._cache.clear()
        self._current_match = -1
        self.search_edit.clear()
        self.match_label.setText("0/0")
        self.prop_table.clearContents()
        self.prop_table.setRowCount(0)
        self.populate_tree()
        self.update_footer()

    def reload_popup(self) -> None:
        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setIcon(QtWidgets.QMessageBox.Icon.Information)
        msg_box.setWindowTitle("File Reloaded")
        msg_box.setText("The file on disk has been edited. The contents have been reloaded.")
        msg_box.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
        msg_box.exec()

    def decoding_failed_popup(self, error: json.JSONDecodeError) -> None:
        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setIcon(QtWidgets.QMessageBox.Icon.Critical)
        msg_box.setWindowTitle("Decoding Failed")
        msg_box.setText(f"Failed to decode JSON file: {error.msg}")
        msg_box.setDetailedText(f"Error at line {error.lineno}, column {error.colno}.")
        msg_box.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
        msg_box.exec()

    def reload(self) -> None:
        self.manager.load(auto_clear=False)
        self._current_path = self.manager.path
        self.setWindowTitle(f"Json Inspector <{self._current_path}>")
        self._cache.clear()
        self.populate_tree()
        self.update_footer()

    def clear(self) -> None:
        self._cache.clear()
        self._current_path = ""
        self.setWindowTitle("Json Inspector")
        self.tree.clear()
        self.prop_table.clearContents()
        self.prop_table.setRowCount(0)
        self.search_edit.clear()
        self.match_label.setText("0/0")
        self.update_footer()

    def _save_file(self) -> None:
        if not self._current_path:
            self._save_as_file()
            return
        self.manager.save(self._current_path)
        self.setWindowTitle(f"Json Inspector <{self.manager.path}>")

    def _save_as_file(self) -> None:
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save JSON", self.manager.path, "JSON files (*.json *.gz);;All files (*)"
        )
        if not path:
            return
        self.manager.save_as(path)
        self.setWindowTitle(f"Json Inspector <{self.manager.path}>")

    def _load_children_sync(self, item: QtWidgets.QTreeWidgetItem, path: Tuple[str, ...]) -> None:
        if item.data(0, QtCore.Qt.ItemDataRole.UserRole):
            return

        raw_items = Helper.prepare_items(self._get_obj_by_path(path))
        self._cache[path] = raw_items
        self._add_children(item, raw_items)
        item.setData(0, QtCore.Qt.ItemDataRole.UserRole, True)

    def item_for_path(self, path: Tuple[str | int, ...]) -> QtWidgets.QTreeWidgetItem | None:
        item: QtWidgets.QTreeWidgetItem | None = self.tree.topLevelItem(0)
        assert item is not None, "Root item should not be None"
        accumulated: List[str] = []
        for key in path:
            self.tree.expandItem(item)

            self._load_children_sync(item, tuple(accumulated))

            found = None
            for idx in range(item.childCount()):
                ch: QtWidgets.QTreeWidgetItem | None = item.child(idx)
                if ch is not None and ch.text(0) == str(key):
                    found: QtWidgets.QTreeWidgetItem | None = ch
                    break

            if not found:
                self._on_item_expanded(item)
                for idx in range(item.childCount()):
                    ch = item.child(idx)
                    if ch is not None and ch.text(0) == str(key):
                        found = ch
                        break

            if not found:
                return None

            item = found
            accumulated.append(key)  # type: ignore[assignment]

        return item
