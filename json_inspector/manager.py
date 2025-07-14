from typing import Any, Dict, Optional
from gui import Helper


class JsonManager:
    def __init__(self, path: str) -> None:
        self._path: str = path
        self.data: Dict[str | int | float, Any] | None = None
        self.load()

    @property
    def path(self) -> str:
        return self._path

    def load(self, path: Optional[str] = None) -> None:
        if path:
            self._path = path
        self.data = Helper.load_json(self._path)

    def save(self, path: str) -> None:
        if self.data is None:
            raise ValueError("No data to save. Load or set data before saving.")
        Helper.save_json(self.data, path)

    def save_as(self, new_path: str) -> None:
        self.save(new_path)
