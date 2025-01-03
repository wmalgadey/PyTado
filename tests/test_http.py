"""Test the Http class."""

from datetime import datetime, timedelta
import json
import responses
import unittest

from PyTado.const import CLIENT_ID, CLIENT_SECRET
from PyTado.exceptions import TadoException, TadoWrongCredentialsException

from . import common

from PyTado.http import Http


class TestHttp(unittest.TestCase):
    """Testcases for Http class."""

    def setUp(self):
        super().setUp()

        # Mock the login response
        responses.add(
            responses.POST,
            "https://auth.tado.com/oauth/token",
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
                common.load_fixture(
                    "home_1234/tadov2.my_api_v2_home_state.json"
                )
            ),
            status=200,
        )

    @responses.activate
    def test_login_successful(self):

        instance = Http(
            username="test_user",
            password="test_pass",
            debug=True,
        )

        # Verify that the login was successful
        self.assertEqual(instance._id, 1234)
        self.assertEqual(instance.is_x_line, False)

    @responses.activate
    def test_login_failed(self):

        responses.replace(
            responses.POST,
            "https://auth.tado.com/oauth/token",
            json={"error": "invalid_grant"},
            status=400,
        )

        with self.assertRaises(
            expected_exception=TadoWrongCredentialsException,
            msg="Your username or password is invalid",
        ):
            Http(
                username="test_user",
                password="test_pass",
                debug=True,
            )

        responses.replace(
            responses.POST,
            "https://auth.tado.com/oauth/token",
            json={"error": "server failed"},
            status=503,
        )

        with self.assertRaises(
            expected_exception=TadoException,
            msg="Login failed for unknown reason with status code 503",
        ):
            Http(
                username="test_user",
                password="test_pass",
                debug=True,
            )

    @responses.activate
    def test_line_x(self):

        responses.replace(
            responses.GET,
            "https://my.tado.com/api/v2/homes/1234/",
            json=json.loads(
                common.load_fixture("home_1234/tadox.my_api_v2_home_state.json")
            ),
            status=200,
        )

        instance = Http(
            username="test_user",
            password="test_pass",
            debug=True,
        )

        # Verify that the login was successful
        self.assertEqual(instance._id, 1234)
        self.assertEqual(instance.is_x_line, True)

    @responses.activate
    def test_refresh_token_success(self):
        instance = Http(
            username="test_user",
            password="test_pass",
            debug=True,
        )

        expected_params = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "refresh_token",
            "scope": "home.user",
            "refresh_token": "another_value",
        }
        # Mock the refresh token response
        refresh_token = responses.replace(
            responses.POST,
            "https://auth.tado.com/oauth/token",
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
        instance._refresh_at = datetime.now() - timedelta(seconds=1)
        instance._refresh_token()

        assert refresh_token.call_count == 1

        # Verify that the token was refreshed
        self.assertEqual(instance._headers["Authorization"], "Bearer new_value")

    @responses.activate
    def test_refresh_token_failure(self):
        instance = Http(
            username="test_user",
            password="test_pass",
            debug=True,
        )

        # Mock the refresh token response with failure
        refresh_token = responses.replace(
            responses.POST,
            "https://auth.tado.com/oauth/token",
            json={"error": "invalid_grant"},
            status=400,
        )

        # Force token refresh
        instance._refresh_at = datetime.now() - timedelta(seconds=1)

        with self.assertRaises(TadoException):
            instance._refresh_token()

        assert refresh_token.call_count == 1
