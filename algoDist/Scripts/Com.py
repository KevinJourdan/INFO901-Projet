import threading
import queue
from threading import Semaphore
from time import sleep

class Com:
    def __init__(self, process_id, total_processes, mailboxes, request_queue):
        """
        Initialise le communicateur pour un processus donné avec un identifiant unique.
        Gère la communication entre les processus via les boîtes aux lettres partagées et protège l'horloge Lamport.
        """
        self.process_id = process_id
        self.total_processes = total_processes
        self.mailboxes = mailboxes
        self.lamport_clock = 0  # Horloge de Lamport initialisée à 0
        self.clock_semaphore = Semaphore(1)

        self.request_queue = request_queue
        self.token_semaphore = Semaphore(1)
        self.token_available = (process_id == 0)  # Le processus 0 démarre avec le jeton
        self.token_owner = 0  # Initialement, le processus 0 détient le jeton

        # Lancer un thread séparé pour gérer le jeton
        self.token_thread = threading.Thread(target=self.token_manager)
        self.token_thread.daemon = True
        self.token_thread.start()


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
        
    def token_manager(self):
        """
        Gère la distribution du jeton indépendamment de l'horloge Lamport.
        """
        while True:
            if self.token_available and not self.request_queue.empty():
                next_process = self.request_queue.get()
                if next_process != self.process_id:  # S'assurer que le jeton ne va pas au processus actuel
                    print(f"[Process {self.process_id}] envoie le jeton à Process {next_process}")
                    self.token_available = False
                    self.send_system_message("TOKEN", next_process)  # Envoi du jeton en tant que message système
                    self.token_owner = next_process
                else:
                    # En cas de condition inattendue, réinitialiser le jeton comme disponible
                    self.token_available = True
            sleep(0.1)  # Petite pause pour éviter une boucle trop gourmande

    def send_system_message(self, message, dest):
        """
        Envoie un message système (ne modifie pas l'horloge).
        """
        self.mailboxes[dest].put((message, None))  # Pas de timestamp pour les messages système
        print(f"[Process {self.process_id}] Message système envoyé à Process {dest}: {message}")

    def requestSC(self):
        """
        Demande d'accès à la section critique. Bloque jusqu'à ce que le processus obtienne le jeton.
        """
        print(f"[Process {self.process_id}] Demande d'accès à la section critique envoyée")
        
        with self.token_semaphore:
            # Vérifie si le processus est déjà dans la file d'attente
            if self.process_id not in list(self.request_queue.queue):  
                self.request_queue.put(self.process_id)
                print(f"[Process {self.process_id}] a été ajouté à la file d'attente (Taille actuelle de la file : {self.request_queue.qsize()})")
            else:
                print(f"[Process {self.process_id}] est déjà dans la file d'attente")

        # Bloque jusqu'à obtention du jeton
        while True:
            with self.token_semaphore:
                if self.token_owner == self.process_id and self.token_available:
                    print(f"[Process {self.process_id}] a reçu le jeton et entre dans la section critique")
                    self.token_available = False  # Le processus utilise le jeton
                    break
            sleep(0.1)

    def releaseSC(self):
        """
        Libère la section critique et passe le jeton au prochain processus.
        """
        with self.token_semaphore:
            if not self.request_queue.empty():
                next_process = self.request_queue.get()
                if next_process != self.process_id:  # S'assurer que le jeton ne va pas au processus actuel
                    print(f"[Process {self.process_id}] envoie le jeton à Process {next_process}")
                    self.token_owner = next_process
                    self.token_available = False  # Le jeton n'est plus disponible pour le moment
                    self.send_system_message("TOKEN", next_process)  # Envoi du jeton au prochain processus
                else:
                    print(f"[Process {self.process_id}] a reçu à nouveau le jeton mais n'a pas besoin de la section critique.")
                    self.token_available = True  # Le jeton est disponible pour le prochain cycle
            else:
                print(f"[Process {self.process_id}] a libéré la section critique, mais personne ne l'a demandé")
                self.token_available = True  # Le jeton est disponible pour le prochain cycle
