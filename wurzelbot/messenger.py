import io
import logging
import re
import xml.etree.ElementTree as eTree
from enum import IntEnum, StrEnum

import http_connection
import message


class MessageState(IntEnum):
    UNKNOWN = 1
    SENT_NO_ERR = 2
    SENT_ERR_NO_RECIPIENT = 4
    SENT_ERR_NO_SUBJECT = 8
    SENT_ERR_NO_TEXT = 16
    SENT_ERR_BLOCKED = 32
    SENT_ERR_RECIPIENT_DOESNT_EXIST = 64


class Folder(StrEnum):
    INBOX = "inbox"
    SYSTEM = "system"


class Messenger:
    def __init__(self, http_connection: http_connection.HTTPConnection):
        self.__http_connection = http_connection
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__sent = []

    def __get_new_message_id(self):
        """ "
        Requests a new message with the HTTP Connection and determines the ID for sending later.
        """

        result = self.__http_connection.execute_message_command("new.php")
        identifier = self.__get_message_id_from_new_message_result(result)
        return identifier

    def clear_sent_list(self):
        """
        Deletes the list of sent messages.
        """
        self.__sent = []

    def get_summary_of_message_delivery_states(self):
        """
        Returns a summary of the status of all sent messages.
        """
        number_of_all_sent_messages = len(self.__sent)
        number_of_successful_messages = 0
        number_of_failed_messages = 0
        number_of_unknown_messages = 0

        error_mask = (
            MessageState.SENT_ERR_BLOCKED
            | MessageState.SENT_ERR_NO_RECIPIENT
            | MessageState.SENT_ERR_NO_SUBJECT
            | MessageState.SENT_ERR_NO_TEXT
            | MessageState.SENT_ERR_RECIPIENT_DOESNT_EXIST
        )

        for msg in self.__sent:
            if msg.state & MessageState.SENT_NO_ERR != 0:
                number_of_successful_messages += 1

            elif msg.state & MessageState.UNKNOWN != 0:
                number_of_unknown_messages += 1

            elif msg.state & error_mask != 0:
                number_of_failed_messages += 1

        summary = {
            "sent": number_of_all_sent_messages,
            "fail": number_of_failed_messages,
            "success": number_of_successful_messages,
            "unknown": number_of_unknown_messages,
        }

        return summary

    def write_message(self, recipients, subject, body):
        """
        Sends a message and adds it to the list of sent messages.
        """
        if not isinstance(recipients, list):
            raise MessengerError("")

        number_recipients = len(recipients)
        counter = 0
        for recipient in recipients:
            try:
                new_message_id = self.__get_new_message_id()
                new_message = message.Message(
                    id=new_message_id, recipient=recipient, subject=subject, body=body
                )
                result_of_sent_message = self.__http_connection.execute_message_command(
                    "new.php", new_message
                )
                message_delivery_state = get_message_delivery_state(
                    result_of_sent_message
                )
                new_message.delivery_state = message_delivery_state
                self.__sent.append(new_message)
            except:
                self.__logger.exception(f"Exception {recipient }")
                raise
            counter += 1
            self.__logger.debug(f"{counter} von {number_recipients}")

    def read_message(self, folder: Folder):
        # Parses messages from inbox to python objects
        # and level up messages can so be read from wurzelbot
        content = self.__http_connection.execute_message_command(
            "list.php?folder={folder.value}"
        )
        content = content.decode("UTF-8")
        html = bytearray(content, encoding="UTF-8")
        self.__logger.info(parse_inbox_from_html(html))


def parse_inbox_from_html(html: str):
    # ElementTree needs a file to parse.
    # With BytesIO a file is created in memory, not on disk.
    html_file = io.BytesIO(html)

    html_tree = eTree.parse(html_file)
    root = html_tree.getroot()
    table = root.find("./body/table")
    return table


def blocked_from_message_recipient(result):
    """
    Checks if the receiver has blocked the reception of messages from the sender.
    """
    res = re.search(r"Der Empfänger hat dich auf die Blockliste gesetzt.", result)
    if res is not None:
        return True
    return False


def was_delivery_successful(result):
    """
    Checks if the message was sent successfully.
    """
    res = re.search(r"Deine Nachricht wurde an.*verschickt.", result)
    if res is not None:
        return True
    return False


def did_the_message_had_a_text(result):
    """
    Checks if the message had a text.
    """
    res = re.search(r"Es wurde keine Nachricht eingegeben.", result)
    if res is not None:
        return False
    return True


def did_the_message_had_a_recipient(result):
    """
    Checks if the message had a recipient.
    """
    res = re.search(r"Es wurde kein Empfänger angegeben.", result)
    if res is not None:
        return False
    return True


def did_the_message_recipient_exist(result):
    """
    Checks if the recipient of the message was present.
    """
    res = re.search(r"Der Empfänger existiert nicht.", result)
    if res is not None:
        return False
    return True


def did_the_message_had_a_subject(result):
    """
    Checks if the message had a subject.
    """
    res = re.search(r"Es wurde kein Betreff angegeben.", result)
    if res is not None:
        return False
    return True


def get_message_delivery_state(result):
    """
    Returns the status of the sent message.
    """
    state = 0
    if was_delivery_successful(result) is True:
        state |= MessageState.SENT_NO_ERR
    else:
        if did_the_message_recipient_exist(result) is False:
            state |= MessageState.SENT_ERR_RECIPIENT_DOESNT_EXIST

        if did_the_message_had_a_subject(result) is False:
            state |= MessageState.SENT_ERR_NO_SUBJECT

        if did_the_message_had_a_text(result) is False:
            state |= MessageState.SENT_ERR_NO_TEXT

        if did_the_message_had_a_recipient(result) is False:
            state |= MessageState.SENT_ERR_NO_RECIPIENT

        if blocked_from_message_recipient(result) is True:
            state |= MessageState.SENT_ERR_BLOCKED

    if state == 0:
        state = state or MessageState.UNKNOWN

    return state


class MessengerError(Exception):
    def __init__(self, value):
        super().__init__(value)
        self.value = value

    def __str__(self):
        return repr(self.value)
