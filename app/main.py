from Node import Job
from Workflow.Structure import Graph
from Workflow.Execution import run

def main():
    import logging.config
    logging.config.fileConfig('logging.conf')
    log = logging.getLogger(__name__)
    # your program code

    job = Job("cool")
    graph = Graph()
    A1 = Job('A1')
    A2 = Job('A2')
    A3 = Job('A3')
    A4 = Job('A4')
    A5 = Job('A5')
    graph.add_dependencies(A1, [])
    graph.add_dependencies(A1, [A2, A3])
    graph.add_dependencies(A3, [A4])
    graph.add_dependencies(A3, [A5])
    graph.add_dependencies(A2, [A5])
    graph.build_reverse_dependencies()
    run(graph)
    log.info("Program ends")


if __name__ == '__main__':
    main()
