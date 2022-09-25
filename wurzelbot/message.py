class MessageBuilder(object):
    def __init__(self) -> None:
        self.__id = None
        self.__recipient = None
        self.__subject = None
        self.__body = None

    @property
    def id(self):
        return self.__id
    
    @id.setter
    def id(self, id):
        self.__id = id

    @property
    def recipient(self):
        return self.__recipient

    @recipient.setter
    def recipient(self, recipient):
        self.__recipient == recipient

    @property
    def subject(self):
        return self.__subject
    
    @subject.setter
    def subject(self, subject):
        self.__subject = subject
    
    @property
    def body(self):
        return self.__body

    @body.setter
    def body(self, body):
        self.__body = body

class Message(object):
    def __init__(self, builder: MessageBuilder) -> None:
        self.__id = builder.id
        self.__recipient = builder.recipient
        self.__subject = builder.subject
        self.__body = builder.body
        self.__delivery_state = None
        self.__sender = None

    @property
    def id(self):
        return self.__id

    @property
    def recipient(self):
        return self.__recipient

    @property
    def subject(self):
        return self.__subject
    
    @property
    def body(self):
        return self.__body

    @property
    def delivery_state(self):
        return self.__delivery_state

    @delivery_state.setter
    def delivery_state(self, state):
        self.__delivery_state = state

    @property
    def sender(self):
        return self.__sender

    @sender.setter
    def sender(self, sender: str):
        self.__sender = sender

    