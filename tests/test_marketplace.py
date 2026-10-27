from unittest.mock import MagicMock
from lxml import html
from marketplace import Marketplace, get_amounts_and_prices_from_table


def test_get_amounts_and_prices_from_table():
    html_content = """
    <table>
        <tr><th>Menge</th><th>Produkt</th><th>Verkäufer</th><th>Preis</th></tr>
        <tr><td>100</td><td><span>Salat</span></td><td><span>Max</span></td><td>0,15 wT</td></tr>
        <tr><td>50</td><td><span>Salat</span></td><td><span>Anna</span></td><td>0,20 wT</td></tr>
        <tr><td>Zurück</td><td></td><td></td><td>Weiter</td></tr>
    </table>
    """
    table = html.fromstring(html_content)
    offers = get_amounts_and_prices_from_table(table)
    assert len(offers) == 2
    assert offers[0].product == "Salat"
    assert offers[0].seller == "Max"
    assert offers[0].amount == 100
    assert offers[0].price == 0.15

    assert offers[1].seller == "Anna"
    assert offers[1].price == 0.20


def test_marketplace_tradeable_products(mock_http):
    tradeable_html = """
    <a href="markt.php?order=p&v=1&filter=1">Salat</a>
    <a href="markt.php?order=p&v=2&filter=1">Möhre</a>
    """.encode("utf-8")
    mock_http.get_all_tradeable_products.return_value = tradeable_html

    mp = Marketplace(mock_http)
    products = mp.get_all_tradeable_products()
    assert products == [1, 2]


def test_marketplace_get_offers_and_cheapest(mock_http):
    tradeable_html = b'<a href="markt.php?order=p&v=1&filter=1">Salat</a>'
    market_page1 = """
    <html><body><div><table>
        <tr><th>Menge</th><th>Produkt</th><th>Verkäufer</th><th>Preis</th></tr>
        <tr><td>100</td><td><span>Salat</span></td><td><span>Max</span></td><td>0,25 wT</td></tr>
        <tr><td>Zurück</td><td></td><td></td><td>weiter</td></tr>
    </table></div></body></html>
    """
    market_page2 = """
    <html><body><div><table>
        <tr><th>Menge</th><th>Produkt</th><th>Verkäufer</th><th>Preis</th></tr>
        <tr><td>50</td><td><span>Salat</span></td><td><span>Anna</span></td><td>0,15 wT</td></tr>
        <tr><td>Zurück</td><td></td><td></td><td>Ende</td></tr>
    </table></div></body></html>
    """
    mock_http.get_all_tradeable_products.return_value = tradeable_html
    mock_http.execute_market_command.side_effect = [market_page1, market_page2]

    mp = Marketplace(mock_http)
    offers = mp.get_all_offers_of_product(1)
    # Page 2 overwrites or returns page 2 offers
    assert len(offers) == 1
    assert offers[0].seller == "Anna"


def test_marketplace_no_offers(mock_http):
    tradeable_html = b'<a href="markt.php?order=p&v=1&filter=1">Salat</a>'
    empty_page = """
    <html><body><div><table>
        <tr><th>Menge</th></tr>
        <tr><td>Keine Angebote</td></tr>
    </table></div></body></html>
    """
    mock_http.get_all_tradeable_products.return_value = tradeable_html
    mock_http.execute_market_command.return_value = empty_page

    mp = Marketplace(mock_http)
    cheapest = mp.get_cheapest_offer(1)
    assert cheapest == float("inf")


def test_marketplace_not_tradeable_product(mock_http):
    tradeable_html = b'<a href="markt.php?order=p&v=1&filter=1">Salat</a>'
    mock_http.get_all_tradeable_products.return_value = tradeable_html

    mp = Marketplace(mock_http)
    offers = mp.get_all_offers_of_product(99)
    assert offers == []
    assert mp.get_cheapest_offer(99) == float("inf")


def test_marketplace_sell_on_market(mock_http):
    mp = Marketplace(mock_http)
    mp.sell_on_market(item_id=1, price=0.20, number=50)
    mock_http.sell_on_market.assert_called_with(1, 0.20, 50)
