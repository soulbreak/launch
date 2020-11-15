from DataStructure import Graph
from Node import Job
import logging
if __name__ == '__main__':


    job = Job("cool")
    g = Graph()
    A1 = Job('A1')
    A2 = Job('A2')
    A3 = Job('A3')
    A4 = Job('A4')
    A5 = Job('A5')
    g.add_dependencies(A1,[])
    g.add_dependencies(A1,[A2,A3])
    g.add_dependencies(A3,[A4])
    g.add_dependencies(A3,[A5])
    g.add_dependencies(A2,[A5])
    #g.DFS()
    g.write_dot_file(filepath='graph.dot')
    g.is_cyclic()
    g.reversed = True
    g.write_dot_file(filepath='rev_graph.dot')

