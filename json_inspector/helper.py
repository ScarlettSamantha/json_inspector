import gzip
import os
import sys
import json
import time
from typing import Any, List, Tuple, Union
import platform
import subprocess
from pathlib import Path
from typing import ClassVar

import psutil


class Helper:
    @staticmethod
    def load_json(path: str) -> Any:
        for attempt in range(3):
            try:
                if path.endswith(".gz"):
                    with gzip.open(path, "rt", encoding="utf-8") as f:
                        return json.load(f)
                else:
                    with open(path, "r", encoding="utf-8") as f:
                        return json.load(f)
            except (OSError, json.JSONDecodeError) as e:
                time.sleep(1)
                if attempt < 2:
                    print(f"Attempt {attempt + 1} failed: {e}. Retrying...")
                    continue
                else:
                    if isinstance(e, json.JSONDecodeError):
                        raise e
                    else:
                        raise OSError(f"Failed to read JSON file {path} after 3 attempts: {e}")

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
    EXECUTABLE: ClassVar[Path] = (Helper.base_path() / "__main__.py").resolve()
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
        import ctypes

        exe_path = str(cls.EXECUTABLE)
        progid = f"{cls.APP_ID}File"

        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\.json") as ext:
            winreg.SetValueEx(ext, "", 0, winreg.REG_SZ, progid)

        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{progid}") as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "JSON Document")

            with winreg.CreateKey(key, "DefaultIcon") as icon:
                winreg.SetValueEx(icon, "", 0, winreg.REG_SZ, f"{exe_path},0")

            with winreg.CreateKey(key, r"shell\open\command") as cmd:
                winreg.SetValueEx(cmd, "", 0, winreg.REG_SZ, f'"{exe_path}" "%1"')

        cap_key = (
            rf"Software\Classes\Applications\{Path(exe_path).name}"
            r"\Capabilities"
        )

        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, cap_key) as cap:
            winreg.SetValueEx(cap, "ApplicationName", 0, winreg.REG_SZ, "Json Inspector")

        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, cap_key + r"\FileAssociations") as fa:
            winreg.SetValueEx(fa, ".json", 0, winreg.REG_SZ, cls.MIME_TYPE)

        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, cap_key + r"\DefaultIcon") as di:
            winreg.SetValueEx(di, "", 0, winreg.REG_SZ, f"{exe_path},0")

        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\RegisteredApplications") as reg:
            winreg.SetValueEx(reg, cls.APP_ID, 0, winreg.REG_SZ, cap_key)

        ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, None, None)

    @classmethod
    def _unregister_windows(cls) -> None:
        import winreg
        import ctypes

        for key in (r".json", f"{cls.APP_ID}File"):
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{key}")
            except FileNotFoundError:
                pass

        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, "Software\\RegisteredApplications", 0, winreg.KEY_SET_VALUE
            ) as reg:
                winreg.DeleteValue(reg, cls.APP_ID)
        except FileNotFoundError:
            pass

        exec_name = Path(str(cls.EXECUTABLE)).name
        cap_root = f"Software\\Classes\\Applications\\{exec_name}\\Capabilities"

        def _del_tree(root, subkey):
            with winreg.OpenKey(root, subkey, 0, winreg.KEY_ALL_ACCESS) as k:  # type: ignore
                i = 0
                while True:
                    try:
                        child = winreg.EnumKey(k, 0)  # type: ignore
                        _del_tree(root, subkey + "\\" + child)  # type: ignore
                    except OSError:
                        break
                winreg.DeleteKey(root, subkey)

        try:
            _del_tree(winreg.HKEY_CURRENT_USER, cap_root)  # type: ignore
        except FileNotFoundError:
            pass

        ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, None, None)

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

    @classmethod
    def get_memory_usage_bytes(cls) -> int:
        proc = psutil.Process(os.getpid())
        return proc.memory_info().rss

    @classmethod
    def get_memory_usage_human(cls) -> str:
        bytes_used = cls.get_memory_usage_bytes()
        for unit in ("bytes", "KB", "MB", "GB", "TB"):
            if bytes_used < 1024 or unit == "TB":
                return f"{bytes_used:.2f} {unit}"
            bytes_used /= 1024.0
        return f"{bytes_used:.2f} TB"
