import threading
from threading import Semaphore
from time import sleep

class Com:
    def __init__(self, process_id, total_processes, mailboxes):
        self.process_id = process_id
        self.total_processes = total_processes
        self.mailboxes = mailboxes
        self.lamport_clock = 0
        self.clock_semaphore = Semaphore(1)

        # Le mutex pour gérer l'accès au jeton
        self.token_mutex = threading.Lock()
        self.token_available = (process_id == 0)  # Le processus 0 démarre avec le jeton
        self.requested_critical_section = False  # Flag pour suivre si une section critique est demandée

        # Thread pour gérer le jeton
        self.token_thread = threading.Thread(target=self.token_manager)
        self.token_thread.daemon = True
        self.token_thread.start()

    def inc_clock(self):
        with self.clock_semaphore:
            self.lamport_clock += 1
            print(f"[Process {self.process_id}] Horloge Lamport incrémentée: {self.lamport_clock}")

    def get_clock(self):
        with self.clock_semaphore:
            return self.lamport_clock
        
    def broadcast(self, message):
        self.inc_clock()
        for i in range(self.total_processes):
            if i != self.process_id:
                self.mailboxes[i].put((message, self.get_clock()))
                print(f"[Process {self.process_id}] Message broadcasté à Process {i}: {message}")

    def sendTo(self, message, dest):
        self.inc_clock()
        self.mailboxes[dest].put((message, self.get_clock()))
        print(f"[Process {self.process_id}] Message envoyé à Process {dest}: {message}")
    
    def receive(self):
        if not self.mailboxes[self.process_id].empty():
            message, timestamp = self.mailboxes[self.process_id].get()
            with self.clock_semaphore:
                self.lamport_clock = max(self.lamport_clock, timestamp) + 1
            print(f"[Process {self.process_id}] Message reçu: {message} avec timestamp: {timestamp}")
            return message
        else:
            return None
        
    def token_manager(self):
        while True:
            if self.token_available and self.requested_critical_section:
                self.enter_critical_section()
            sleep(0.1)

    def send_system_message(self, message, dest):
        self.mailboxes[dest].put((message, None))
        print(f"[Process {self.process_id}] Message système envoyé à Process {dest}: {message}")

    def requestSC(self):
        print(f"[Process {self.process_id}] Demande d'accès à la section critique envoyée")
        self.requested_critical_section = True

    def enter_critical_section(self):
        with self.token_mutex:
            if self.token_available:
                print(f"[Process {self.process_id}] a reçu le jeton et entre dans la section critique")
                self.token_available = False  # Le processus utilise le jeton
                self.requested_critical_section = False  # Reset le flag après l'entrée dans SC
                sleep(1)  # Simuler l'exécution dans la section critique
                self.releaseSC()  # Libérer le jeton après l'exécution

    def releaseSC(self):
        next_process = (self.process_id + 1) % self.total_processes
        print(f"[Process {self.process_id}] envoie le jeton à Process {next_process}")
        self.send_system_message("TOKEN", next_process)  # Le jeton est envoyé au processus suivant
        self.token_available = False  # Le jeton est parti, donc ce processus ne l'a plus

    def receive_token(self):
        self.token_available = True
        print(f"[Process {self.process_id}] a reçu le jeton")
