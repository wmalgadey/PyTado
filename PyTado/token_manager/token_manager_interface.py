from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone


class TokenManagerInterface(ABC):
    """Interface for a token manager to handle saving and loading of refresh tokens."""

    def __init__(self):
        super().__init__()

        self._refresh_at = datetime.now(timezone.utc) - timedelta(minutes=10)
        self._token_refresh: str | None = None

    def _set_oauth_data(self, oauth_data: dict) -> None:
        """
        Set the oauth data.

        Args:
            oauth_data (dict): The oauth data to set.
        """

        self._token_refresh = oauth_data.get("refresh_token", None)

        expires_in = float(oauth_data.get("expires_in", 0))
        self._refresh_at = datetime.now(timezone.utc)
        self._refresh_at = self._refresh_at + timedelta(seconds=expires_in)
        # We subtract 30 seconds from the correct refresh time.
        # Then we have a 30 seconds timespan to get a new refresh_token
        self._refresh_at = self._refresh_at - timedelta(seconds=30)

    def set_oauth_data(self, oauth_data: dict) -> None:
        """
        Set the oauth data.

        Args:
            oauth_data (dict): The oauth data to use.
        """
        self._set_oauth_data(oauth_data)

    def has_valid_refresh_token(self) -> bool:
        """
        Check if a valid refresh token is available.

        Returns:
            bool: True if the refresh token is still valid, False otherwise.
        """
        self.get_token()

        return datetime.timestamp(datetime.now(timezone.utc)) < datetime.timestamp(
            self._refresh_at
        )

    @abstractmethod
    def get_token(self) -> str | None:
        """
        Get the refresh token.

        Returns:
            str | None: The current refresh token, or None if not available.
        """
        return self._token_refresh
