from http import HTTPStatus
from unittest.mock import MagicMock, patch

import pytest
from http_connection import HTTPConnection, HTTPRequestError, check_if_http_status_is_ok
from login_data import LoginData
from message import Message
from parsing_utils import HTTPStateError, JSONError


def test_singleton():
    assert HTTPConnection() == HTTPConnection()


def test_check_if_http_status_is_ok():
    check_if_http_status_is_ok({"status": "200"})

    with pytest.raises(HTTPStateError):
        check_if_http_status_is_ok({"status": "404"})

    with pytest.raises(HTTPStateError):
        check_if_http_status_is_ok({"status": "500"})


def test_http_request_error():
    err = HTTPRequestError("Request failed")
    assert str(err) == "'Request failed'"


@pytest.fixture
def conn():
    # Reset singleton instance for fresh tests if needed
    conn_obj = HTTPConnection()
    conn_obj._HTTPConnection__webclient = MagicMock()
    conn_obj._HTTPConnection__token = "0123456789abcdef0123456789abcdef"
    conn_obj._HTTPConnection__user_id = "12345"
    conn_obj._HTTPConnection__session.open_session("sess123", "1")
    return conn_obj


def test_login(conn):
    login_info = LoginData(server=1, username="testuser", password="secretpassword")
    dispatch_response = {"status": "200"}
    dispatch_content = b'{"status":"ok", "url":"https://s1.wurzelimperium.de/logw.php?token=0123456789abcdef0123456789abcdef"}'

    redirect_response = {
        "status": "302",
        "set-cookie": "PHPSESSID=phpsess123; path=/, wunr=67890; path=/",
    }
    redirect_content = b""

    conn._HTTPConnection__webclient.request.side_effect = [
        (dispatch_response, dispatch_content),
        (redirect_response, redirect_content),
    ]

    conn.login(login_info)
    assert conn.user_id == "67890"


def test_login_invalid_token(conn):
    login_info = LoginData(server=1, username="testuser", password="secretpassword")
    dispatch_response = {"status": "200"}
    dispatch_content = (
        b'{"status":"ok", "url":"https://s1.wurzelimperium.de/invalid_url"}'
    )

    conn._HTTPConnection__webclient.request.return_value = (
        dispatch_response,
        dispatch_content,
    )

    with pytest.raises(JSONError, match="Fehler bei der Ermittlung des Tokens"):
        conn.login(login_info)


def test_logout(conn):
    logout_response = {
        "status": "302",
        "set-cookie": "PHPSESSID=deleted; path=/",
    }
    conn._HTTPConnection__webclient.request.return_value = (logout_response, b"")
    conn.logout()


def test_execute_command(conn):
    conn._HTTPConnection__webclient.request.return_value = (
        {"status": "200"},
        b'{"status":"ok", "data":{"value": 1}}',
    )
    result = conn.execute_command("do=testCommand")
    assert result["status"] == "ok"
    assert result["data"]["value"] == 1


def test_execute_tree_gardencommand(conn):
    conn._HTTPConnection__webclient.request.return_value = (
        {"status": "200"},
        b'{"status":"SUCCESS", "data": "tree_ok"}',
    )
    result = conn.execute_tree_gardencommand("op=test")
    assert result["status"] == "SUCCESS"


def test_execute_decogarden_command(conn):
    conn._HTTPConnection__webclient.request.return_value = (
        {"status": "200"},
        b'{"status":"ok", "objects": {}}',
    )
    result = conn.execute_decogarden_command("do=getGarden")
    assert result["status"] == "ok"


def test_execute_wimp_command(conn):
    conn._HTTPConnection__webclient.request.return_value = (
        {"status": "200"},
        b'{"status":"ok", "wimps": []}',
    )
    result = conn.execute_wimp_command("do=getAreaData")
    assert result["status"] == "ok"


