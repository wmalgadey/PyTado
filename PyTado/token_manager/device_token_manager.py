import json
import logging
import os
from fcntl import LOCK_EX, LOCK_SH, LOCK_UN, flock  # For file locking on Unix systems
from json import dump as json_dump
from json import load as json_load
from pathlib import Path

from platformdirs import user_data_dir

from PyTado.exceptions import TadoException  # For secure, platform-specific directories

from .token_manager_interface import TokenManagerInterface

_LOGGER = logging.getLogger(__name__)


class DeviceTokenManager(TokenManagerInterface):
    """Handles saving and loading of the data with file locking for multi-process safety."""

    def __init__(self):
        """Initialize the TokenManager."""
        # Use a secure, platform-specific directory for storing the sync file
        app_data_dir = user_data_dir(appname="PyTado", appauthor="PyTado")
        self._sync_file_path = os.path.join(app_data_dir, "device_token_manager.json")
        self._refresh_token: str | None = None

    def save_token(self, refresh_token: str) -> None:
        """Save the refresh token to a file with file locking."""
        self._refresh_token = refresh_token

        if not refresh_token:
            return

        # Overwrite the file with the new refresh token
        self._save_sync_file({"refresh_token": refresh_token})

    def load_token(self) -> str | None:
        """Load the refresh token from a file with file locking."""
        data = self._load_sync_file()
        if data:
            self._refresh_token = data.get("refresh_token")
        return self._refresh_token

    def has_pending_device_data(self) -> bool:
        """Check if there is pending device data."""
        device_data = self._load_sync_file()

        if device_data and "pending_device" in device_data:
            return True

        return False

    def save_pending_device_data(self, device_data) -> None:
        """Save device data to the sync file."""
        if not device_data:
            return

        # Save device data to the file
        self._save_sync_file({"pending_device": device_data})

    def load_pending_device_data(self) -> dict:
        """Load the device data from a file with file locking."""
        data = self._load_sync_file()

        if not data or "pending_device" not in data:
            raise TadoException("No pending device data found")

        return data.get("pending_device", {})

    def _save_sync_file(self, data: dict) -> None:
        """Save data to the sync file with file locking."""
        try:
            token_dir = os.path.dirname(self._sync_file_path)
            if token_dir and not os.path.exists(token_dir):
                Path(token_dir).mkdir(parents=True, exist_ok=True)

            with open(self._sync_file_path, "w", encoding="utf-8") as f:
                # Acquire an exclusive lock
                flock(f, LOCK_EX)
                json_dump(data, f)
                # Release the lock
                flock(f, LOCK_UN)

            _LOGGER.debug("Data saved to %s: %s", self._sync_file_path, data)
        except Exception as e:
            _LOGGER.error("Failed to save data to sync file: %s", e)
            raise

    def _load_sync_file(self) -> dict:
        """Load data from the sync file with file locking."""
        if not self._sync_file_path or not os.path.exists(self._sync_file_path):
            return {}

        try:
            with open(self._sync_file_path, encoding="utf-8") as f:
                # Acquire a shared lock
                flock(f, LOCK_SH)
                data = json_load(f)
                # Release the lock
                flock(f, LOCK_UN)

                _LOGGER.debug("Data loaded from %s: %s", self._sync_file_path, data)
                return data
        except (OSError, json.JSONDecodeError) as e:
            _LOGGER.error("Failed to load data from sync file: %s", e)
            return {}
