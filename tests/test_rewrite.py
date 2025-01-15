"""Tests for PyTado."""


import pytest
import responses

from PyTado.http import Http

from .const import TADO_API_URL, TADO_TOKEN_URL


def test_login_success() -> None:
    """Test login success."""
    tado = Http(username="username", password="password")

    assert tado._session is not None
    assert "response" in tado._session.hooks
    assert tado._log_response in tado._session.hooks["response"]
    assert tado._headers == {
        "Referer": "https://app.tado.com/",
        "Authorization": "Bearer test_access_token",
    }
    assert tado._username == "username"
    assert tado._password == "password"


@responses.activate
def test_login_failure() -> None:
    """Test login failure."""
    responses.add(
        responses.POST,
        f"{TADO_TOKEN_URL}",
        json={"error": "invalid_grant", "error_description": "Invalid credentials"},
        status=401,
    )

    responses.add(
        responses.GET,
        f"{TADO_API_URL}/me",
        json={"error": "unauthorized", "error_description": "Unauthorized"},
        status=401,
    )

    with pytest.raises(Exception) as excinfo:
        Http(username="username", password="password")
    assert "Login failed for unknown reason with status code 401" in str(excinfo.value)
