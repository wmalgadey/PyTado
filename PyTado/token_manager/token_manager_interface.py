from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import ContextManager


class DummyLock:
    """Dummy lock class for no real locking."""

    def __enter__(self):
        """Acquire the lock."""
        return

    def __exit__(self, exc_type, exc_value, traceback):
        """Release the lock."""
        return


class TokenManagerInterface(ABC):
    """Interface for a token manager to handle saving and loading of refresh tokens."""

    def __init__(self):
        super().__init__()

        self._refresh_at = datetime.now() - timedelta(minutes=10)
        self._token_refresh: str | None = None

    def _set_oauth_data(self, oauth_data: dict) -> None:
        """
        Set the oauth data.

        Args:
            oauth_data (dict): The oauth data to set.
        """

        self._token_refresh = oauth_data.get("refresh_token", None)

        expires_in = float(oauth_data.get("expires_in", 0))
        self._refresh_at = datetime.now()
        self._refresh_at = self._refresh_at + timedelta(seconds=expires_in)
        # We subtract 30 seconds from the correct refresh time.
        # Then we have a 30 seconds timespan to get a new refresh_token
        self._refresh_at = self._refresh_at - timedelta(seconds=30)

    def save_oauth_data(self, oauth_data: dict) -> None:
        """
        Save the refresh token.

        Args:
            refresh_token (str): The refresh token to save.
        """
        self._set_oauth_data(oauth_data)

    def has_valid_refresh_token(self) -> bool:
        """
        Check if a valid refresh token is available.

        Returns:
            bool: True if the refresh token is still valid, False otherwise.
        """
        self.load_token()

        return datetime.timestamp(datetime.now()) < datetime.timestamp(self._refresh_at)

    def lock_device_activation(self, msg) -> ContextManager:
        """
        Lock the token.

        This method should be implemented in a subclass.
        """
        return DummyLock()

    def is_locked(self) -> bool:
        """
        Check if the token is locked.

        This method should be implemented in a subclass.

        Returns:
            bool: True if the token is locked, False otherwise.
        """
        return False

    @abstractmethod
    def load_token(self) -> str | None:
        """
        Load the refresh token.

        Returns:
            str | None: The loaded refresh token, or None if not available.
        """
        return self._token_refresh

    def has_pending_device_data(self) -> bool:
        """
        Check if there is pending device data.

        Returns:
            bool: True if there is pending device data, False otherwise.
        """
        return False

    def save_pending_device_data(self, device_data: dict) -> None:
        """
        Save the device data for pending device activation.

        Args:
            device_data (dict): The device data to save after initial device activation.
        """
        pass

    def load_pending_device_data(self) -> dict:
        """
        Load the device data for pending device activation.

        Returns:
            dict | None: The device data, or None if not available.
        """
        return {}
