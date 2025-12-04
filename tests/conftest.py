"""Fixtures for Huckleberry integration tests."""
import pytest
from unittest.mock import MagicMock

from custom_components.huckleberry.const import DOMAIN

@pytest.fixture(scope="function")
def event_loop():
    """Create an instance of the event loop."""
    import asyncio
    from pytest_socket import enable_socket

    # Enable sockets before creating the loop to avoid Windows ProactorEventLoop issues
    enable_socket()

    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations defined in the test dir."""
    yield

@pytest.fixture(autouse=True)
def socket_enabled():
    """Override socket_enabled to always be true."""
    return True


@pytest.fixture
def mock_huckleberry_api():
    """Mock the Huckleberry API."""
    mock = MagicMock()
    mock.authenticate = MagicMock()
    mock.get_children = MagicMock(return_value=[
        {
            "uid": "child_1",
            "name": "Test Child",
            "birthday": "2023-01-01",
            "gender": "boy",
            "profilePictureUrl": None
        }
    ])
    mock.setup_realtime_listener = MagicMock()
    mock.setup_feed_listener = MagicMock()
    mock.setup_health_listener = MagicMock()
    mock.setup_diaper_listener = MagicMock()
    mock.stop_all_listeners = MagicMock()
    return mock

@pytest.fixture
def mock_setup_entry():
    """Mock setting up a config entry."""
    with pytest.patch(
        "custom_components.huckleberry.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup
