import logging
import threading, queue
import time
from DataStructure import Graph
from Node import Job, Status, Action
import random
import sys
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

q = queue.Queue()


class ThreadPool:
    """Pool of threads consuming tasks from a queue"""
    def __init__(self, num_threads=0):
        self.queue = queue.Queue(num_threads)
        for _ in range(num_threads):
            Worker(self.queue)


    def add_task(self, func, *args, **kargs):
        """Add a task to the queue"""
        self.queue.put((func, args, kargs))

    def wait_completion(self):
        """Wait for completion of all the tasks in the queue"""
        self.queue.join()

class Worker(threading.Thread):
    """Thread executing tasks from a given tasks queue"""
    def __init__(self, tasks):
        super(Worker, self).__init__()
        self.tasks = tasks
        self.daemon = True
        self.start()

    def run(self):
        while True:
            func, args, kargs = self.tasks.get()
            try:
                func(*args, **kargs)
            except Exception as e:
                print(e)
            finally:
                self.tasks.task_done()




if __name__ == '__main__':
    job = Job("cool")
    graph = Graph()
    A1 = Job('A1')
    A2 = Job('A2')
    A3 = Job('A3')
    A4 = Job('A4')
    A5 = Job('A5')
    graph.add_dependencies(A1,[])
    graph.add_dependencies(A1,[A2,A3])
    graph.add_dependencies(A3,[A4])
    graph.add_dependencies(A3,[A5])
    graph.add_dependencies(A2,[A5])
    pool = ThreadPool(20)
    while graph.node_end.status != Status.ENDED_OK:
        jobs = graph.get_jobs_ready()
        if jobs:
            [setattr(job,'status', Status.RUNNING) for job in jobs]
            [setattr(job, 'action', Action.START) for job in jobs]
            logging.info(f"Launching jobs : {jobs}")
            for job in jobs:
                pool.add_task(job)
            # To do need to check if workflow is blocked
