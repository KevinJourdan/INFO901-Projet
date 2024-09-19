import threading
import queue
from threading import Semaphore

class Com:
    def __init__(self, process_id, total_processes, mailboxes):
        """
        Initialise le communicateur pour un processus donné avec un identifiant unique.
        Gère la communication entre les processus via les boîtes aux lettres partagées et protège l'horloge Lamport.
        """
        self.process_id = process_id  # Identifiant unique du processus
        self.total_processes = total_processes  # Nombre total de processus
        self.mailboxes = mailboxes  # Boîtes aux lettres partagées pour la communication
        self.lamport_clock = 0  # Horloge de Lamport initialisée à 0
        self.clock_semaphore = Semaphore(1)  # Sémaphore pour protéger l'accès concurrent à l'horloge

    def inc_clock(self):
        """
        Incrémente l'horloge de Lamport en s'assurant qu'elle est protégée par un sémaphore.
        Cette méthode est utilisée avant chaque envoi de message.
        """
        with self.clock_semaphore:
            self.lamport_clock += 1
            print(f"[Process {self.process_id}] Horloge Lamport incrémentée: {self.lamport_clock}")

    def get_clock(self):
        """
        Retourne la valeur actuelle de l'horloge de Lamport.
        Cette méthode est protégée par un sémaphore pour éviter les accès concurrents.
        """
        with self.clock_semaphore:
            return self.lamport_clock

    def broadcast(self, message):
        """
        Envoie un message à tous les processus sauf à soi-même.
        Incrémente l'horloge de Lamport avant l'envoi et place le message dans les boîtes aux lettres des autres processus.
        """
        self.inc_clock()  # Incrémente l'horloge avant l'envoi
        for i in range(self.total_processes):
            if i != self.process_id:  # Ne pas s'envoyer à soi-même
                self.mailboxes[i].put((message, self.get_clock()))  # Ajoute le message dans la boîte aux lettres de chaque processus
                print(f"[Process {self.process_id}] Message broadcasté à Process {i}: {message}")

    def sendTo(self, message, dest):
        """
        Envoie un message à un processus spécifique (désigné par dest).
        Incrémente l'horloge de Lamport avant l'envoi et place le message dans la boîte aux lettres du destinataire.
        """
        self.inc_clock()  # Incrémente l'horloge avant l'envoi
        self.mailboxes[dest].put((message, self.get_clock()))  # Ajoute le message dans la boîte aux lettres du destinataire
        print(f"[Process {self.process_id}] Message envoyé à Process {dest}: {message}")

    def receive(self):
        """
        Récupère un message de la boîte aux lettres du processus.
        Met à jour l'horloge de Lamport en tenant compte du timestamp du message reçu.
        """
        if not self.mailboxes[self.process_id].empty():
            message, timestamp = self.mailboxes[self.process_id].get()  # Récupère le message et son horodatage
            with self.clock_semaphore:
                self.lamport_clock = max(self.lamport_clock, timestamp) + 1  # Met à jour l'horloge avec le timestamp reçu
            print(f"[Process {self.process_id}] Message reçu: {message} avec timestamp: {timestamp}")
            return message
        else:
            print(f"[Process {self.process_id}] Pas de message disponible")
            return None
