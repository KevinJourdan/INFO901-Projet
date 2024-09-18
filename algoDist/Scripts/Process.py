import random
from time import sleep
from typing import Callable

from pyeventbus3.pyeventbus3 import *

from Message import Message, BroadcastMessage, MessageTo, Token, TokenState, SyncingMessage


def mod(x: int, y: int) -> int:
    return ((x % y) + y) % y


class Process(Thread):
    nbProcessCreated = 0

    def __init__(self, name: str, nbProcess: int, verbose: int):
        Thread.__init__(self)

        self.nbProcess = nbProcess
        self.myId = Process.nbProcessCreated
        Process.nbProcessCreated += 1
        self.name = name

        PyBus.Instance().register(self, self)

        self.alive = True
        self.horloge = 0
        self.verbose = verbose
        self.token_state = TokenState.Null
        self.nbSync = 0
        self.isSyncing = False
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

            if self.name == "P1":
                self.sendTo("P2", "Message de P1: Salut P2!")
                self.doCriticalAction(self.criticalActionWarning, ["Critical warning"])
            if self.name == "P2":
                self.broadcast("Diffusion de P2: Bonjour à tous!")
            if self.name == "P3":
                receiver = str(random.randint(0, self.nbProcess - 1))
                self.sendTo("P" + receiver, "Spam de P3 à P" + receiver + ": Comment ça va ?")
            loop += 1
        sleep(1)
        self.printer(2, [self.name, "arrêté"])

    def stop(self):
        self.alive = False
        self.join()

    def sendMessage(self, message: Message, verbosityThreshold=1):
        self.horloge += 1
        message.horloge = self.horloge
        self.printer(verbosityThreshold, [self.name, "envoie:", message.getObject()])
        PyBus.Instance().post(message)

    def receiveMessage(self, message: Message, verbosityThreshold=1):
        self.printer(verbosityThreshold, [self.name, "Traite l'événement:", message.getObject()])
        self.horloge = max(self.horloge, message.horloge) + 1

    def sendAll(self, obj: any):
        self.sendMessage(Message(obj))

    @subscribe(threadMode=Mode.PARALLEL, onEvent=Message)
    def process(self, event: Message):
        self.receiveMessage(event)

    def broadcast(self, obj: any):
        self.sendMessage(BroadcastMessage(obj, self.name))

    @subscribe(threadMode=Mode.PARALLEL, onEvent=BroadcastMessage)
    def onBroadcast(self, event: BroadcastMessage):
        if event.from_process != self.name:
            self.receiveMessage(event)

    def sendTo(self, dest: str, obj: any):
        self.sendMessage(MessageTo(obj, self.name, dest))

    @subscribe(threadMode=Mode.PARALLEL, onEvent=MessageTo)
    def onReceive(self, event: MessageTo):
        if event.to_process == self.name:
            self.receiveMessage(event)

    def releaseToken(self):
        self.printer(8, [self.myId, "libère le jeton à", mod(self.myId + 1, Process.nbProcessCreated)])
        if self.token_state == TokenState.SC:
            self.token_state = TokenState.Release
        token = Token()
        token.from_process = self.myId
        token.to_process = mod(self.myId + 1, Process.nbProcessCreated)
        token.nbSync = self.nbSync
        self.sendMessage(token, verbosityThreshold=8)
        self.token_state = TokenState.Null

    def requestToken(self):
        self.token_state = TokenState.Requested
        self.printer(4, [self.name, "en attente du jeton"])
        while self.token_state == TokenState.Requested:
            if not self.alive:
                return
        self.token_state = TokenState.SC
        self.printer(4, [self.name, "a reçu le jeton demandé"])

    @subscribe(threadMode=Mode.PARALLEL, onEvent=Token)
    def onToken(self, event: Token):
        """
        Le jeton circule continuellement. Il s'arrête si un processus en a besoin pour accéder à une section critique.
        """
        if event.to_process == self.myId:
            self.receiveMessage(event, verbosityThreshold=8)
            if not self.alive:
                return
            if self.token_state == TokenState.Requested:
                self.token_state = TokenState.SC
                return
            if self.isSyncing:
                self.isSyncing = False
                self.nbSync = mod(event.nbSync + 1, Process.nbProcessCreated)
                if self.nbSync == 0:
                    self.sendMessage(SyncingMessage(self.myId))
            self.releaseToken()

    def doCriticalAction(self, funcToCall: Callable, args: list):
        """
        L'action critique nécessite de demander le jeton, d'exécuter l'action, puis de le libérer.
        """
        self.requestToken()
        if self.alive:
            funcToCall(*args)
            self.releaseToken()

    def criticalActionWarning(self, msg: str):
        """
        Message critique : peut être remplacé par toute action sur une ressource partagée.
        """
        print("ACTION CRITIQUE, LE JETON EST UTILISÉ PAR", self.name, "; MESSAGE:", msg)

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

    @subscribe(threadMode=Mode.PARALLEL, onEvent=SyncingMessage)
    def onSyncing(self, event: SyncingMessage):
        if event.from_process != self.myId:
            self.receiveMessage(event)
            self.nbSync = 0

    def printer(self, verbosityThreshold: int, msgArgs: list):
        if self.verbose & verbosityThreshold > 0:
            print(*([time.time_ns(), ":"] + msgArgs))
