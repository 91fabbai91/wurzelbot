from product_information import ProductInformation, parse_npc_prices_from_html


def test_parse_npc_prices_from_html(sample_npc_prices_html):
    prices = parse_npc_prices_from_html(sample_npc_prices_html)
    assert prices["Salat"] == 0.16
    assert prices["Möhre"] == 0.32
    assert prices["Zwerg"] == float("inf")


def test_product_information_init_and_getters(
    mock_http, sample_products_js_content, sample_npc_prices_html
):
    mock_http.get_all_product_informations.return_value = sample_products_js_content
    mock_http.get_npc_prices.return_value = sample_npc_prices_html

    pi = ProductInformation(mock_http, "product_names.json")

    # Product 999 should be excluded
    all_ids = pi.get_list_of_all_product_ids()
    assert 999 not in all_ids
    assert set(all_ids) == {1, 2, 3}

    # get_product_by_id
    prod_1 = pi.get_product_by_id(1)
    assert prod_1 is not None
    assert prod_1.name == "Salat"
    assert prod_1.price_npc == 0.16
    assert prod_1.is_plant() is True

    prod_str = pi.get_product_by_id("2")
    assert prod_str is not None
    assert prod_str.name == "Möhre"
    assert prod_str.price_npc == 0.32

    assert pi.get_product_by_id(9999) is None

    # get_product_by_name
    prod_exact = pi.get_product_by_name("Salat")
    assert prod_exact.id == 1

    prod_case = pi.get_product_by_name("möhre")
    assert prod_case.id == 2

    # substring match
    prod_sub = pi.get_product_by_name("Zwer")
    assert prod_sub.id == 3

    assert pi.get_product_by_name("UnbekanntesDing") is None


def test_product_information_plural(
    mock_http, sample_products_js_content, sample_npc_prices_html
):
    mock_http.get_all_product_informations.return_value = sample_products_js_content
    mock_http.get_npc_prices.return_value = sample_npc_prices_html

    pi = ProductInformation(mock_http, "product_names.json")

    # In product_names.json, e.g. "Rosen" -> "Rose", or fallback
    assert pi.get_plural("Rosen") == "Rose"
    # Unknown word returns singular
    assert pi.get_plural("Salat") == "Salat"
    assert pi.get_plural("Phantasiepflanze") == "Phantasiepflanze"
