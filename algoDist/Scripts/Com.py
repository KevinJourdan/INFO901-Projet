import threading
import queue
import time
from threading import Semaphore

class Com:
    def __init__(self, process_id, total_processes):
        self.process_id = process_id  # ID unique du processus
        self.total_processes = total_processes  # Nombre total de processus
        self.mailboxes = [queue.Queue() for _ in range(total_processes)]  # Boîtes aux lettres pour chaque processus
        self.lamport_clock = 0  # Horloge de Lamport
        self.clock_semaphore = Semaphore(1)  # Sémaphore pour protéger l'horloge
        self.lock = threading.Lock()  # Pour la gestion des threads

    def inc_clock(self):
        """Méthode pour incrémenter l'horloge de Lamport"""
        with self.clock_semaphore:
            self.lamport_clock += 1
            print(f"[Process {self.process_id}] Horloge Lamport incrémentée: {self.lamport_clock}")

    def get_clock(self):
        """Retourne l'horloge Lamport actuelle"""
        with self.clock_semaphore:
            return self.lamport_clock

    def broadcast(self, message):
        """Envoie un message à tous les processus"""
        self.inc_clock()  # Incrémente l'horloge avant d'envoyer
        for i in range(self.total_processes):
            if i != self.process_id:  # Ne pas s'envoyer à soi-même
                self.mailboxes[i].put((message, self.get_clock()))  # Envoie le message avec l'horloge actuelle
                print(f"[Process {self.process_id}] Message broadcasté à Process {i}: {message}")

    def sendTo(self, message, dest):
        """Envoie un message à un processus spécifique"""
        self.inc_clock()  # Incrémente l'horloge avant d'envoyer
        self.mailboxes[dest].put((message, self.get_clock()))  # Envoie le message avec l'horloge actuelle
        print(f"[Process {self.process_id}] Message envoyé à Process {dest}: {message}")

    def receive(self):
        """Récupère un message dans la boîte aux lettres du processus"""
        if not self.mailboxes[self.process_id].empty():
            message, timestamp = self.mailboxes[self.process_id].get()
            with self.clock_semaphore:
                self.lamport_clock = max(self.lamport_clock, timestamp) + 1
            print(f"[Process {self.process_id}] Message reçu: {message} avec timestamp: {timestamp}")
            return message
        else:
            print(f"[Process {self.process_id}] Pas de message disponible")
            return None
