import json
from pathlib import Path
import sys
import types
from typing import Any, List, Tuple
import pytest
from PyQt6 import QtWidgets, QtCore
from pytest import MonkeyPatch

from json_inspector.manager import JsonManager
from watchdog import FileEvent  # type: ignore


class DummyGui:
    def __init__(self, manager: JsonManager):
        self.actions: List[Any] = []

    def load(self):
        self.actions.append("load")

    def populate_tree(self):
        self.actions.append("populate_tree")

    def reload_popup(self):
        self.actions.append("reload_popup")

    def reload(self):
        self.actions.append("reload")

    def clear(self):
        self.actions.append("clear")

    def open_file(self):
        self.actions.append("open_file")

    def decoding_failed_popup(self, e: Exception):
        self.actions.append(("decoding_failed", str(e)))


class DummyMonitor:
    def __init__(self, manager: JsonManager):
        self.stopped = False

    def register_callback(self, cb: Any):
        self._cb = cb

    def stop_monitoring(self):
        self.stopped = True


@pytest.fixture(autouse=True)
def patch_json_manager(monkeypatch: MonkeyPatch, tmp_path: Path):
    mod = types.ModuleType("monitor")
    mod.JsonFileMonitor = DummyMonitor  # type: ignore

    class _FileEvent:
        MODIFIED = "modified"
        DELETED = "deleted"

    mod.FileEvent = _FileEvent  # type: ignore
    sys.modules["monitor"] = mod

    import importlib
    import json_inspector.manager as manager_mod

    importlib.reload(manager_mod)
    import json_inspector.gui as gui_mod

    importlib.reload(gui_mod)

    monkeypatch.setattr("json_inspector.manager.Gui", DummyGui)

    def fake_load(path: str):
        with open(path, "r") as f:
            return json.load(f)

    def fake_save(data: Any, path: str):
        with open(path, "w") as f:
            json.dump(data, f)

    monkeypatch.setattr("json_inspector.manager.Helper.load_json", fake_load)
    monkeypatch.setattr("json_inspector.manager.Helper.save_json", fake_save)


class TestJsonManager:
    def test_init_with_path_loads_and_populates(self, tmp_path: Path):
        data = {"foo": 1}
        file: Path = tmp_path / "t.json"
        file.write_text(json.dumps(data))
        jm = JsonManager(str(file))
        assert jm.data == data
        assert jm.gui.actions == ["load", "populate_tree"]

    def test_init_without_path_opens_file_only(self):
        jm = JsonManager(None)
        assert jm.data is None
        assert jm.gui.actions == ["load"]

    def test_save_and_save_as(self, tmp_path: Path):
        jm = JsonManager(None)
        jm.data = {"a": 2}
        dest: Path = tmp_path / "out.json"
        jm.save(str(dest))
        assert json.loads(dest.read_text()) == {"a": 2}
        dest2 = tmp_path / "out2.json"
        jm.save_as(str(dest2))
        assert json.loads(dest2.read_text()) == {"a": 2}

    def test_save_without_data_raises(self):
        jm = JsonManager(None)
        jm.data = None
        with pytest.raises(ValueError):
            jm.save("nope.json")

    def test_start_and_stop_monitoring(self):
        jm = JsonManager(None)
        jm.start_monitoring()
        assert hasattr(jm, "_monitor")
        jm.stop_monitoring()
        assert not hasattr(jm, "_monitor")

    def test_handle_file_change(self):
        jm = JsonManager(None)
        jm.handle_file_change(FileEvent.MODIFIED)  # type: ignore
        assert jm.gui.actions[-2:] == ["reload_popup", "reload"]  # type: ignore
        jm.data = {"x": 1}
        jm.handle_file_change(FileEvent.DELETED)  # type: ignore
        assert jm.data == {"x": 1}

    def test_get_total_count(self, monkeypatch: MonkeyPatch):
        jm = JsonManager(None)
        jm.data = {"a": 1, "b": {"c": 2, "d": [3, {"e": 4}]}}
        c1 = jm.get_total_count(cache=True)
        assert c1 == 5
        jm.data = {}
        assert jm.get_total_count(cache=True) == 5
        monkeypatch.setattr("json_inspector.manager.Helper.prepare_items", lambda data: [1, 2, 3])  # type: ignore
        jm.data = {"whatever": True}
        assert jm.get_total_count(cache=False) == 3

    def test_find_paths_in_data(self):
        jm = JsonManager(None)
        jm.data = {"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}], "count": 2}
        paths: List[Tuple[Tuple[str | int, ...], str]] = jm.find_paths_in_data("id")
        assert (("users", 0, "id"), "id") in paths
        assert (("users", 1, "id"), "id") in paths
        val_paths: List[Tuple[Tuple[str | int, ...], str]] = jm.find_paths_in_data("1")
        assert (("users", 0, "id"), "1") in val_paths


@pytest.fixture
def app() -> QtCore.QCoreApplication | QtWidgets.QApplication:
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


@pytest.fixture(autouse=True)
def patch_gui_deps(monkeypatch: MonkeyPatch, tmp_path: Path):
    monkeypatch.setattr("helper.Helper.assets_path", lambda: tmp_path)
    monkeypatch.setattr("helper.OSHelper.get_memory_usage_human", lambda: "0 MB")

    def mock_edit_value_dialog(*args: Any, **kwargs: Any) -> types.SimpleNamespace:
        return types.SimpleNamespace(exec=lambda: QtWidgets.QDialog.DialogCode.Accepted, result_value=("int", "123"))

    monkeypatch.setattr(
        "json_inspector.gui.EditValueDialog",
        mock_edit_value_dialog,
    )
    monkeypatch.setattr(
        "json_inspector.gui.AboutDialog",
        lambda *args, **kwargs: types.SimpleNamespace(exec=lambda: None),  # type: ignore
    )
    monkeypatch.setattr(
        "json_inspector.gui.SettingsDialog",
        lambda *args, **kwargs: types.SimpleNamespace(exec=lambda: None),  # type: ignore
    )
    monkeypatch.setattr(
        "json_inspector.gui.Search",
        lambda manager, pool: types.SimpleNamespace(  # type: ignore
            perform_search=lambda x: None,  # type: ignore
            clear=lambda: None,
            step=lambda d: None,  # type: ignore
        ),
    )


@pytest.fixture
def manager_instance() -> JsonManager:
    jm = JsonManager(None)
    jm.data = {"parent": {"child": [1, 2]}}
    return jm
