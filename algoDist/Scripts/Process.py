import random
from time import sleep
from typing import Callable
from pyeventbus3.pyeventbus3 import *
from Message import Message, BroadcastMessage, MessageTo, Token, TokenState, SyncingMessage
from Com import Com  # Import de la classe Com

def mod(x: int, y: int) -> int:
    return ((x % y) + y) % y

class Process(Thread):
    nbProcessCreated = 0

    def __init__(self, name: str, nbProcess: int, verbose: int, mailboxes):
        Thread.__init__(self)
        self.nbProcess = nbProcess
        self.myId = Process.nbProcessCreated
        Process.nbProcessCreated += 1
        self.name = name
        self.alive = True
        self.horloge = 0
        self.verbose = verbose
        self.token_state = TokenState.Null
        self.nbSync = 0
        self.isSyncing = False

        # Instancier la classe Com pour gérer la communication
        self.communicator = Com(self.myId, nbProcess, mailboxes)

        PyBus.Instance().register(self, self)
        self.start()

    def run(self):
        while self.nbProcess != Process.nbProcessCreated:
            pass
        if self.myId == 0:
            self.releaseToken()
        self.synchronize()
        loop = 0
        while self.alive:
            self.printer(2, [self.name, "Itération:", loop, "; Horloge locale:", self.horloge])
            sleep(1)

            # Exemples de communication
            if self.name == "P1":
                self.communicator.sendTo("Message de P1: Salut P2!", 1)  # Utilisation de Com pour sendTo
                self.doCriticalAction(self.criticalActionWarning, ["Critical warning"])
            if self.name == "P2":
                self.communicator.broadcast("Diffusion de P2: Bonjour à tous!")  # Utilisation de Com pour broadcast
            if self.name == "P3":
                receiver = random.randint(0, self.nbProcess - 1)
                self.communicator.sendTo(f"Spam de P3 à P{receiver}: Comment ça va ?", receiver)
            loop += 1
        sleep(1)
        self.printer(2, [self.name, "arrêté"])

    def stop(self):
        self.alive = False
        self.join()

    # Remplacement des méthodes d'envoi et réception par les méthodes de Com
    def receiveMessage(self):
        message = self.communicator.receive()  # Utilisation de Com pour recevoir des messages
        if message is not None:
            self.printer(1, [self.name, "reçu:", message])

    def releaseToken(self):
        self.printer(8, [self.myId, "libère le jeton à", mod(self.myId + 1, Process.nbProcessCreated)])
        if self.token_state == TokenState.SC:
            self.token_state = TokenState.Release
        token = Token()
        token.from_process = self.myId
        token.to_process = mod(self.myId + 1, Process.nbProcessCreated)
        token.nbSync = self.nbSync
        self.communicator.sendTo(token, token.to_process)  # Utilisation de Com pour envoyer un Token
        self.token_state = TokenState.Null

    def requestToken(self):
        self.token_state = TokenState.Requested
        self.printer(4, [self.name, "en attente du jeton"])
        while self.token_state == TokenState.Requested:
            if not self.alive:
                return
        self.token_state = TokenState.SC
        self.printer(4, [self.name, "a reçu le jeton demandé"])

    def doCriticalAction(self, funcToCall: Callable, args: list):
        """
        L'action critique nécessite de demander le jeton, d'exécuter l'action, puis de le libérer.
        """
        self.requestToken()
        if self.alive:
            funcToCall(*args)
            self.releaseToken()

    def criticalActionWarning(self, msg: str):
        print(f"ACTION CRITIQUE, LE JETON EST UTILISÉ PAR {self.name}; MESSAGE: {msg}")

    def synchronize(self):
        self.isSyncing = True
        self.printer(2, [self.myId, "est en cours de synchronisation"])
        while self.isSyncing:
            if not self.alive:
                return
        while self.nbSync != 0:
            if not self.alive:
                return
        self.printer(2, [self.myId, "synchronisé"])

    def printer(self, verbosityThreshold: int, msgArgs: list):
        if self.verbose & verbosityThreshold > 0:
            print(*([time.time_ns(), ":"] + msgArgs))
