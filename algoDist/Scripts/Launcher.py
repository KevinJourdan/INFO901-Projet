from time import sleep
from Process import Process
import sys


def launch(nbProcessToCreate: int, verbosityLevel: int, runningTime: int):
    processes = []

    for i in range(nbProcessToCreate):
        processes.append(Process("P" + str(i), nbProcessToCreate, verbosityLevel))

    sleep(runningTime)

    for p in processes:
        p.stop()


def getParam(pos: int, default: int) -> int:
    if len(sys.argv) > pos:
        return int(sys.argv[pos])
    return default


if __name__ == '__main__':
    launch(getParam(1, 3), getParam(3, 7), getParam(2, 15))