"""Test the Http class."""

import io
import unittest
from unittest import mock
import responses

from PyTado.token_manager.file_token_manager import FileTokenManager



class TestFileTokenManager(unittest.TestCase):
    """Test cases for the Http class."""

    def test_save_refresh_token(self):
        """Test if refresh token is saved."""

        buffer = io.StringIO()

        # We need to disable the `close` method, since we can't call
        # getvalue() on a closed StringIO object.
        buffer.close = lambda: None

        mock_open = mock.mock_open()
        mock_open.return_value = buffer

        with mock.patch("builtins.open", mock_open) as mock_file:
            token_manager = FileTokenManager(token_file_path="path/to/open")
            token_manager.save_oauth_data({"refresh_token": "another_value"})

        mock_file.assert_called_with("path/to/open", 'w', encoding='utf-8')
        assert mock_open.return_value.getvalue() == '{"oauth_data": {"refresh_token": "another_value"}}'


    @responses.activate
    @mock.patch('os.path.exists')
    def test_load_refresh_token(self, mock_exists):
        """Test if token is loaded."""
        def side_effect(filename):
            if filename == 'path/to/open':
                return True
            else:
                return False
        mock_exists.side_effect = side_effect

        with mock.patch("builtins.open", mock.mock_open(read_data='{"oauth_data": {"refresh_token": "saved_value"}}')) as mock_file:
            token_manager = FileTokenManager(token_file_path="path/to/open")
            assert token_manager.load_token() == "saved_value"

        mock_file.assert_called_with("path/to/open", encoding='utf-8')
