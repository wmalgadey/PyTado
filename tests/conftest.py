"""Tests for Python Tado API."""

from typing import Generator

import pytest
import responses
from syrupy import SnapshotAssertion

from tests import load_fixture

from .syrupy import TadoSnapshotExtension


@pytest.fixture(name="snapshot")
def snapshot_assertion(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """Return snapshot assertion fixture with the Tado extension."""
    return snapshot.use_extension(TadoSnapshotExtension)


@pytest.fixture(autouse=True)
def mock_tado_api() -> Generator[responses.RequestsMock, None, None]:
    """Fixture to mock Tado API endpoints."""
    # Don't check that all requests have been executed
    with responses.RequestsMock(assert_all_requests_are_fired=False) as mock_responses:
        mock_responses.add(
            responses.POST,
            "https://auth.tado.com/oauth/token",
            json={
                "access_token": "test_access_token",
                "expires_in": 3600,
                "refresh_token": "test_refresh_token",
            },
            status=200,
        )
        mock_responses.add(
            responses.GET,
            "https://my.tado.com/api/v2/me",
            body=load_fixture(folder="home_1234", filename="my_api_v2_me.json"),
            status=200,
        )
        mock_responses.add(
            responses.GET,
            "https://my.tado.com/api/v2/homes/1234/",
            body=load_fixture(folder="home_1234", filename="tadov2.my_api_v2_home_state.json"),
            status=200,
        )

        yield mock_responses
