import random
from time import sleep
from threading import Thread
from pyeventbus3.pyeventbus3 import *
from Com import Com

class Process(Thread):
    nbProcessCreated = 0

    def __init__(self, name: str, nbProcess: int, verbose: int, mailboxes):
        Thread.__init__(self)
        self.nbProcess = nbProcess
        self.myId = Process.nbProcessCreated
        Process.nbProcessCreated += 1
        self.name = name
        self.alive = True
        self.verbose = verbose

        # Instancier la classe Com pour gérer la communication
        self.communicator = Com(self.myId, nbProcess, mailboxes)  # Plus de request_queue ici

        PyBus.Instance().register(self, self)
        self.start()

    def run(self):
        while self.nbProcess != Process.nbProcessCreated:
            pass  # Attendre que tous les processus soient créés

        if self.myId == 0:
            self.communicator.releaseSC()  # Release token si c'est le premier processus
        
        loop = 0
        while self.alive:
            self.printer(2, [self.name, "Itération:", loop])
            sleep(1)  # Attendre un moment entre chaque itération
            
            # Gestion des sections critiques
            self.doCriticalAction(self.criticalActionWarning, ["Une Action critique est réalisée par", self.name])
            
            # Exemples de communication
            if self.name == "P1":
                self.communicator.sendTo("Message de P1: Salut P2!", 1)
            elif self.name == "P2":
                self.communicator.broadcast("Diffusion de P2: Bonjour à tous!")
            elif self.name == "P3":
                receiver = random.randint(0, self.nbProcess - 1)
                self.communicator.sendTo(f"Spam de P3 à P{receiver}: Comment ça va ?", receiver)
            
            loop += 1
        sleep(1)
        self.printer(2, [self.name, "arrêté"])

    def stop(self):
        self.alive = False
        self.join()

    def receiveMessage(self):
        message = self.communicator.receive()
        if message is not None:
            self.printer(1, [self.name, "reçu:", message])

    def doCriticalAction(self, funcToCall, args):
        """
        Appelle une action critique et passe les bons arguments.
        """
        self.communicator.requestSC()
        if isinstance(args, list) and len(args) == 2:
            message = f"{args[0]} {args[1]}"
            funcToCall(message)
        else:
            funcToCall(args)
        self.communicator.releaseSC()

    def criticalActionWarning(self, message):
        print(message)

    def printer(self, verbosityThreshold: int, msgArgs: list):
        if self.verbose & verbosityThreshold > 0:
            print(*([time.time_ns(), ":"] + msgArgs))
