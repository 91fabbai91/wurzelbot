import pytest
from login_data import LoginData
from pydantic import ValidationError


def test_login_data_valid():
    login = LoginData(server=1, username="testuser", password="secretpassword")
    assert login.server == 1
    assert login.username == "testuser"
    assert login.password.get_secret_value() == "secretpassword"

    login_46 = LoginData(server=46, username="user46", password="pw")
    assert login_46.server == 46


def test_login_data_server_validation_invalid_bounds():
    # server=0 fails PositiveInt
    with pytest.raises(ValidationError):
        LoginData(server=0, username="testuser", password="pw")

    # server=47 fails server_match
    with pytest.raises(ValidationError, match="Server must be Integer"):
        LoginData(server=47, username="testuser", password="pw")

    with pytest.raises(ValidationError, match="Server must be Integer"):
        LoginData(server=100, username="testuser", password="pw")


def test_login_data_frozen():
    login = LoginData(server=5, username="user", password="pw")
    with pytest.raises(ValidationError):
        login.username = "new_user"
