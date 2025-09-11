from abc import ABC, abstractmethod


class TokenManagerInterface(ABC):
    """Interface for a token manager to handle saving and loading of refresh tokens."""

    @abstractmethod
    def save_token(self, refresh_token: str) -> None:
        """
        Save the refresh token.

        Args:
            refresh_token (str): The refresh token to save.
        """
        pass

    @abstractmethod
    def load_token(self) -> str | None:
        """
        Load the refresh token.

        Returns:
            str | None: The loaded refresh token, or None if not available.
        """
        pass
