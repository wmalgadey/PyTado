import io
import unittest
from unittest import mock
from datetime import datetime, timedelta, timezone
from PyTado.token_manager.device_token_manager import DeviceTokenManager, FileContent
from PyTado.exceptions import TadoException


class TestDeviceTokenManager(unittest.TestCase):
    """Unit tests for the DeviceTokenManager class."""

    def setUp(self):
        """Set up a DeviceTokenManager instance for testing."""
        file_lock = mock.patch("PyTado.token_manager.device_token_manager.FileLock")
        file_lock.start()
        self.addCleanup(file_lock.stop)

        self.token_manager = DeviceTokenManager()
        self.token_manager._token_file_path = "/mock/path/device_token.json"

    @mock.patch("os.path.exists", return_value=True)
    @mock.patch(
        "builtins.open",
        new_callable=mock.mock_open,
        read_data='{"pending_device": {"expires_at": "2099-12-31T23:59:59"}}',
    )
    def test_has_pending_device_data_true(self, mock_open, mock_exists):
        """Test has_pending_device_data returns True when valid data exists."""
        self.assertTrue(self.token_manager.has_pending_device_data())

    @mock.patch("os.path.exists", return_value=True)
    @mock.patch(
        "builtins.open",
        new_callable=mock.mock_open,
        read_data='{"pending_device": {"expires_at": "2000-01-01T00:00:00"}}',
    )
    def test_has_pending_device_data_false_expired(self, mock_open, mock_exists):
        """Test has_pending_device_data returns False when data is expired."""
        self.assertFalse(self.token_manager.has_pending_device_data())

    @mock.patch("os.path.exists", return_value=False)
    def test_has_pending_device_data_no_file(self, mock_exists):
        """Test has_pending_device_data returns False when no file exists."""
        self.assertFalse(self.token_manager.has_pending_device_data())

    @mock.patch("os.path.exists", return_value=True)
    @mock.patch("builtins.open", new_callable=mock.mock_open, read_data="{}")
    def test_get_pending_device_data_raises_exception(self, mock_open, mock_exists):
        """Test get_pending_device_data raises TadoException when no data exists."""
        with self.assertRaises(TadoException):
            self.token_manager.get_pending_device_data()

    @mock.patch("os.path.exists", return_value=True)
    @mock.patch(
        "builtins.open",
        new_callable=mock.mock_open,
        read_data='{"pending_device": {"expires_at": "2099-12-31T23:59:59"}}',
    )
    def test_get_pending_device_data_success(self, mock_open, mock_exists):
        """Test get_pending_device_data returns the correct data."""
        data = self.token_manager.get_pending_device_data()
        self.assertEqual(data, {"expires_at": "2099-12-31T23:59:59"})

    @mock.patch("os.path.exists", return_value=True)
    @mock.patch("pathlib.Path.mkdir")
    def test_set_pending_device_data(self, mock_mkdir, mock_exists):
        """Test set_pending_device_data saves data correctly."""
        device_data = {
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
            "device_code": "mock_code",
        }

        buffer = io.StringIO()

        # We need to disable the `close` method, since we can't call
        # getvalue() on a closed StringIO object.
        buffer.close = lambda: None

        mock_open = mock.mock_open()
        mock_open.return_value = buffer

        # with patch("os.path.exists", return_value=False):
        with mock.patch("builtins.open", mock_open) as mock_file:
            self.token_manager.set_pending_device_data(device_data)

            # self.assertTrue(self.token_manager.has_pending_device_data())

        mock_file.assert_called_with(
            self.token_manager._token_file_path, "w", encoding="utf-8"
        )


# class TestDeviceTokenManager2(unittest.TestCase):
#     """Unit tests for the DeviceTokenManager class."""

#     def setUp(self):
#         """Set up a DeviceTokenManager instance for testing."""

#         self.token_manager = DeviceTokenManager()

#     @mock.patch("os.path.exists", return_value=True)
#     @mock.patch("builtins.open", new_callable=mock.mock_open, read_data='{}')
#     def test_is_locked_false(self, mock_open, mock_exists):
#         """Test is_locked returns False when the file is not locked."""
#         with mock.patch("fcntl.flock") as mock_flock:
#             mock_flock.return_value = None
#             self.assertFalse(self.token_manager.is_locked())

#     @mock.patch("os.path.exists", return_value=True)
#     @mock.patch("builtins.open", new_callable=mock.mock_open, read_data='{}')
#     def test_is_locked_true(self, mock_open, mock_exists):
#         """Test is_locked returns True when the file is locked."""
#         with mock.patch("fcntl.flock", side_effect=BlockingIOError):
#             self.assertTrue(self.token_manager.is_locked())
