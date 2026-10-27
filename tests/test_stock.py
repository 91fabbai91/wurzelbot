from unittest.mock import MagicMock
from stock import Stock, merge_dictionaries


def test_merge_dictionaries():
    d1 = {
        "1": {"name": "Salat", "level": 1},
        "2": {"name": "Möhre", "level": 2},
    }
    d2 = {
        "1": 50,
        "2": 10,
    }
    merged = merge_dictionaries(d1, d2)
    assert merged["1"]["amount"] == 50
    assert merged["1"]["name"] == "Salat"
    assert merged["2"]["amount"] == 10
    assert merged["2"]["name"] == "Möhre"


def test_stock_init_and_storage(mock_http, sample_products_js_content):
    mock_http.get_all_product_informations.return_value = sample_products_js_content
    mock_http.read_storage_from_server.return_value = {"1": 100, "2": 25}

    stock_obj = Stock(mock_http)

    assert set(stock_obj.get_keys()) == {"1", "2", "3", "999"}
    assert stock_obj.get_stock_by_product_id(1) == 100
    assert stock_obj.get_stock_by_product_id("1") == 100
    assert stock_obj.get_stock_by_product_id(2) == 25
    assert stock_obj.get_stock_by_product_id(3) == 0


def test_stock_update_number_in_stock(mock_http, sample_products_js_content):
    mock_http.get_all_product_informations.return_value = sample_products_js_content
    mock_http.read_storage_from_server.return_value = {"1": 50}

    stock_obj = Stock(mock_http)
    assert stock_obj.get_stock_by_product_id(1) == 50

    # New storage response
    mock_http.read_storage_from_server.return_value = {"1": 70, "2": 15}
    stock_obj.update_number_in_stock()

    assert stock_obj.get_stock_by_product_id(1) == 70
    assert stock_obj.get_stock_by_product_id(2) == 15


def test_stock_ordered_list(mock_http, sample_products_js_content):
    mock_http.get_all_product_informations.return_value = sample_products_js_content
    # product 1 has amount 20, product 2 has amount 100, product 3 has 0 (filtered out)
    mock_http.read_storage_from_server.return_value = {"1": 20, "2": 100, "3": 0}

    stock_obj = Stock(mock_http)

    # Ascending by amount: "1" (20) should come before "2" (100)
    ordered_asc = stock_obj.get_ordered_stock_list("amount", descending=False)
    assert list(ordered_asc.keys()) == ["1", "2"]
    assert "3" not in ordered_asc

    # Descending by amount: "2" (100) before "1" (20)
    ordered_desc = stock_obj.get_ordered_stock_list("amount", descending=True)
    assert list(ordered_desc.keys()) == ["2", "1"]


def test_stock_lowest_entry(mock_http, sample_products_js_content):
    mock_http.get_all_product_informations.return_value = sample_products_js_content
    mock_http.read_storage_from_server.return_value = {"1": 80, "2": 15}

    stock_obj = Stock(mock_http)
    assert stock_obj.get_lowest_stock_entry() == "2"

    # When all amounts are 0
    mock_http.read_storage_from_server.return_value = {}
    stock_obj.update_number_in_stock()
    assert stock_obj.get_lowest_stock_entry() == -1

