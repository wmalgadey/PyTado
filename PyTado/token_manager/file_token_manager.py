import enum
import json
import logging
import os
from json import dump as json_dump
from json import load as json_load
from pathlib import Path

from PyTado.exceptions import TadoException
from PyTado.token_manager.token_manager_interface import TokenManagerInterface

_LOGGER = logging.getLogger(__name__)


class FileContent(enum.StrEnum):
    OAUTH_DATA = "oauth_data"
    REFRESH_TOKEN = "refresh_token"  # nosec, deprecated


class FileTokenManager(TokenManagerInterface):
    """Handles saving and loading of the refresh token."""

    def __init__(self, token_file_path: str | None = None, saved_refresh_token: str | None = None):
        """
        Initialize the TokenManager.

        Args:
            token_file_path (str | None, optional): Path to the file where the token is stored.
            saved_refresh_token (str | None, optional): A refresh token which should be used,
                no mather what.
        """
        super().__init__()

        self._token_file_path = token_file_path

        if saved_refresh_token:
            self._set_oauth_data({"refresh_token": saved_refresh_token})

    def set_oauth_data(self, oauth_data: dict) -> None:
        """Try to save the oauth data to a file if a file is defined."""
        self._save_oauth_data(oauth_data)
        super().set_oauth_data(oauth_data)

    def _save_oauth_data(self, oauth_data: dict) -> None:
        if not self._token_file_path or not oauth_data:
            return

        try:
            token_dir = os.path.dirname(self._token_file_path)
            if token_dir and not os.path.exists(token_dir):
                Path(token_dir).mkdir(parents=True, exist_ok=True)

            with open(self._token_file_path, "w", encoding="utf-8") as f:
                json_dump({FileContent.OAUTH_DATA: oauth_data}, f)

            _LOGGER.debug("OAuth data saved to %s", self._token_file_path)
        except Exception as e:
            _LOGGER.error("Failed to save OAuth data: %s", e)
            raise TadoException(f"Failed to save OAuth data: {e}") from e

    def get_token(self) -> str | None:
        """Try to load the oauth data from a file if a file is defined."""
        self._load_oauth_data()
        return super().get_token()

    def _load_oauth_data(self) -> None:
        """Load the refresh token from a file."""
        if self._token_file_path and os.path.exists(self._token_file_path):
            try:
                with open(self._token_file_path, encoding="utf-8") as f:
                    data = json_load(f)

                    if FileContent.REFRESH_TOKEN in data:
                        self._set_oauth_data(
                            {"refresh_token": data[FileContent.REFRESH_TOKEN]})
                    else:
                        self._set_oauth_data(data.get(FileContent.OAUTH_DATA, {}))

                    _LOGGER.debug("Refresh token loaded from '%s'", self._token_file_path)
            except (OSError, json.JSONDecodeError) as e:
                _LOGGER.error("Failed to load OAuth data: %s", e)
                raise TadoException(f"Failed to load OAuth data: {e}") from e
