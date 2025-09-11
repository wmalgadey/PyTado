from contextlib import contextmanager
from typing import Generator

from PyTado.token_manager.can_manage_device_activation import CanManageDeviceActivation


class DummyDeviceManager(CanManageDeviceActivation):
    """Dummy implementation of CanManageDeviceActivation for fallback."""

    def has_pending_device_data(self) -> bool:
        """Always return False for pending device data."""
        return False

    def save_pending_device_data(self, device_data: dict) -> None:
        """Do nothing when saving pending device data."""
        pass

    def load_pending_device_data(self) -> dict:
        """Return an empty dictionary for pending device data."""
        return {}

    def is_locked(self) -> bool:
        """Always return False for lock status."""
        return False

    @contextmanager
    def lock_device_activation(self, msg: str) -> Generator[None, None, None]:
        """Provide a no-op context manager for locking."""
        yield
