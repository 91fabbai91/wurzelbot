import io
import logging
import re
import xml.etree.ElementTree as eTree

import http_connection
import message

# Message States
MSG_STATE_UNKNOWN = 1
MSG_STATE_SENT_NO_ERR = 2
MSG_STATE_SENT_ERR_NO_RECIPIENT = 4
MSG_STATE_SENT_ERR_NO_SUBJECT = 8
MSG_STATE_SENT_ERR_NO_TEXT = 16
MSG_STATE_SENT_ERR_BLOCKED = 32
MSG_STATE_SENT_ERR_RECIPIENT_DOESNT_EXIST = 64


class Messenger(object):
    def __init__(self, http_connection: http_connection.HTTPConnection):
        self.__http_connection = http_connection
        self.__logger = logging.getLogger()
        self.__sent = []

    def __get_message_id_from_new_message_result(self, result):
        """
        Extracts from content the ID of the newly created message
        """

        res = re.search(r'name="hpc" value="(.*)" id="hpc"', result)
        if res is None:
            raise MessengerError("")
        else:
            return res.group(1)

    def __was_delivery_successful(self, result):
        """
        Checks if the message was sent successfully.
        """
        res = re.search(r"Deine Nachricht wurde an.*verschickt.", result)
        if res is not None:
            return True
        else:
            return False

    def __did_the_message_recipient_exist(self, result):
        """
        Checks if the recipient of the message was present.
        """
        res = re.search(r"Der Empfänger existiert nicht.", result)
        if res is not None:
            return False
        else:
            return True

    def __did_the_message_had_a_subject(self, result):
        """
        Checks if the message had a subject.
        """
        res = re.search(r"Es wurde kein Betreff angegeben.", result)
        if res is not None:
            return False
        else:
            return True

    def __did_the_message_had_a_text(self, result):
        """
        Checks if the message had a text.
        """
        res = re.search(r"Es wurde keine Nachricht eingegeben.", result)
        if res is not None:
            return False
        else:
            return True

    def __did_the_message_had_a_recipient(self, result):
        """
        Checks if the message had a recipient.
        """
        res = re.search(r"Es wurde kein Empfänger angegeben.", result)
        if res is not None:
            return False
        else:
            return True

    def __blocked_from_message_recipient(self, result):
        """
        Checks if the receiver has blocked the reception of messages from the sender.
        """
        res = re.search(r"Der Empfänger hat dich auf die Blockliste gesetzt.", result)
        if res is not None:
            return True
        else:
            return False

    def __get_message_delivery_state(self, result):
        """
        Returns the status of the sent message.
        """
        state = 0
        if self.__was_delivery_successful(result) is True:
            state |= MSG_STATE_SENT_NO_ERR
        else:
            if self.__did_the_message_recipient_exist(result) is False:
                state |= MSG_STATE_SENT_ERR_RECIPIENT_DOESNT_EXIST

            if self.__did_the_message_had_a_subject(result) is False:
                state |= MSG_STATE_SENT_ERR_NO_SUBJECT

            if self.__did_the_message_had_a_text(result) is False:
                state |= MSG_STATE_SENT_ERR_NO_TEXT

            if self.__did_the_message_had_a_recipient(result) is False:
                state |= MSG_STATE_SENT_ERR_NO_RECIPIENT

            if self.__blocked_from_message_recipient(result) is True:
                state |= MSG_STATE_SENT_ERR_BLOCKED

        if state == 0:
            state = state or MSG_STATE_UNKNOWN

        return state

    def __get_new_message_id(self):
        """ "
        Requests a new message with the HTTP Connection and determines the ID for sending later.
        """

        try:
            result = self.__http_connection.execute_message_command("new.php")
            id = self.__get_message_id_from_new_message_result(result)
        except:
            raise
        else:
            return id

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

        errorMask = (
            MSG_STATE_SENT_ERR_BLOCKED
            | MSG_STATE_SENT_ERR_NO_RECIPIENT
            | MSG_STATE_SENT_ERR_NO_SUBJECT
            | MSG_STATE_SENT_ERR_NO_TEXT
            | MSG_STATE_SENT_ERR_RECIPIENT_DOESNT_EXIST
        )

        for msg in self.__sent:
            if msg.state & MSG_STATE_SENT_NO_ERR != 0:
                number_of_successful_messages += 1

            elif msg.state & MSG_STATE_UNKNOWN != 0:
                number_of_unknown_messages += 1

            elif msg.state & errorMask != 0:
                number_of_failedMessages += 1

        summary = {
            "sent": number_of_all_sent_messages,
            "fail": number_of_failedMessages,
            "success": number_of_successful_messages,
            "unknown": number_of_unknown_messages,
        }

        return summary

    def write_message(self, recipients, subject, body):
        """
        Sends a message and adds it to the list of sent messages.
        """
        if not type(recipients) is ListType:
            raise MessengerError("")

        n = len(recipients)
        i = 0
        for recipient in recipients:
            try:
                newMessageID = self.__get_new_message_id()
                new_message = message.Message(
                    id=newMessageID, recipient=recipient, subject=subject, body=body
                )
                result_of_sent_message = self.__http_connection.execute_message_command(
                    "new.php", new_message
                )
                message_delivery_state = self.__get_message_delivery_state(
                    result_of_sent_message
                )
                new_message.delivery_state = message_delivery_state
                self.__sent.append(new_message)
            except:
                self.__logger.exception("Exception " + recipient)
                raise
            else:
                i += 1
                self.__logger.debug(str(i) + " von " + str(n))

    # TODO: Write complete function
    def read_message(self):
        # Parses messages from inbox to python objects and level up messages can so be read from wurzelbot
        content = self.__http_connection.execute_message_command(
            "list.php?folder=inbox"
        )
        content = content.decode("UTF-8")
        html = bytearray(content, encoding="UTF-8")
        self.__parse_inbox_from_html(html)

    def __parse_inbox_from_html(self, html: str):
        # ElementTree needs a file to parse.
        # With BytesIO a file is created in memory, not on disk.
        html_file = io.BytesIO(html)

        html_tree = eTree.parse(html_file)
        root = html_tree.getroot()
        table = root.find("./body/table")
        print(table)


class MessengerError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
