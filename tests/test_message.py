import pytest
from message import Message
from pydantic import ValidationError


def test_message_creation_and_attributes():
    msg = Message(
        id=123,
        recipient="GartenFreund",
        subject="Tausch",
        body="Hallo, ich möchte tauschen.",
        delivery_state="SENT_NO_ERR",
        sender="WurzelKönig",
    )
    assert msg.id == 123
    assert msg.recipient == "GartenFreund"
    assert msg.subject == "Tausch"
    assert msg.body == "Hallo, ich möchte tauschen."
    assert msg.delivery_state == "SENT_NO_ERR"
    assert msg.sender == "WurzelKönig"


def test_message_defaults():
    msg = Message(
        id=1,
        recipient="User1",
        subject="Subj",
        body="Content",
    )
    assert msg.delivery_state is None
    assert msg.sender is None


def test_message_validation_error():
    # id must be PositiveInt
    with pytest.raises(ValidationError):
        Message(id=0, recipient="U1", subject="S", body="B")

    with pytest.raises(ValidationError):
        Message(id=-5, recipient="U1", subject="S", body="B")

    # missing required fields
    with pytest.raises(ValidationError):
        Message(id=1, recipient="U1")
