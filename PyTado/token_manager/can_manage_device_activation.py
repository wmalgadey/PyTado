from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Generator


class CanManageDeviceActivation(ABC):
    """
    Interface for managing device activation.

    This interface defines methods for managing device activation,
    including locking, checking for pending data, and saving/loading device data.
    """

    @abstractmethod
    @contextmanager
    def lock_device_activation(self, msg) -> Generator[None, None, None]:
        """
        Lock the token.

        This method should be implemented in a subclass.
        """

    @abstractmethod
    def is_locked(self) -> bool:
        """
        Check if the token is locked.

        This method should be implemented in a subclass.

        Returns:
            bool: True if the token is locked, False otherwise.
        """

    @abstractmethod
    def has_pending_device_data(self) -> bool:
        """
        Check if there is pending device data.

        Returns:
            bool: True if there is pending device data, False otherwise.
        """

    @abstractmethod
    def set_pending_device_data(self, device_data: dict) -> None:
        """
        Save the device data for pending device activation.

        Args:
            device_data (dict): The device data to save after initial device activation.
        """

    @abstractmethod
    def get_pending_device_data(self) -> dict:
        """
        Load the device data for pending device activation.

        Returns:
            dict | None: The device data, or None if not available.
        """
