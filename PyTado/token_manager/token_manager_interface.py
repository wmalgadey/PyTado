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
