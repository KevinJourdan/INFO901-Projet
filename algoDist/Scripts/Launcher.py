from Com import Com
import threading
import queue
import time

def process_behavior(process_id, total_processes, com):
    if process_id == 0:
        com.broadcast("Hello from Process 0")
    elif process_id == 1:
        com.sendTo("Hello Process 2", 2)
    
    time.sleep(1)  # Laisser le temps aux autres processus de recevoir
    com.receive()

if __name__ == "__main__":
    total_processes = 3
    mailboxes = [queue.Queue() for _ in range(total_processes)]  # Boîtes aux lettres partagées
    
    processes = []
    
    # Crée une instance de Com pour chaque processus avec la boîte aux lettres partagée
    for i in range(total_processes):
        com = Com(i, total_processes, mailboxes)
        p = threading.Thread(target=process_behavior, args=(i, total_processes, com))
        processes.append(p)
        p.start()

    # Attendre que tous les threads terminent
    for p in processes:
        p.join()