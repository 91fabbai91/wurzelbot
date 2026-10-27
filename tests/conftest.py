import json
import pytest
from unittest.mock import MagicMock
from product import Product
from login_data import LoginData


@pytest.fixture
def mock_http():
    mock = MagicMock()
    mock.user_id = 12345
    return mock


@pytest.fixture
def sample_login_data():
    return LoginData(server=1, username="testuser", password="secretpassword")


@pytest.fixture
def sample_product():
    return Product(
        id=1,
        cat="v",
        sx=1,
        sy=1,
        name="Salat",
        lvl=1,
        crop=1,
        is_plantable=True,
        time=900,
        price_npc=0.16,
    )


@pytest.fixture
def sample_products_raw_data():
    return {
        "1": {
            "name": "Salat",
            "category": "v",
            "plantable": True,
            "sx": 1,
            "sy": 1,
            "time": 900,
            "crop": 1,
            "level": 1,
        },
        "2": {
            "name": "Möhre",
            "category": "v",
            "plantable": True,
            "sx": 1,
            "sy": 1,
            "time": 1200,
            "crop": 1,
            "level": 1,
        },
        "3": {
            "name": "Zwerg",
            "category": "d",
            "plantable": False,
            "level": 2,
        },
        "999": {
            "name": "Testprodukt",
            "category": "v",
            "plantable": False,
            "level": 1,
        },
    }


@pytest.fixture
def sample_products_js_content(sample_products_raw_data):
    return f"data_products = {json.dumps(sample_products_raw_data)};var other = 1;"


@pytest.fixture
def sample_npc_prices_html():
    return """
    <html>
        <body>
            <div id="content">
                <table>
                    <tr><th>Produkt</th><th>NPC-Preis</th></tr>
                    <tr><td>Salat</td><td>0,16 wT</td></tr>
                    <tr><td>Möhre</td><td>0,32 wT</td></tr>
                    <tr><td>Zwerg</td><td>-</td></tr>
                </table>
            </div>
        </body>
    </html>
    """


@pytest.fixture
def sample_notes_html():
    return """
    <html>
        <body>
            <form>
                <div>
                    <textarea id="notiztext">
minStock: 25
minStock(Salat): 100
minStock(Möhre): 50
                    </textarea>
                </div>
            </form>
        </body>
    </html>
    """


@pytest.fixture
def sample_garden_json():
    # 204 fields in garden (17 x 12)
    garden_fields = {}
    for i in range(1, 205):
        garden_fields[str(i)] = [0, 0, 0, 0, 0, 0, 0, 0, 0, "1x1"]
    
    # field 1 has plant 1
    garden_fields["1"] = [1, 1, 0, 0, 0, 0, 0, 0, 0, "1x1"]
    # field 2 is weed (41)
    garden_fields["2"] = [41, 0, 0, 0, 0, 0, 0, 0, 0, "1x1"]
    # field 3 is stone (43)
    garden_fields["3"] = [43, 0, 0, 0, 0, 0, 0, 0, 0, "1x1"]

    water_data = [[i, 0] for i in range(1, 205)]
    grow_data = [
        [1, 1, 0, 1600000000, 1, 1],
    ]

    return {
        "garden": garden_fields,
        "water": water_data,
        "grow": grow_data,
    }


@pytest.fixture
def sample_user_data_dict():
    return {
        "levelnr": 15,
        "bar_unformat": 1234.56,
        "coins": 42,
        "level": "Maulwurfjäger",
        "points": 500000,
        "mail": 1,
        "contracts": 2,
        "g_tag": "tag1",
        "time": 1600000000,
    }
