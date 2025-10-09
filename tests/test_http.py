"""Test the Http class."""

import io
import json
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

import responses

from PyTado.const import CLIENT_ID_DEVICE
from PyTado.exceptions import TadoException
from PyTado.http import Domain, Endpoint, Http, TadoRequest

from . import common


class TestHttp(unittest.TestCase):
    """Test cases for the Http class."""

    def setUp(self):
        """Set up mock responses for HTTP requests."""
        super().setUp()

        responses.add(
            responses.POST,
            "https://login.tado.com/oauth2/device_authorize",
            json={
                "device_code": "XXX_code_XXX",
                "expires_in": 300,
                "interval": 1,
                "user_code": "7BQ5ZQ",
                "verification_uri": "https://login.tado.com/oauth2/device",
                "verification_uri_complete": "https://login.tado.com/oauth2/device?user_code=7BQ5ZQ",
            },
            status=200,
        )

        responses.add(
            responses.POST,
            "https://login.tado.com/oauth2/token",
            json={
                "access_token": "value",
                "expires_in": 1000,
                "refresh_token": "another_value",
            },
            status=200,
        )

        responses.add(
            responses.GET,
            "https://my.tado.com/api/v2/me",
            json=json.loads(common.load_fixture("home_1234/my_api_v2_me.json")),
            status=200,
        )

        responses.add(
            responses.GET,
            "https://my.tado.com/api/v2/homes/1234/",
            json=json.loads(
                common.load_fixture("home_1234/tadov2.my_api_v2_home_state.json")
            ),
            status=200,
        )

    @responses.activate
    def test_login_successful(self):
        """Test that login is successful and sets the correct properties."""
        instance = Http(debug=True)
        instance.device_activation()

        # Verify that the login was successful
        self.assertEqual(instance._id, 1234)
        self.assertEqual(instance.is_x_line, False)

    @responses.activate
    def test_login_failed(self):
        """Test that login fails with appropriate exceptions."""
        responses.replace(
            responses.POST,
            "https://login.tado.com/oauth2/token",
            json={"error": "invalid_grant"},
            status=400,
        )

        with self.assertRaises(
            expected_exception=TadoException,
            msg="Your username or password is invalid",
        ):
            instance = Http(debug=True)
            instance.device_activation()

        responses.replace(
            responses.POST,
            "https://login.tado.com/oauth2/token",
            json={"error": "server failed"},
            status=503,
        )

        with self.assertRaises(
            expected_exception=TadoException,
            msg="Login failed for unknown reason with status code 503",
        ):
            instance = Http(debug=True)
            instance.device_activation()

    @responses.activate
    def test_line_x(self):
        """Test that the we correctly identified new TadoX environments."""
        responses.replace(
            responses.GET,
            "https://my.tado.com/api/v2/homes/1234/",
            json=json.loads(
                common.load_fixture("home_1234/tadox.my_api_v2_home_state.json")
            ),
            status=200,
        )

        instance = Http(debug=True)
        instance.device_activation()

        # Verify that the login was successful
        self.assertEqual(instance._id, 1234)
        self.assertEqual(instance.is_x_line, True)

        @responses.activate
        def test_user_agent(self):
            """Test that the we set the correct user-agent."""
            responses.replace(
                responses.GET,
                "https://my.tado.com/api/v2/homes/1234/",
                json=json.loads(
                    common.load_fixture("home_1234/tadov2.my_api_v2_home_state.json")
                ),
                match=[matchers.header_matcher({"user-agent": "MyCustomAgent/1.0"})],
                status=200,
            )

            instance = Http(debug=True, user_agent="MyCustomAgent/1.0")
            instance.device_activation()

            # Verify that the login was successful
            self.assertEqual(instance._id, 1234)

    @responses.activate
    def test_refresh_token_success(self):
        """Test that the refresh token is successfully updated."""
        instance = Http(debug=True)
        instance.device_activation()

        expected_params = {
            "client_id": CLIENT_ID_DEVICE,
            "grant_type": "refresh_token",
            "refresh_token": "another_value",
        }
        # Mock the refresh token response
        refresh_token = responses.replace(
            responses.POST,
            "https://login.tado.com/oauth2/token",
            match=[
                responses.matchers.query_param_matcher(expected_params),
            ],
            json={
                "access_token": "new_value",
                "expires_in": 1234,
                "refresh_token": "new_refresh_value",
            },
            status=200,
        )

        # Force token refresh
        instance._refresh_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        instance._refresh_token()

        assert refresh_token.call_count == 1

        # Verify that the token was refreshed
        self.assertEqual(instance._headers["Authorization"], "Bearer new_value")

    @responses.activate
    def test_refresh_token_failure(self):
        """Test that refresh token failure raises an exception."""
        instance = Http(debug=True)
        instance.device_activation()

        # Mock the refresh token response with failure
        refresh_token = responses.replace(
            responses.POST,
            "https://login.tado.com/oauth2/token",
            json={"error": "invalid_grant"},
            status=400,
        )

        # Force token refresh
        instance._refresh_at = datetime.now(timezone.utc) - timedelta(seconds=1)

        with self.assertRaises(TadoException):
            instance._refresh_token()

        assert refresh_token.call_count == 1

    @responses.activate
    def test_configure_url_endpoint_mobile(self):
        """Test URL configuration for the MOBILE endpoint."""
        http = Http()
        request = TadoRequest(endpoint=Endpoint.MOBILE, command="test")
        url = http._configure_url(request)
        self.assertEqual(url, "https://my.tado.com/mobile/1.9/test")

    @responses.activate
    def test_configure_url_domain_device(self):
        """Test URL configuration for the DEVICES domain."""
        http = Http()
        request = TadoRequest(command="test", domain=Domain.DEVICES, device="id1234")
        url = http._configure_url(request)
        self.assertEqual(url, "https://my.tado.com/api/v2/devices/id1234/test")

    @responses.activate
    def test_configure_url_domain_me(self):
        """Test URL configuration for the ME domain."""
        http = Http()
        request = TadoRequest(command="test", domain=Domain.ME)
        url = http._configure_url(request)
        self.assertEqual(url, "https://my.tado.com/api/v2/me")

    @responses.activate
    def test_configure_url_domain_home_with_params(self):
        """Test URL configuration for the ME domain."""
        http = Http()
        http._id = 123
        request = TadoRequest(
            command="test", domain=Domain.HOME, params={"test": "value"}
        )
        url = http._configure_url(request)
        self.assertEqual(url, "https://my.tado.com/api/v2/homes/123/test?test=value")

    @responses.activate
    @mock.patch("time.sleep", return_value=None)
    def test_check_device_activation(self, mock_sleep):
        """Test the device activation check process."""

        http = Http()
        http._device_flow_data = {"interval": 5, "device_code": "mock_code"}
        http._expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

        result = http._check_device_activation()
        self.assertTrue(result)
        mock_sleep.assert_called_once_with(5)

    @responses.activate
    def test_save_refresh_token(self):
        """Test if refresh token is saved."""

        buffer = io.StringIO()

        # We need to disable the `close` method, since we can't call
        # getvalue() on a closed StringIO object.
        buffer.close = lambda: None

        mock_open = mock.mock_open()
        mock_open.return_value = buffer

        with mock.patch("builtins.open", mock_open) as mock_file:
            http = Http(token_file_path="path/to/open")
            http._check_device_activation()

        mock_file.assert_called_with("path/to/open", "w", encoding="utf-8")
        assert mock_open.return_value.getvalue() == '{"refresh_token": "another_value"}'

    @responses.activate
    @mock.patch("os.path.exists")
    @mock.patch("PyTado.http.Http._save_token")
    def test_load_refresh_token(self, mock_save, mock_exists):
        """Test if token is loaded."""

        def side_effect(filename):
            if filename == "path/to/open":
                return True
            else:
                return False

        mock_exists.side_effect = side_effect

        with mock.patch(
            "builtins.open",
            mock.mock_open(read_data='{"refresh_token": "saved_value"}'),
        ) as mock_file:
            http = Http(token_file_path="path/to/open")

        mock_save.assert_called_once()
        mock_file.assert_called_with("path/to/open", encoding="utf-8")
        assert http._device_activation_status == "COMPLETED"

    @mock.patch("PyTado.http.Http._refresh_token", return_value=True)
    @mock.patch("PyTado.http.Http._device_ready")
    @mock.patch("PyTado.http.Http._load_token")
    @mock.patch("PyTado.http.Http._login_device_flow")
    def test_constructor_with_valid_refresh_token(
        self,
        mock_load_token,
        mock_login_device_flow,
        mock_device_ready,
        mock_refresh_token,
    ):
        """
        Test that the Http constructor correctly uses a provided valid refresh token.
        """
        refresh_token = "mock_refresh_token"

        Http(saved_refresh_token=refresh_token)

        mock_refresh_token.assert_called_once_with(
            refresh_token=refresh_token, force_refresh=True
        )
        mock_device_ready.assert_called_once()
        mock_load_token.assert_not_called()
        mock_login_device_flow.assert_not_called()
