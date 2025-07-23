from typing import TYPE_CHECKING, Callable, List
import os
from enum import Enum, auto
from watchdog.observers import Observer
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers.api import BaseObserver

from pathlib import Path

if TYPE_CHECKING:
    from manager import JsonManager


class FileEvent(Enum):
    MODIFIED = auto()
    DELETED = auto()


class JsonFileMonitor:
    def __init__(self, manager: "JsonManager") -> None:
        self.manager: "JsonManager" = manager

        assert manager.path is not None, "Path must be set before initializing the monitor."

        self._path: str = manager.path

        self._callbacks: List[Callable[[FileEvent], None]] = []

        self._observer: BaseObserver = Observer()
        directory: str = str(Path(self._path).resolve().parent) or "."
        event_handler = JsonFileEventHandler(self)
        self._observer.schedule(event_handler, directory, recursive=False)
        self._observer.daemon = True
        self._observer.start()

    def register_callback(self, cb: Callable[[FileEvent], None]) -> None:
        if cb not in self._callbacks:
            self._callbacks.append(cb)

    def unregister_callback(self, cb: Callable[[FileEvent], None]) -> None:
        if cb in self._callbacks:
            self._callbacks.remove(cb)

    def dispatch(self, event: FileEvent) -> None:
        for cb in list(self._callbacks):
            try:
                cb(event)
            except Exception:
                pass

    def stop_monitoring(self) -> None:
        self._observer.stop()
        try:
            self._observer.join()
        except RuntimeError:
            pass


class JsonFileEventHandler(FileSystemEventHandler):
    def __init__(self, monitor: JsonFileMonitor) -> None:
        self._monitor: JsonFileMonitor = monitor

        if self._monitor.manager.path is None:
            raise ValueError("The manager's path cannot be None.")

        self._target: str = os.path.abspath(self._monitor.manager.path)

    def on_modified(self, event: FileSystemEvent) -> None:
        if os.path.abspath(event.src_path) == self._target:
            self._monitor.manager.load(auto_clear=False)
            self._monitor.dispatch(FileEvent.MODIFIED)

    def on_deleted(self, event: FileSystemEvent) -> None:
        if os.path.abspath(event.src_path) == self._target:
            self._monitor.dispatch(FileEvent.DELETED)
