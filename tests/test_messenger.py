import pytest
from unittest.mock import MagicMock
from messenger import (
    Messenger,
    MessageState,
    Folder,
    MessengerError,
    blocked_from_message_recipient,
    was_delivery_successful,
    did_the_message_had_a_text,
    did_the_message_had_a_recipient,
    did_the_message_recipient_exist,
    did_the_message_had_a_subject,
    get_message_delivery_state,
    parse_inbox_from_html,
)


def test_helper_patterns():
    # blocked
    assert blocked_from_message_recipient("Der Empfänger hat dich auf die Blockliste gesetzt.") is True
    assert blocked_from_message_recipient("Alles ok") is False

    # success
    assert was_delivery_successful("Deine Nachricht wurde an Max verschickt.") is True
    assert was_delivery_successful("Fehler") is False

    # text
    assert did_the_message_had_a_text("Es wurde keine Nachricht eingegeben.") is False
    assert did_the_message_had_a_text("Text vorhanden") is True

    # recipient
    assert did_the_message_had_a_recipient("Es wurde kein Empfänger angegeben.") is False
    assert did_the_message_had_a_recipient("Empfänger angegeben") is True

    # recipient exists
    assert did_the_message_recipient_exist("Der Empfänger existiert nicht.") is False
    assert did_the_message_recipient_exist("Empfänger existiert") is True

    # subject
    assert did_the_message_had_a_subject("Es wurde kein Betreff angegeben.") is False
    assert did_the_message_had_a_subject("Betreff ist da") is True


def test_get_message_delivery_state():
    # Success
    state_ok = get_message_delivery_state("Deine Nachricht wurde an Alex verschickt.")
    assert state_ok == MessageState.SENT_NO_ERR

    # Unknown
    state_unknown = get_message_delivery_state("Unbekannte Antwort")
    assert state_unknown == MessageState.UNKNOWN

    # Multiple errors combined
    err_text = "Der Empfänger existiert nicht. Es wurde kein Betreff angegeben."
    state_err = get_message_delivery_state(err_text)
    assert (state_err & MessageState.SENT_ERR_RECIPIENT_DOESNT_EXIST) != 0
    assert (state_err & MessageState.SENT_ERR_NO_SUBJECT) != 0


def test_parse_inbox_from_html():
    html_inbox = "<html><body><table><tr><td>Nachricht 1</td></tr></table></body></html>"
    table = parse_inbox_from_html(html_inbox)
    assert table is not None
    assert len(table) == 1


def test_messenger_write_message_invalid_recipients(mock_http):
    messenger = Messenger(mock_http)
    with pytest.raises(MessengerError):
        messenger.write_message("not_a_list", "Subject", "Body")


def test_messenger_write_message_and_summary(mock_http):
    messenger = Messenger(mock_http)

    # 1. new.php returns HTML with message id input
    # 2. send returns success text
    mock_http.execute_message_command.side_effect = [
        '<input type="hidden" name="hpc" value="456" id="hpc">',
        "Deine Nachricht wurde an Max verschickt.",
    ]

    messenger.write_message(["Max"], "Hallo", "Wie gehts?")

    summary = messenger.get_summary_of_message_delivery_states()
    assert summary["sent"] == 1
    assert summary["success"] == 1
    assert summary["fail"] == 0
    assert summary["unknown"] == 0

    messenger.clear_sent_list()
    assert messenger.get_summary_of_message_delivery_states()["sent"] == 0


def test_messenger_read_message(mock_http):
    messenger = Messenger(mock_http)
    mock_http.execute_message_command.return_value = (
        b"<html><body><table><tr><td>Item</td></tr></table></body></html>"
    )
    # Should not raise exception
    messenger.read_message(Folder.INBOX)


def test_messenger_error_str():
    err = MessengerError("Delivery failed")
    assert str(err) == "'Delivery failed'"