def test_execute_market_command(conn):
    conn._HTTPConnection__webclient.request.return_value = (
        {"status": "200"},
        b"<html><table></table></html>",
    )
    content = conn.execute_market_command(identifier=1, page=1)
    assert "<html>" in content


def test_destroy_weed_field(conn):
    conn._HTTPConnection__webclient.request.return_value = (
        {"status": "200"},
        b'{"success": 1}',
    )
    result = conn.destroy_weed_field(5)
    assert result["success"] == 1


def test_execute_message_command(conn):
    # Without message object (GET)
    conn._HTTPConnection__webclient.request.return_value = (
        {"status": "200"},
        b"Message content",
    )
    res_get = conn.execute_message_command("list.php")
    assert res_get == b"Message content"

    # With message object (POST)
    msg = Message(id=1, recipient="User", subject="Subj", body="Body")
    res_post = conn.execute_message_command("new.php", msg)
    assert res_post == b"Message content"


def test_read_user_data_from_server(conn):
    conn._HTTPConnection__webclient.request.return_value = (
        {"status": "200"},
        b'{"success": 1, "levelnr": 5}',
    )
    user_data = conn.read_user_data_from_server()
    assert user_data["levelnr"] == 5


def test_grow_and_water_plant(conn):
    conn._HTTPConnection__webclient.request.return_value = (
        {"status": "200"},
        b"success: 1\n",
    )
    conn.grow_plant(field=1, plant=2, garden_id=1, fields="1")
    conn.water_plant(garden_id=1, field_id=1, fields_to_water="1")


def test_get_username_from_server(conn):
    conn._HTTPConnection__webclient.request.return_value = (
        {"status": "200"},
        b'{"status":"ok", "table": ["<tr><td>Spielername</td><td>Tester</td></tr>"]}',
    )
    data = conn.get_username_from_server()
    assert data["status"] == "ok"


def test_get_trophies(conn):
    conn._HTTPConnection__webclient.request.return_value = (
        {"status": "200"},
        b'{"status":"ok", "html": "trophies"}',
    )
    trophies = conn.get_trophies()
    assert trophies["status"] == "ok"


def test_get_user_profile(conn):
    conn._HTTPConnection__webclient.request.return_value = (
        {"status": "200"},
        b"<html>User Profile</html>",
    )
    profile = conn.get_user_profile()
    assert "User Profile" in profile


def test_read_and_update_storage(conn):
    conn._HTTPConnection__webclient.request.return_value = (
        {"status": "200"},
        b'{"status":"ok", "produkte": {"1": 100}}',
    )
    storage = conn.read_storage_from_server()
    assert storage == {"1": 100}

    conn.update_storage()


def test_get_all_product_informations(conn):
    conn._HTTPConnection__webclient.request.return_value = (
        {"status": "200"},
        b'data_products = {};var other = 1; ajax.setToken("abcdef1234567890abcdef1234567890");',
    )
    content = conn.get_all_product_informations()
    assert "data_products" in content


def test_get_all_tradeable_products(conn):
    conn._HTTPConnection__webclient.request.return_value = (
        {"status": "200"},
        b'<a href="markt.php?show=overview">Markt</a>',
    )
    content = conn.get_all_tradeable_products()
    assert b"Markt" in content


def test_get_npc_prices(conn):
    conn._HTTPConnection__webclient.request.return_value = (
        {"status": "200"},
        b"<html><table><tr><td>Salat</td><td>0,16 wT</td></tr></table></html>",
    )
    prices_html = conn.get_npc_prices()
    assert "Salat" in prices_html


def test_get_notes(conn):
    conn._HTTPConnection__webclient.request.return_value = (
        {"status": "200"},
        b"<html><textarea id='notiztext'>minStock: 10</textarea></html>",
    )
    notes_html = conn.get_notes()
    assert "minStock: 10" in notes_html


