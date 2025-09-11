"""Test the Http class."""

from datetime import datetime, timedelta, timezone
import io
import json
import unittest
from unittest import mock
import pytest
import responses

from PyTado.const import CLIENT_ID_DEVICE
from PyTado.exceptions import TadoException
from PyTado.http import Domain, Endpoint, Http, TadoRequest
from PyTado.token_manager.token_manager_interface import TokenManagerInterface

from . import common


@pytest.fixture(scope="class")
def token_manager_authenticated(request):
    """Fixture to create a mock TokenManagerInterface."""
    mockit = mock.MagicMock()

    # Mock the methods of TokenManagerInterface
    mockit.save_oauth_data = mock.MagicMock()
    mockit.load_token = mock.MagicMock(return_value="mock_refresh_token")
    mockit.has_pending_device_data = mock.MagicMock(return_value=False)
    mockit.save_pending_device_data = mock.MagicMock()
    mockit.load_pending_device_data = mock.MagicMock(return_value=None)
    mockit.lock_device_activation = mock.MagicMock()
    mockit.is_locked = mock.MagicMock(return_value=False)

    request.cls.token_manager_authenticated = mockit


@pytest.fixture(scope="class")
def token_manager_pending(request):
    """Fixture to create a mock TokenManagerInterface."""
    mockit = mock.MagicMock()

    # Mock the methods of TokenManagerInterface
    mockit.save_oauth_data = mock.MagicMock()
    mockit.load_token = mock.MagicMock(return_value=None)
    mockit.has_pending_device_data = mock.MagicMock(return_value=True)
    mockit.save_pending_device_data = mock.MagicMock()
    mockit.load_pending_device_data = mock.MagicMock(
        return_value={"interval": 5, "device_code": "mock_code", "expires_in": 5}
    )
    mockit.lock_device_activation = mock.MagicMock()
    mockit.is_locked = mock.MagicMock(return_value=False)

    request.cls.token_manager_pending = mockit


@pytest.mark.usefixtures("token_manager_authenticated")
@pytest.mark.usefixtures("token_manager_pending")
class TestHttp(unittest.TestCase):
    """Test cases for the Http class."""

    # will be replaced by token_manager_* fixtures
    token_manager_authenticated: TokenManagerInterface = None
    token_manager_pending: TokenManagerInterface = None

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
        instance = Http(debug=True, token_manager=self.token_manager_authenticated)
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
            instance = Http(debug=True, token_manager=self.token_manager_authenticated)
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
            instance = Http(debug=True, token_manager=self.token_manager_authenticated)
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

        instance = Http(debug=True, token_manager=self.token_manager_authenticated)
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
                    common.load_fixture(
                        "home_1234/tadov2.my_api_v2_home_state.json"
                    )
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
        instance = Http(debug=True, token_manager=self.token_manager_authenticated)
        instance.device_activation()

        expected_params = {
            "client_id": CLIENT_ID_DEVICE,
            "grant_type": "refresh_token",
            "refresh_token": self.token_manager_authenticated.load_token(),
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

        self.token_manager_authenticated.has_valid_refresh_token = mock.MagicMock(
            return_value=False
        )

        # Force token refresh
        instance._refresh_token()

        assert refresh_token.call_count == 1

        # Verify that the token was refreshed
        self.assertEqual(instance._headers["Authorization"], "Bearer new_value")

    @responses.activate
    def test_refresh_token_failure(self):
        """Test that refresh token failure raises an exception."""
        instance = Http(debug=True, token_manager=self.token_manager_authenticated)
        instance.device_activation()

        # Mock the refresh token response with failure
        refresh_token = responses.replace(
            responses.POST,
            "https://login.tado.com/oauth2/token",
            json={"error": "invalid_grant"},
            status=400,
        )

        self.token_manager_authenticated.has_valid_refresh_token = mock.MagicMock(
            return_value=False
        )

        with self.assertRaises(TadoException):
            instance._refresh_token()

        assert refresh_token.call_count == 1

    @responses.activate
    def test_configure_url_endpoint_mobile(self):
        """Test URL configuration for the MOBILE endpoint."""
        http = Http(token_manager=self.token_manager_authenticated)
        request = TadoRequest(endpoint=Endpoint.MOBILE, command="test")
        url = http._configure_url(request)
        self.assertEqual(url, "https://my.tado.com/mobile/1.9/test")

    @responses.activate
    def test_configure_url_domain_device(self):
        """Test URL configuration for the DEVICES domain."""
        http = Http(token_manager=self.token_manager_authenticated)
        request = TadoRequest(command="test", domain=Domain.DEVICES, device="id1234")
        url = http._configure_url(request)
        self.assertEqual(url, "https://my.tado.com/api/v2/devices/id1234/test")

    @responses.activate
    def test_configure_url_domain_me(self):
        """Test URL configuration for the ME domain."""
        http = Http(token_manager=self.token_manager_authenticated)
        request = TadoRequest(command="test", domain=Domain.ME)
        url = http._configure_url(request)
        self.assertEqual(url, "https://my.tado.com/api/v2/me")

    @responses.activate
    def test_configure_url_domain_home_with_params(self):
        """Test URL configuration for the ME domain."""
        http = Http(token_manager=self.token_manager_authenticated)
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

        http = Http(token_manager=self.token_manager_pending)

        result = http._check_device_activation()
        self.assertTrue(result)
        mock_sleep.assert_called_once_with(5)
