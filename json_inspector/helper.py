import gzip
import sys
import json
from typing import Any, List, Tuple, Union
import platform
import subprocess
from pathlib import Path
from typing import ClassVar


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

    @staticmethod
    def base_path() -> Path:
        return Path(sys.argv[0]).parent if hasattr(sys, "frozen") else Path(__file__).parent

    @staticmethod
    def assets_path() -> Path:
        return Helper.base_path() / "assets"


class OSHelper:
    APP_ID: ClassVar[str] = "JsonInspector"
    EXECUTABLE: ClassVar[Path] = (Path(sys.argv[0]) / ".." / "run.py").resolve()
    DESKTOP_DIR: ClassVar[Path] = Path.home() / ".local" / "share" / "applications"
    DESKTOP_FILE: ClassVar[Path] = DESKTOP_DIR / f"{APP_ID}.desktop"
    MIME_TYPE: ClassVar[str] = "application/json"

    @classmethod
    def register_association(cls) -> None:
        if platform.system() == "Windows":
            cls._register_windows()
        else:
            cls._register_linux()

    @classmethod
    def unregister_association(cls) -> None:
        if platform.system() == "Windows":
            cls._unregister_windows()
        else:
            cls._unregister_linux()

    @classmethod
    def _register_windows(cls) -> None:
        import winreg

        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\.json") as ext:  # type: ignore
            winreg.SetValue(ext, "", winreg.REG_SZ, f"{cls.APP_ID}File")  # type: ignore
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{cls.APP_ID}File") as fk:  # type: ignore
            winreg.SetValue(fk, "", winreg.REG_SZ, "JSON Document")  # type: ignore
            with winreg.CreateKey(fk, "DefaultIcon") as ik:  # type: ignore
                winreg.SetValue(ik, "", winreg.REG_SZ, f"{cls.EXECUTABLE},0")  # type: ignore , windows calls always have this issue on linux
            with winreg.CreateKey(fk, r"shell\open\command") as ck:  # type: ignore
                winreg.SetValue(ck, "", winreg.REG_SZ, f'"{cls.EXECUTABLE}" "%1"')  # type: ignore , windows calls always have this issue on linux

    @classmethod
    def _unregister_windows(cls) -> None:
        import winreg

        for key in (r".json", f"{cls.APP_ID}File"):
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{key}")  # type: ignore , windows calls always have this issue on linux
            except FileNotFoundError:
                pass

    @classmethod
    def _register_linux(cls) -> None:
        from vars import APPLICATION_NAME

        cls.DESKTOP_DIR.mkdir(parents=True, exist_ok=True)
        cls.DESKTOP_FILE.write_text(
            "\n".join(
                [
                    "[Desktop Entry]",
                    f"Name={APPLICATION_NAME}",
                    f"Exec=/usr/bin/python3 {cls.EXECUTABLE} %f",
                    "Type=Application",
                    f"MimeType={cls.MIME_TYPE};",
                    "NoDisplay=false",
                    f"Icon={Helper.assets_path() / 'application_icon_512.png'}",
                    "StartupWMClass=JsonInspector",
                ]
            )
        )
        subprocess.run(["xdg-mime", "default", cls.DESKTOP_FILE.name, cls.MIME_TYPE], check=False)

    @classmethod
    def _unregister_linux(cls) -> None:
        if cls.DESKTOP_FILE.exists():
            cls.DESKTOP_FILE.unlink()
        subprocess.run(["xdg-mime", "default", "", cls.MIME_TYPE], check=False)

    @classmethod
    def is_association_registered(cls) -> bool:
        if platform.system() == "Windows":
            import winreg

            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\\Classes\\.json") as ext:  # type: ignore
                    val, _ = winreg.QueryValueEx(ext, "")  # type: ignore
                    return val == f"{cls.APP_ID}File"  # type: ignore
            except OSError:
                return False
        else:
            result: subprocess.CompletedProcess[str] = subprocess.run(
                ["xdg-mime", "query", "default", cls.MIME_TYPE], capture_output=True, text=True
            )
            if result.returncode == 0:
                return result.stdout.strip() == cls.DESKTOP_FILE.name
            return False