def test_sell_on_market(conn):
    conn._HTTPConnection__webclient.request.return_value = (
        {"status": "200"},
        b'{"status":"ok", "produkte": {}}',
    )
    conn.sell_on_market(item_id=1, price=1.50, number=10)
    assert conn._HTTPConnection__webclient.request.call_count >= 4


def test_check_if_http_status_is_ok():
    check_if_http_status_is_ok({"status": "200"})

    with pytest.raises(HTTPStateError):
        check_if_http_status_is_ok({"status": "404"})

    with pytest.raises(HTTPStateError):
        check_if_http_status_is_ok({"status": "500"})


def test_http_request_error():
    err = HTTPRequestError("Request failed")
    assert str(err) == "'Request failed'"


@pytest.fixture
def conn():
    # Reset singleton instance for fresh tests if needed
    conn_obj = HTTPConnection()
    conn_obj._HTTPConnection__webclient = MagicMock()
    conn_obj._HTTPConnection__token = "0123456789abcdef0123456789abcdef"
    conn_obj._HTTPConnection__user_id = "12345"
    conn_obj._HTTPConnection__session.open_session("sess123", "1")
    return conn_obj


def test_login(conn):
    login_info = LoginData(server=1, username="testuser", password="secretpassword")
    dispatch_response = {"status": "200"}
    dispatch_content = b'{"status":"ok", "url":"https://s1.wurzelimperium.de/logw.php?token=0123456789abcdef0123456789abcdef"}'

    redirect_response = {
        "status": "302",
        "set-cookie": "PHPSESSID=phpsess123; path=/, wunr=67890; path=/",
    }
    redirect_content = b""

    conn._HTTPConnection__webclient.request.side_effect = [
        (dispatch_response, dispatch_content),
        (redirect_response, redirect_content),
    ]

    conn.login(login_info)
    assert conn.user_id == "67890"


def test_login_invalid_token(conn):
    login_info = LoginData(server=1, username="testuser", password="secretpassword")
    dispatch_response = {"status": "200"}
    dispatch_content = (
        b'{"status":"ok", "url":"https://s1.wurzelimperium.de/invalid_url"}'
    )

    conn._HTTPConnection__webclient.request.return_value = (
        dispatch_response,
        dispatch_content,
    )

    with pytest.raises(JSONError, match="Fehler bei der Ermittlung des Tokens"):
        conn.login(login_info)


def test_logout(conn):
    logout_response = {
        "status": "302",
        "set-cookie": "PHPSESSID=deleted; path=/",
    }
    conn._HTTPConnection__webclient.request.return_value = (logout_response, b"")
    conn.logout()


def test_execute_command(conn):
    conn._HTTPConnection__webclient.request.return_value = (
        {"status": "200"},
        b'{"status":"ok", "data":{"value": 1}}',
    )
    result = conn.execute_command("do=testCommand")
    assert result["status"] == "ok"
    assert result["data"]["value"] == 1


def test_execute_tree_gardencommand(conn):
    conn._HTTPConnection__webclient.request.return_value = (
        {"status": "200"},
        b'{"status":"SUCCESS", "data": "tree_ok"}',
    )
    result = conn.execute_tree_gardencommand("op=test")
    assert result["status"] == "SUCCESS"


def test_execute_decogarden_command(conn):
    conn._HTTPConnection__webclient.request.return_value = (
        {"status": "200"},
        b'{"status":"ok", "objects": {}}',
    )
    result = conn.execute_decogarden_command("do=getGarden")
    assert result["status"] == "ok"


def test_execute_wimp_command(conn):
    conn._HTTPConnection__webclient.request.return_value = (
        {"status": "200"},
        b'{"status":"ok", "wimps": []}',
    )
    result = conn.execute_wimp_command("do=getAreaData")
    assert result["status"] == "ok"


def test_execute_market_command(conn):
    conn._HTTPConnection__webclient.request.return_value = (
        {"status": "200"},
        b"<html><table></table></html>",
    )
    content = conn.execute_market_command(identifier=1, page=1)
    assert "<html>" in content


