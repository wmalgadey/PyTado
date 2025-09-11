import json
import logging
import os
from json import dump as json_dump
from json import load as json_load
from pathlib import Path

from .token_manager_interface import TokenManagerInterface

_LOGGER = logging.getLogger(__name__)


class FileTokenManager(TokenManagerInterface):
    """Handles saving and loading of the refresh token."""

    def __init__(self, token_file_path: str | None = None, saved_refresh_token: str | None = None):
        """
        Initialize the TokenManager.

        Args:
            token_file_path (str | None): Path to the file where the token is stored.
            saved_refresh_token (str | None): A refresh token which should be used, no mather what.
        """
        self._token_file_path = token_file_path
        self._refresh_token: str | None = None

        if saved_refresh_token:
            self.save_token(saved_refresh_token)

    def save_token(self, refresh_token: str) -> None:
        """Save the refresh token to a file."""

        self._refresh_token = refresh_token

        if not self._token_file_path or not refresh_token:
            return

        try:
            token_dir = os.path.dirname(self._token_file_path)
            if token_dir and not os.path.exists(token_dir):
                Path(token_dir).mkdir(parents=True, exist_ok=True)

            with open(self._token_file_path, "w", encoding="utf-8") as f:
                json_dump({"refresh_token": refresh_token}, f)

            _LOGGER.debug("Refresh token saved to %s", self._token_file_path)
        except Exception as e:
            _LOGGER.error("Failed to save refresh token: %s", e)
            raise

    def load_token(self) -> str | None:
        """Load the refresh token from a file."""
        if not self._token_file_path or not os.path.exists(self._token_file_path):
            return self._refresh_token

        try:
            with open(self._token_file_path, encoding="utf-8") as f:
                data = json_load(f)
                self._refresh_token = data.get("refresh_token")

                _LOGGER.debug("Refresh token loaded from %s", self._token_file_path)
                return self._refresh_token
        except (OSError, json.JSONDecodeError) as e:
            _LOGGER.error("Failed to load refresh token: %s", e)
            raise
