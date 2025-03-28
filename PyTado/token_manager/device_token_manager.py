import json
import logging
import os
from datetime import datetime
from fcntl import LOCK_EX, LOCK_SH, LOCK_UN, flock  # For file locking on Unix systems
from json import dump as json_dump
from json import load as json_load
from multiprocessing import current_process
from pathlib import Path
from typing import ContextManager

from platformdirs import user_data_dir

from PyTado.exceptions import TadoException
from PyTado.token_manager.token_manager_interface import (
    TokenManagerInterface,  # For secure, platform-specific directories
)

_LOGGER = logging.getLogger(__name__)

OAUTH_DATA_KEY = "oauth_data"
PENDING_DEVICE_KEY = "pending_device"


class FileLock:
    """Context manager for file locking."""

    def __init__(self, file, lock_type, msg):
        self.file = file
        self.lock_type = lock_type
        self.msg = msg

    def __enter__(self):
        """Acquire the lock."""
        print(f"[{current_process().pid}] {self.msg}: Try to lock file")
        flock(self.file, self.lock_type)
        print(f"[{current_process().pid}] {self.msg}: Locked file")
        return self.file

    def __exit__(self, exc_type, exc_value, traceback):
        """Release the lock."""
        flock(self.file, LOCK_UN)
        print(f"[{current_process().pid}] {self.msg}: Unlocked file")


class DeviceTokenManager(TokenManagerInterface):
    """Handles saving and loading of the data with file locking for multi-process safety."""

    def __init__(self):
        """Initialize the TokenManager."""
        super().__init__()

        # Use a secure, platform-specific directory for storing the sync file
        app_data_dir = user_data_dir(appname="PyTado", appauthor="PyTado")
        self._sync_file_path = os.path.join(app_data_dir, "device_token_manager.json")

        _LOGGER.debug("Sync file path: %s", self._sync_file_path)

    def lock_device_activation(self, msg) -> ContextManager:
        return FileLock(open(self._sync_file_path, encoding="utf-8"), LOCK_EX, msg)

    def is_locked(self) -> bool:
        try:
            with (
                open(self._sync_file_path, encoding="utf-8") as f,
                FileLock(f, LOCK_EX | LOCK_SH, "Check if locked"),
            ):
                return False
        except BlockingIOError:
            return True

    def save_oauth_data(self, oauth_data: dict) -> None:
        """Save the refresh token to a file with file locking."""
        super().save_oauth_data(oauth_data)

        self._save_sync_file({OAUTH_DATA_KEY: oauth_data})

    def load_token(self) -> str | None:
        """Load the refresh token from a file with file locking."""
        data = self._load_sync_file()

        if data:
            self._set_oauth_data(data.get(OAUTH_DATA_KEY, {}))

        return super().load_token()

    def has_pending_device_data(self) -> bool:
        """Check if there is pending device data."""
        device_data = self._load_sync_file()

        if (
            device_data
            and PENDING_DEVICE_KEY in device_data
            and datetime.now().timestamp()
            < datetime.fromisoformat(device_data[PENDING_DEVICE_KEY]["expires_at"]).timestamp()
        ):
            return True

        return False

    def save_pending_device_data(self, device_data) -> None:
        """Save device data to the sync file."""
        if not device_data:
            return self._save_sync_file({})

        self._save_sync_file({PENDING_DEVICE_KEY: device_data})

    def load_pending_device_data(self) -> dict:
        """Load the device data from a file with file locking."""
        data = self._load_sync_file()

        if not data or PENDING_DEVICE_KEY not in data:
            raise TadoException("No pending device data found")

        return data.get(PENDING_DEVICE_KEY, {})

    def _save_sync_file(self, data: dict) -> None:
        """Save data to the sync file with file locking."""
        try:
            token_dir = os.path.dirname(self._sync_file_path)
            if token_dir and not os.path.exists(token_dir):
                Path(token_dir).mkdir(parents=True, exist_ok=True)

            with (
                open(self._sync_file_path, "w", encoding="utf-8") as f,
                FileLock(f, LOCK_EX, "Save data"),
            ):
                json_dump(data, f)

            _LOGGER.debug("Data saved to %s: %s", self._sync_file_path, data)
        except Exception as e:
            _LOGGER.error("Failed to save data to sync file: %s", e)
            raise

    def _load_sync_file(self) -> dict:
        """Load data from the sync file with file locking."""
        if not self._sync_file_path or not os.path.exists(self._sync_file_path):
            return {}

        try:
            with (
                open(self._sync_file_path, encoding="utf-8") as f,
                FileLock(f, LOCK_SH, "Load data"),
            ):
                data = json_load(f)

            _LOGGER.debug("Data loaded from %s: %s", self._sync_file_path, data)
            return data
        except (OSError, json.JSONDecodeError) as e:
            _LOGGER.error("Failed to load data from sync file: %s", e)
            return {}
