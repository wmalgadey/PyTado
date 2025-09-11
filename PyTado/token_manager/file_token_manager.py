import json
import logging
import os
from json import dump as json_dump
from json import load as json_load
from pathlib import Path

from PyTado.exceptions import TadoException
from PyTado.token_manager.token_manager_interface import TokenManagerInterface

_LOGGER = logging.getLogger(__name__)

OAUTH_DATA_KEY = "oauth_data"


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

    def save_oauth_data(self, oauth_data: dict) -> None:
        """Save the refresh token to a file."""
        super().save_oauth_data(oauth_data)

        if not self._token_file_path or not oauth_data:
            return

        try:
            token_dir = os.path.dirname(self._token_file_path)
            if token_dir and not os.path.exists(token_dir):
                Path(token_dir).mkdir(parents=True, exist_ok=True)

            with open(self._token_file_path, "w", encoding="utf-8") as f:
                json_dump({OAUTH_DATA_KEY: oauth_data}, f)

            _LOGGER.debug("OAuth data saved to %s", self._token_file_path)
        except Exception as e:
            _LOGGER.error("Failed to save OAuth data: %s", e)
            raise TadoException(f"Failed to save OAuth data: {e}") from e

    def load_token(self) -> str | None:
        """Load the refresh token from a file."""
        if self._token_file_path and os.path.exists(self._token_file_path):
            try:
                with open(self._token_file_path, encoding="utf-8") as f:
                    data = json_load(f)
                    self._set_oauth_data(data.get(OAUTH_DATA_KEY, {}))

                    _LOGGER.debug("Refresh token loaded from '%s'", self._token_file_path)
                    return super().load_token()
            except (OSError, json.JSONDecodeError) as e:
                _LOGGER.error("Failed to load OAuth data: %s", e)
                raise TadoException(f"Failed to load OAuth data: {e}") from e

        return super().load_token()
