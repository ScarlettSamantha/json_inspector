import json
import gzip
from typing import Any, Dict, List, Tuple, Union
from edit_value_dialog import EditValueDialog
from load_children_worker import LoadChildrenWorker
from helper import Helper
from search import Search
from PyQt6 import QtWidgets, QtGui, QtCore

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


class JsonInspector(QtWidgets.QMainWindow):
    def __init__(self, path: str) -> None:
        super().__init__()
        self._current_path = path
        self.data: Any = Helper.load_json(path)
        self._cache: Dict[Tuple[Union[str, int], ...], List[Any]] = {}
        self._threadpool: QtCore.QThreadPool | None = QtCore.QThreadPool.globalInstance()

        self._match_paths: List[Tuple[Union[str, int], ...]] = []
        self._current_match: int = -1

        self.setWindowTitle(f"Json Inspector <{path}>")
        self.resize(1400, 800)
        self._build_ui()

        self.tree.itemExpanded.connect(self._on_item_expanded)  # type: ignore
        self._populate_tree()

        assert self._threadpool is not None, "Thread pool should not be None"

        self._search_controller = Search(self, self._threadpool)
        self.search_btn.clicked.connect(lambda: self._search_controller.perform_search(self.search_edit.text()))  # type: ignore
        self.clear_btn.clicked.connect(self._search_controller.clear)  # type: ignore
        self.prev_btn.clicked.connect(lambda: self._search_controller.step(-1))  # type: ignore
        self.next_btn.clicked.connect(lambda: self._search_controller.step(+1))  # type: ignore

    def _build_ui(self) -> None:
        menu: QtWidgets.QMenu | None = self.menuBar().addMenu("File")  # type: ignore
        open_act: QtGui.QAction | None = menu.addAction("Open…")  # type: ignore
        open_act.triggered.connect(self._open_file)  # type: ignore
        save_act: QtGui.QAction | None = menu.addAction("Save")  # type: ignore
        save_act.triggered.connect(self._save_file)  # type: ignore
        save_as_act: QtGui.QAction | None = menu.addAction("Save As…")  # type: ignore
        save_as_act.triggered.connect(self._save_as_file)  # type: ignore
        menu.addSeparator()  # type: ignore
        quit_act: QtGui.QAction | None = menu.addAction("Quit")  # type: ignore
        quit_act.triggered.connect(self.close)  # type: ignore

        tool_bar = QtWidgets.QToolBar()
        self.addToolBar(tool_bar)

        self.search_edit = QtWidgets.QLineEdit()
        self.search_edit.setPlaceholderText("Find key or value…")
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
        self.tree.itemSelectionChanged.connect(self._on_select)  # type: ignore
        splitter.addWidget(self.tree)

        self.prop_table = QtWidgets.QTableWidget()
        self.prop_table.setColumnCount(3)
        self.prop_table.setHorizontalHeaderLabels(["Key", "Type", "Value"])  # type: ignore
        self.prop_table.horizontalHeader().setStretchLastSection(True)  # type: ignore
        self.prop_table.itemDoubleClicked.connect(self._on_prop_double_click)  # type: ignore
        splitter.addWidget(self.prop_table)
        splitter.setSizes([500, 1000])  # type: ignore

    def _populate_tree(self) -> None:
        self.tree.clear()
        root = QtWidgets.QTreeWidgetItem(["root", type(self.data).__name__, ""])
        self.tree.addTopLevelItem(root)

        if isinstance(self.data, (dict, list, tuple, set)):
            placeholder = QtWidgets.QTreeWidgetItem(["Loading...", "", ""])
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

            worker = LoadChildrenWorker(item, self._current_obj_from_item(item), path_tuple)
            worker.signals.loaded.connect(self._on_children_loaded, QtCore.Qt.ConnectionType.QueuedConnection)  # type: ignore
            self._threadpool.start(worker)  # type: ignore

    @QtCore.pyqtSlot(QtWidgets.QTreeWidgetItem, list, tuple)  # type: ignore
    def _on_children_loaded(
        self,
        parent_item: QtWidgets.QTreeWidgetItem,
        items: List[Tuple[Union[str, int], str, str, bool]],
        path_tuple: Tuple[Union[str, int], ...],
    ) -> None:
        self._cache[path_tuple] = items

        self._add_children(parent_item, items)
        parent_item.setData(0, QtCore.Qt.ItemDataRole.UserRole, True)

        for key, typ, val, is_cont in items:  # type: ignore
            if is_cont:
                child_path = path_tuple + (key,)
                child_obj = self._get_obj_by_path(child_path)
                w = LoadChildrenWorker(parent_item.child(key if isinstance(key, int) else 0), child_obj, child_path)  # type: ignore
                w.signals.loaded.connect(self._on_cache_only, QtCore.Qt.ConnectionType.QueuedConnection)  # type: ignore
                self._threadpool.start(w)  # type: ignore

    @QtCore.pyqtSlot(QtWidgets.QTreeWidgetItem, list, tuple)  # type: ignore[no-untyped-def]
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

            parent_item.addChild(child)

    def _get_obj_by_path(self, path: Tuple[Union[str, int], ...]) -> Any:
        obj = self.data
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

        if cur_type in {"dict", "list", "tuple", "set"}:
            return

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

    def _open_file(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open File", "", filter="JSON files (*.json *.gz);;All files (*)"
        )
        if not path:
            return
        self._current_path = path
        self.data = Helper.load_json(path)
        self.setWindowTitle(f"Json Inspector <{path}>")
        self._cache.clear()
        self._matches.clear()  # type: ignore
        self._current_match = -1
        self.search_edit.clear()
        self.match_label.setText("0/0")
        self.prop_table.clearContents()
        self.prop_table.setRowCount(0)
        self._populate_tree()

    def _save_file(self) -> None:
        self._write_json(self._current_path)

    def _save_as_file(self) -> None:
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save JSON", self._current_path, filter="JSON files (*.json *.gz);;All files (*)"
        )
        if not path:
            return
        self._current_path = path
        self._write_json(path)

    def _write_json(self, path: str) -> None:
        if path.endswith(".gz"):
            with gzip.open(path, "wt", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4)
        else:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4)

    def find_paths_in_data(
        self, term: str, obj: Any = None, path: Tuple[str, ...] = ()
    ) -> List[Tuple[Tuple[Union[str, int], ...], str]]:
        if obj is None:
            obj = self.data
        results: List[Tuple[Tuple[Union[str, int], ...], str]] = []

        if isinstance(obj, dict):
            for k, v in obj.items():  # type: ignore
                key_str = str(k).lower()  # type: ignore
                is_cont = isinstance(v, (dict, list, tuple, set))
                val_str = (repr(v) if not isinstance(v, str) else v).lower()  # type: ignore
                p = path + (k,)  # type: ignore

                if term == key_str or (not is_cont and term == val_str):
                    results.append((p, val_str if term == val_str else key_str))  # type: ignore

                if is_cont:
                    results += self.find_paths_in_data(term, v, p)  # type: ignore

        elif isinstance(obj, (list, tuple, set)):
            for i, v in enumerate(obj):  # type: ignore
                key_str: str = str(i).lower()
                is_cont: bool = isinstance(v, (dict, list, tuple, set))
                val_str: str = repr(v).lower()  # type: ignore
                p = path + (i,)

                if term == key_str or (not is_cont and term == val_str):
                    results.append((p, val_str if term == val_str else key_str))

                if isinstance(v, (dict, list, tuple, set)):
                    results += self.find_paths_in_data(term, v, p)  # type: ignore

        return results

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
