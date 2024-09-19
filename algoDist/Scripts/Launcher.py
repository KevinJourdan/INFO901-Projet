import threading
import queue
from Com import Com
from Process import Process

# Code de lancement des processus
if __name__ == "__main__":
    total_processes = 3  # Par exemple, si tu as 3 processus
    mailboxes = [queue.Queue() for _ in range(total_processes)]  # Crée une boîte aux lettres pour chaque processus
    request_queue = queue.Queue()  # La file d'attente partagée pour les requêtes de section critique

    # Lancement des processus
    for i in range(total_processes):
        process = Process(name=f"P{i+1}", nbProcess=total_processes, verbose=True, mailboxes=mailboxes, request_queue=request_queue)