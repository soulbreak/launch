import threading, queue
from Workflow.Structure import Graph
from Node import State
import logging
log = logging.getLogger()
q = queue.Queue()


class ThreadPool:
    """Pool of threads consuming tasks from a queue"""
    def __init__(self, num_threads=0):
        self.queue = queue.Queue(num_threads)
        for _ in range(num_threads):
            t = Worker(self.queue)
            log.debug(f"Creating new thread {t}")

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
        self.name = threading.current_thread().name

        self.daemon = True
        self.start()

    def run(self):

        while True:
            func, args, kargs = self.tasks.get()
            try:
                log.debug("New thread run")
                func(*args, **kargs)
            except Exception as e:
                print(e)
            finally:
                self.tasks.task_done()

def run(graph: Graph, trigger: str):
    pool = ThreadPool(4)
    logging.info("Running Graph's trigger \"{0}\"".format(trigger))
    while graph.node_end.state != State.ENDED_OK:
        jobs = graph.get_jobs_ready()
        if jobs:
            [setattr(job, 'status', State.RUNNING) for job in jobs]
            [setattr(job, 'trigger', trigger) for job in jobs]
            log.info(f"Launching jobs : {jobs}")
            for job in jobs:
                pool.add_task(job)
