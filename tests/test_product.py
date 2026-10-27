import pytest
from pydantic import ValidationError

from product import Product


def test_product_is_plant():
    plant = Product(
        id=1,
        cat="v",
        name="Salat",
        lvl=1,
    )
    assert plant.is_plant() is True
    assert plant.is_decoration() is False


def test_product_is_decoration():
    deco = Product(
        id=2,
        cat="d",
        name="Zwerg",
        lvl=1,
    )
    assert deco.is_decoration() is True
    assert deco.is_plant() is False


def test_product_other_category():
    prod = Product(
        id=3,
        cat="z",
        name="Spezial",
        lvl=1,
    )
    assert prod.is_plant() is False
    assert prod.is_decoration() is False


def test_product_attributes_and_defaults():
    prod = Product(
        id=1,
        cat="v",
        name="Möhre",
        lvl=2,
        sx=1,
        sy=2,
        crop=2,
        is_plantable=True,
        time=1800,
        price_npc=0.32,
    )
    assert prod.id == 1
    assert prod.cat == "v"
    assert prod.name == "Möhre"
    assert prod.lvl == 2
    assert prod.sx == 1
    assert prod.sy == 2
    assert prod.crop == 2
    assert prod.is_plantable is True
    assert prod.time == 1800
    assert prod.price_npc == 0.32


def test_product_price_npc_assignment():
    prod = Product(
        id=1,
        cat="v",
        name="Salat",
        lvl=1,
    )
    assert prod.price_npc is None
    prod.price_npc = 1.5
    assert prod.price_npc == 1.5


def test_product_frozen_fields():
    prod = Product(
        id=1,
        cat="v",
        name="Salat",
        lvl=1,
    )
    with pytest.raises(ValidationError):
        prod.name = "Neuer Name"

    with pytest.raises(ValidationError):
        prod.lvl = 5


def test_product_validation_errors():
    # missing required fields: cat, name, lvl
    with pytest.raises(ValidationError):
        Product(id=1)

    # invalid types
    with pytest.raises(ValidationError):
        Product(id="abc", cat="v", name="Salat", lvl=1)

    with pytest.raises(ValidationError):
        Product(id=1, cat="v", name="Salat", lvl="eins")