def test_destroy_weed_field(conn):
    conn._HTTPConnection__webclient.request.return_value = (
        {"status": "200"},
        b'{"success": 1}',
    )
    result = conn.destroy_weed_field(5)
    assert result["success"] == 1


def test_execute_message_command(conn):
    # Without message object (GET)
    conn._HTTPConnection__webclient.request.return_value = (
        {"status": "200"},
        b"Message content",
    )
    res_get = conn.execute_message_command("list.php")
    assert res_get == b"Message content"

    # With message object (POST)
    msg = Message(id=1, recipient="User", subject="Subj", body="Body")
    res_post = conn.execute_message_command("new.php", msg)
    assert res_post == b"Message content"


def test_read_user_data_from_server(conn):
    conn._HTTPConnection__webclient.request.return_value = (
        {"status": "200"},
        b'{"success": 1, "levelnr": 5}',
    )
    user_data = conn.read_user_data_from_server()
    assert user_data["levelnr"] == 5


def test_grow_and_water_plant(conn):
    conn._HTTPConnection__webclient.request.return_value = (
        {"status": "200"},
        b"success: 1\n",
    )
    conn.grow_plant(field=1, plant=2, garden_id=1, fields="1")
    conn.water_plant(garden_id=1, field_id=1, fields_to_water="1")


def test_get_username_from_server(conn):
    conn._HTTPConnection__webclient.request.return_value = (
        {"status": "200"},
        b'{"status":"ok", "table": ["<tr><td>Spielername</td><td>Tester</td></tr>"]}',
    )
    data = conn.get_username_from_server()
    assert data["status"] == "ok"


def test_get_trophies(conn):
    conn._HTTPConnection__webclient.request.return_value = (
        {"status": "200"},
        b'{"status":"ok", "html": "trophies"}',
    )
    trophies = conn.get_trophies()
    assert trophies["status"] == "ok"


def test_get_user_profile(conn):
    conn._HTTPConnection__webclient.request.return_value = (
        {"status": "200"},
        b"<html>User Profile</html>",
    )
    profile = conn.get_user_profile()
    assert "User Profile" in profile


def test_read_and_update_storage(conn):
    conn._HTTPConnection__webclient.request.return_value = (
        {"status": "200"},
        b'{"status":"ok", "produkte": {"1": 100}}',
    )
    storage = conn.read_storage_from_server()
    assert storage == {"1": 100}

    conn.update_storage()


def test_get_all_product_informations(conn):
    conn._HTTPConnection__webclient.request.return_value = (
        {"status": "200"},
        b'data_products = {};var other = 1; ajax.setToken("abcdef1234567890abcdef1234567890");',
    )
    content = conn.get_all_product_informations()
    assert "data_products" in content


def test_get_all_tradeable_products(conn):
    conn._HTTPConnection__webclient.request.return_value = (
        {"status": "200"},
        b'<a href="markt.php?show=overview">Markt</a>',
    )
    content = conn.get_all_tradeable_products()
    assert b"Markt" in content


def test_get_npc_prices(conn):
    conn._HTTPConnection__webclient.request.return_value = (
        {"status": "200"},
        b"<html><table><tr><td>Salat</td><td>0,16 wT</td></tr></table></html>",
    )
    prices_html = conn.get_npc_prices()
    assert "Salat" in prices_html


def test_get_notes(conn):
    conn._HTTPConnection__webclient.request.return_value = (
        {"status": "200"},
        b"<html><textarea id='notiztext'>minStock: 10</textarea></html>",
    )
    notes_html = conn.get_notes()
    assert "minStock: 10" in notes_html


def test_sell_on_market(conn):
    conn._HTTPConnection__webclient.request.return_value = (
        {"status": "200"},
        b'{"status":"ok", "produkte": {}}',
    )
    conn.sell_on_market(item_id=1, price=1.50, number=10)
    assert conn._HTTPConnection__webclient.request.call_count >= 4
