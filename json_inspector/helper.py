import gzip
import json
from typing import Any, List, Tuple, Union


class Helper:
    @staticmethod
    def load_json(path: str) -> Any:
        if path.endswith(".gz"):
            with gzip.open(path, "rt", encoding="utf-8") as f:
                return json.load(f)
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def save_json(data: Any, path: str, indents: int = 4) -> None:
        if path.endswith(".gz"):
            with gzip.open(path, "wt", encoding="utf-8") as f:
                json.dump(data, f, indent=indents)
        else:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=indents)

    @staticmethod
    def prepare_items(obj: Any) -> List[Tuple[Union[str, int], str, str, bool]]:
        items: List[Tuple[Union[str, int], str, str, bool]] = []
        if isinstance(obj, dict):
            for k, v in obj.items():  # type: ignore
                displayed = repr(v) if not isinstance(v, str) else v  # type: ignore
                items.append((k, type(v).__name__, displayed, isinstance(v, (dict, list, tuple, set))))  # type: ignore
        elif isinstance(obj, (list, tuple, set)):
            for i, v in enumerate(obj):  # type: ignore
                items.append((i, type(v).__name__, repr(v), isinstance(v, (dict, list, tuple, set))))  # type: ignore
        return items
