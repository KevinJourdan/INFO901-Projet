import queue
from Process import Process

if __name__ == "__main__":
    total_processes = 3
    mailboxes = [queue.Queue() for _ in range(total_processes)]

    for i in range(total_processes):
        process = Process(name=f"P{i+1}", nbProcess=total_processes, verbose=True, mailboxes=mailboxes)
