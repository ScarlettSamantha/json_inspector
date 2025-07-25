import json
from typing import Any, Dict, List, Optional, Tuple, Type, Union
from gui import Helper
import gc
from gui import Gui

from monitor import FileEvent
from settings import Settings
from monitor import JsonFileMonitor


class JsonManager:
    def __init__(self, path: str | None = None) -> None:
        self._path: str | None = path
        self.data: Dict[str | int | float, Any] | None = None
        self.object_loaded_cache: int = 0
        self.gui: Gui = Gui(self)
        self.settings: Type[Settings] = Settings
        self.settings.setup()

        self.gui.load()
        if self._path:
            self.load_file()

        if self.data is not None:
            self.gui.populate_tree()

        self._monitor: JsonFileMonitor | None = None

    def load_file(self):
        self.load()

    @property
    def path(self) -> str | None:
        return self._path

    @path.setter
    def path(self, value: str) -> None:
        self._path = value

    def start_monitoring(self) -> None:
        if self._path is None:
            return

        if not hasattr(self, "_monitor") or self._monitor is None:
            self._monitor = JsonFileMonitor(self)

        self._monitor.register_callback(self.handle_file_change)
        self._monitor.start()

    def stop_monitoring(self) -> None:
        if hasattr(self, "_monitor") and self._monitor is not None:
            self._monitor.stop_monitoring()
            del self._monitor

    def handle_file_change(self, event: FileEvent) -> None:
        if event.value == FileEvent.MODIFIED.value:
            self.gui.reload_popup()
            self.gui.reload()
        elif event == FileEvent.DELETED:
            self.clear()
            self.gui.clear()

    def load(self, path: Optional[str] = None, auto_clear: bool = True, activate_monitor: bool = True) -> None:
        if auto_clear and self.data is not None:
            self.clear()

        if path is not None:
            self._path = path
        elif self._path is None:
            self.gui.open_file()

        assert self._path is not None, "Path must be set before loading data."

        try:
            self.data = Helper.load_json(self._path)
        except (OSError, json.JSONDecodeError) as e:
            if isinstance(e, json.JSONDecodeError):
                self.gui.decoding_failed_popup(e)
                self.clear()
                self.gui.clear()
                return
            else:
                raise OSError(f"Failed to read JSON file {self._path}: {e}")
        gc.collect()

        if activate_monitor and self.settings.monitoring_enabled():
            self.start_monitoring()

    def save(self, path: str) -> None:
        if self.data is None:
            raise ValueError("No data to save. Load or set data before saving.")
        Helper.save_json(self.data, path)
        gc.collect()

    def save_as(self, new_path: str) -> None:
        self.save(new_path)

    def clear(self) -> None:
        self.stop_monitoring()
        self.data.clear() if self.data else None
        self.data = None
        self._path = None
        self.object_loaded_cache = 0
        gc.collect()

    def is_monitoring(self) -> bool:
        return hasattr(self, "_monitor") and self._monitor is not None and self._monitor.is_observer_running

    def get_monitor(self) -> "JsonFileMonitor":
        if not hasattr(self, "_monitor") or self._monitor is None:
            raise RuntimeError("Manager does not have a monitor.")
        return self._monitor

    def get_total_count(self, cache: bool = True) -> int:
        if cache:
            if self.object_loaded_cache == 0:

                def count_keys_recursive(data: Any):
                    if isinstance(data, dict):
                        return sum(count_keys_recursive(v) for v in data.values()) + len(data)  # type: ignore
                    elif isinstance(data, list):
                        return sum(count_keys_recursive(item) for item in data)  # type: ignore
                    else:
                        return 0

                self.object_loaded_cache = count_keys_recursive(self.data)
            return self.object_loaded_cache
        else:
            return len(Helper.prepare_items(self.data)) if self.data else 0

    def get_data_from_path(self, path: Tuple[str, ...]) -> Any:
        if self.data is None:
            return None
        current: Dict[str | int | float, Any] = self.data
        for key in path:
            if key in current:
                current = current[key]
            elif isinstance(current, (list, tuple)) and isinstance(key, int) and 0 <= key < len(current):
                current = current[key]
            else:
                return None
        return current

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
