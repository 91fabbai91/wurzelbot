import time
from unittest.mock import patch
from session import Session


def test_session_init():
    s = Session()
    assert s.session_id is None
    assert s.server is None
    assert s.is_session_valid() is False


def test_session_open_and_properties():
    s = Session()
    with patch("time.time", return_value=1000.0):
        s.open_session("abc123session", "server1")
        assert s.session_id == "abc123session"
        assert s.server == "server1"
        assert s.is_session_valid() is True
        # Lifetime is 7200, reserve 300 -> 6900s validity
        # End time = 1000 + 6900 = 7900
        assert s.get_remaining_time() == 6900.0


def test_session_elapsed():
    s = Session()
    with patch("time.time", return_value=1000.0):
        s.open_session("s_id", "s1")

    # Time before expiry (e.g. at 5000)
    with patch("time.time", return_value=5000.0):
        assert s.is_session_time_elapsed() is False
        assert s.is_session_valid() is True
        assert s.get_remaining_time() == 2900.0

    # Time exactly at expiry (7900.0) -> not strictly greater, so not elapsed
    with patch("time.time", return_value=7900.0):
        assert s.is_session_time_elapsed() is False

    # Time after expiry (7901.0)
    with patch("time.time", return_value=7901.0):
        assert s.is_session_time_elapsed() is True
        assert s.is_session_valid() is False
        assert s.get_remaining_time() < 0


def test_session_close():
    s = Session()
    s.open_session("my_session", "server2")
    assert s.session_id == "my_session"
    assert s.server == "server2"

    s.close_session()
    assert s.session_id is None
    assert s.server is None
    assert s.is_session_valid() is False

