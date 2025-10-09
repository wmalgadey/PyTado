import unittest
from unittest import mock

import pytest
from unittest import mock
from PyTado.__main__ import (
    main,
    log_in,
    get_me,
    get_state,
    get_states,
    get_capabilities,
)

from PyTado.__main__ import (
    get_capabilities,
    get_me,
    get_state,
    get_states,
    log_in,
    main,
)


class TestMain(unittest.TestCase):
    """Test cases for the methods in __main__.py."""

    def test_entry_point_no_args(self):
        """Test the main() method."""
        with pytest.raises(SystemExit) as excinfo:
            main()

        assert excinfo.value.code == 2

    @mock.patch("PyTado.__main__.Tado")
    def test_log_in(self, mock_tado):
        """Test the log_in method."""
        args = mock.Mock()
        args.token_file_path = "mock_token_file_path"

        # Call the method
        tado_instance = log_in(args)

        # Verify that Tado was initialized and device_activation was called
        mock_tado.assert_called_once_with(token_file_path="mock_token_file_path")
        mock_tado.return_value.device_activation.assert_called_once()
        self.assertEqual(tado_instance, mock_tado.return_value)

    @mock.patch("PyTado.__main__.log_in")
    def test_get_me(self, mock_log_in):
        """Test the get_me method."""
        args = mock.Mock()
        mock_tado_instance = mock.Mock()
        mock_log_in.return_value = mock_tado_instance
        mock_tado_instance.get_me.return_value = {"mock": "data"}

        # Call the method
        with mock.patch("builtins.print") as mock_print:
            get_me(args)

            # Verify that log_in was called and get_me was called
            mock_log_in.assert_called_once_with(args)
            mock_tado_instance.get_me.assert_called_once()

            # Verify that the output was printed
            mock_print.assert_called_once_with({"mock": "data"})

    @mock.patch("PyTado.__main__.log_in")
    def test_get_state(self, mock_log_in):
        """Test the get_state method."""
        args = mock.Mock()
        args.zone = "1"
        mock_tado_instance = mock.Mock()
        mock_log_in.return_value = mock_tado_instance
        mock_tado_instance.get_state.return_value = {"zone": "state"}

        # Call the method
        with mock.patch("builtins.print") as mock_print:
            get_state(args)

            # Verify that log_in was called and get_state was called
            mock_log_in.assert_called_once_with(args)
            mock_tado_instance.get_state.assert_called_once_with(1)

            # Verify that the output was printed
            mock_print.assert_called_once_with({"zone": "state"})

    @mock.patch("PyTado.__main__.log_in")
    def test_get_states(self, mock_log_in):
        """Test the get_states method."""
        args = mock.Mock()
        mock_tado_instance = mock.Mock()
        mock_log_in.return_value = mock_tado_instance
        mock_tado_instance.get_zone_states.return_value = [
            {"zone": "state1"},
            {"zone": "state2"},
        ]

        # Call the method
        with mock.patch("builtins.print") as mock_print:
            get_states(args)

            # Verify that log_in was called and get_zone_states was called
            mock_log_in.assert_called_once_with(args)
            mock_tado_instance.get_zone_states.assert_called_once()

            # Verify that the output was printed
            mock_print.assert_called_once_with([{"zone": "state1"}, {"zone": "state2"}])

    @mock.patch("PyTado.__main__.log_in")
    def test_get_capabilities(self, mock_log_in):
        """Test the get_capabilities method."""
        args = mock.Mock()
        args.zone = "1"
        mock_tado_instance = mock.Mock()
        mock_log_in.return_value = mock_tado_instance
        mock_tado_instance.get_capabilities.return_value = {"capabilities": "data"}

        # Call the method
        with mock.patch("builtins.print") as mock_print:
            get_capabilities(args)

            # Verify that log_in was called and get_capabilities was called
            mock_log_in.assert_called_once_with(args)
            mock_tado_instance.get_capabilities.assert_called_once_with(1)

            # Verify that the output was printed
            mock_print.assert_called_once_with({"capabilities": "data"})
