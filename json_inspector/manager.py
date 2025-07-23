from typing import Any, Dict, List, Optional, Tuple, Union
from gui import Helper
import gc
from gui import Gui


class JsonManager:
    def __init__(self, path: str) -> None:
        self._path: str = path
        self.data: Dict[str | int | float, Any] | None = None
        self.object_loaded_cache: int = 0
        self.gui: Gui = Gui(self)
        self.load()
        self.gui.load()

    @property
    def path(self) -> str:
        return self._path

    def load(self, path: Optional[str] = None, auto_clear: bool = True) -> None:
        if auto_clear and self.data is not None:
            self.clear()
        if path:
            self._path = path
        self.data = Helper.load_json(self._path)
        gc.collect()

    def save(self, path: str) -> None:
        if self.data is None:
            raise ValueError("No data to save. Load or set data before saving.")
        Helper.save_json(self.data, path)
        gc.collect()

    def save_as(self, new_path: str) -> None:
        self.save(new_path)

    def clear(self) -> None:
        self.data.clear() if self.data else None
        self.data = None
        self.object_loaded_cache = 0
        gc.collect()

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
