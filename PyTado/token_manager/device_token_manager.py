import enum
import json
import logging
import os
from contextlib import contextmanager
from datetime import datetime
from fcntl import LOCK_EX, LOCK_SH, LOCK_UN, flock  # For file locking on Unix systems
from json import dump as json_dump
from json import load as json_load
from pathlib import Path
from typing import Generator

from platformdirs import user_data_dir

from PyTado.exceptions import TadoException
from PyTado.token_manager import CanManageDeviceActivation, FileTokenManager

_LOGGER = logging.getLogger(__name__)


class FileContent(enum.StrEnum):
    PENDING_DEVICE = "pending_device"


class FileLock:
    """Context manager for file locking."""

    def __init__(self, file, lock_type, msg):
        self.file = file
        self.lock_type = lock_type
        self.msg = msg

    def __enter__(self):
        """Acquire the lock."""
        flock(self.file, self.lock_type)
        return self.file

    def __exit__(self, exc_type, exc_value, traceback):
        """Release the lock."""
        flock(self.file, LOCK_UN)


class DeviceTokenManager(FileTokenManager, CanManageDeviceActivation):
    """Handles saving and loading of the data with file locking for multi-process safety."""

    def __init__(self):
        """Initialize the TokenManager."""

        # Use a secure, platform-specific directory for storing the sync file
        app_data_dir = user_data_dir(appname="PyTado", appauthor="PyTado")

        super().__init__(token_file_path=os.path.join(app_data_dir, "device_token.json"))

        _LOGGER.debug("Sync file path: %s", self._token_file_path)

    @contextmanager
    def lock_device_activation(self, msg) -> Generator[None, None, None]:
        if not self._token_file_path:
            raise ValueError("Token file path is not set")

        with open(self._token_file_path, "r+", encoding="utf-8") as f:
            with FileLock(f, LOCK_EX, msg):
                yield

    def is_locked(self) -> bool:
        if not self._token_file_path:
            raise ValueError("Token file path is not set")

        try:
            with (
                open(self._token_file_path, encoding="utf-8") as f,
                FileLock(f, LOCK_EX | LOCK_SH, "Check if locked"),
            ):
                return False
        except BlockingIOError:
            return True

    def has_pending_device_data(self) -> bool:
        """Check if there is pending device data."""
        device_data = self._load_data()

        if (
            device_data
            and FileContent.PENDING_DEVICE in device_data
            and datetime.now().timestamp() < datetime.fromisoformat(
                device_data[FileContent.PENDING_DEVICE]["expires_at"]
            ).timestamp()
        ):
            return True

        return False

    def set_pending_device_data(self, device_data) -> None:
        """Save device data to the sync file."""
        if not device_data:
            return self._save_data({})

        self._save_data({FileContent.PENDING_DEVICE: device_data})

    def get_pending_device_data(self) -> dict:
        """Get the device data from a file with file locking."""
        data = self._load_data()

        if not data or FileContent.PENDING_DEVICE not in data:
            raise TadoException("No pending device data found")

        return data.get(FileContent.PENDING_DEVICE, {})

    def _save_data(self, data: dict) -> None:
        """Save data to the sync file with file locking."""
        if not self._token_file_path:
            raise ValueError("Token file path is not set")

        try:
            token_dir = os.path.dirname(self._token_file_path)
            if token_dir and not os.path.exists(token_dir):
                Path(token_dir).mkdir(parents=True, exist_ok=True)

            with (
                open(self._token_file_path, "w", encoding="utf-8") as f,
                FileLock(f, LOCK_EX, "Save data"),
            ):
                json_dump(data, f)

            _LOGGER.debug("Data saved to %s: %s", self._token_file_path, data)
        except Exception as e:
            _LOGGER.error("Failed to save data to sync file: %s", e)
            raise

    def _load_data(self) -> dict:
        """Load data from the sync file with file locking."""
        if not self._token_file_path:
            raise ValueError("Token file path is not set")

        if not os.path.exists(self._token_file_path):
            return {}

        try:
            with (
                open(self._token_file_path, encoding="utf-8") as f,
                FileLock(f, LOCK_SH, "Load data"),
            ):
                data = json_load(f)

            _LOGGER.debug("Data loaded from %s: %s", self._token_file_path, data)
            return data
        except (OSError, json.JSONDecodeError) as e:
            _LOGGER.error("Failed to load data from sync file: %s", e)
            return {}
