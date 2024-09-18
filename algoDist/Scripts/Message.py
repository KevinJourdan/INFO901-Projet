from enum import Enum


class Message:
    def __init__(self, obj: any):
        self.object = obj
        self.horloge = None

    def getObject(self: any):
        return self.object


class BroadcastMessage(Message):
    def __init__(self, obj: any, from_process: str):
        Message.__init__(self, obj)
        self.from_process = from_process


class MessageTo(Message):
    def __init__(self, obj: any, from_process: str, to_process: str):
        Message.__init__(self, obj)
        self.from_process = from_process
        self.to_process = to_process


class Token(Message):
    def __init__(self):
        Message.__init__(self, "TOKEN")
        self.from_process = None
        self.to_process = None
        self.nbSync = 0


class TokenState(Enum):
    """
    Null: pas de token et pas de demande de token
    Requested: demande de token en cours
    SC: processus en section critique
    Release: liberation du token en cours
    """
    Null = 1
    Requested = 2
    SC = 3
    Release = 4


class SyncingMessage(Message):
    def __init__(self, from_process: int):
        Message.__init__(self, "SYNCING")
        self.from_process = from_process