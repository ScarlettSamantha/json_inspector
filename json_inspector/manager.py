from typing import Any, Dict, Optional
from gui import Helper
import gc


class JsonManager:
    def __init__(self, path: str) -> None:
        self._path: str = path
        self.data: Dict[str | int | float, Any] | None = None
        self.object_loaded_cache: int = 0
        self.load()

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
