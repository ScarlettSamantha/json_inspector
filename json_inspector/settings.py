from typing import Any, Self, Type
from PyQt6.QtCore import QSettings
from vars import APPLICATION_NAME, APPLICATION_ORGANIZATION


class Settings:
    MONITORING_KEY = "monitoring_enabled"

    _settings: QSettings | None = None

    @classmethod
    def get_instance(cls) -> Type[Self]:
        if cls._settings is None:
            cls._setup()

        assert cls._settings is not None, "Settings not initialized"

        return cls

    @classmethod
    def setup(cls) -> None:
        cls._setup()

    @classmethod
    def _setup(cls):
        cls._settings = QSettings(APPLICATION_ORGANIZATION, APPLICATION_NAME)

    @classmethod
    def _get_settings(cls) -> QSettings:
        if cls._settings is None:
            cls._setup()

        assert cls._settings is not None, "Settings not initialized"

        return cls._settings

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        return cls._get_settings().value(key, default)

    @classmethod
    def set(cls, key: str, value: Any):
        cls._get_settings().setValue(key, value)
        cls.sync()

    @classmethod
    def remove(cls, key: str):
        cls._get_settings().remove(key)

    @classmethod
    def clear(cls):
        cls._get_settings().clear()

    @classmethod
    def sync(cls):
        cls._get_settings().sync()

    @classmethod
    def monitoring_enabled(cls) -> bool:
        return bool(cls.get(cls.MONITORING_KEY, True).upper() == "TRUE")

    @classmethod
    def set_monitoring_enabled(cls, enabled: bool):
        cls.set(cls.MONITORING_KEY, enabled)
