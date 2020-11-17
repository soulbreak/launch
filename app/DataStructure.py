from collections import defaultdict
from Node import Job, Status
import logging
from typing import List


class Graph:
    def __init__(self):
        self.reversed = False
        self.dependencies = defaultdict(list)
        self.reverse_dependencies = defaultdict(list)
        self.node_start = Job("node_start", Status.READY)
        self.node_end = Job("node_end", Status.NOT_READY)


    def _get_dependencies_list(self, node: Job) -> List[Job]:
        if self.reversed is False:
            return self.dependencies[node]
        else:
            return self.reverse_dependencies[node]

    def _add_normal_dep(self, nodea: Job, node_list: List[Job]) -> None:
        # Detach from end
        if self.node_end in self.dependencies[nodea]:
            self.dependencies[nodea].remove(self.node_end)

        for node in node_list:
            if not isinstance(node, Job):
                raise RuntimeError(f'{node} is not a Job object')
            # Detach dependencies nodes from start
            if node in self.dependencies[self.node_start]:
                self.dependencies[self.node_start].remove(node)
            # Add the node
            if node not in self.dependencies[nodea]:
                self.dependencies[nodea].append(node)

        all_dependencies = [item for sublist in self.dependencies.values() for item in sublist]
        if nodea not in all_dependencies:
            self.dependencies[self.node_start].append(nodea)

        if len(self.dependencies[self.node_start]) == 0:
            raise RuntimeError(f"Adding node {nodea} with dependencies {node_list} break the graph (it create a cycle)")

        # Retach to end_node
        all_dependencies_without_dependencies = [item for item in all_dependencies
                                                 if item not in self.dependencies.keys() and item != self.node_end]

        for node in all_dependencies_without_dependencies:
            self.dependencies[node].append(self.node_end)

    def _add_rev_dep(self, nodea: Job, node_list: List[Job]) -> None:
        # Detach main node from start
        if nodea in self.reverse_dependencies[self.node_start]:
            self.reverse_dependencies[self.node_start].remove(nodea)

        for node in node_list:
            if self.node_end in self.reverse_dependencies[node]:
                self.reverse_dependencies[node].remove(self.node_end)
            # Add the node
            if nodea not in self.reverse_dependencies[node]:
                self.reverse_dependencies[node].append(nodea)

        all_dependencies = [item for sublist in self.reverse_dependencies.values() for item in sublist]
        for node in node_list:
            if node not in all_dependencies and node not in self.reverse_dependencies[self.node_start]:
                self.reverse_dependencies[self.node_start].append(node)
        # Retach to end_node
        all_dependencies_without_dependencies = [item for item in all_dependencies
                                                 if item not in self.reverse_dependencies.keys()
                                                 and item != self.node_end]

        for node in all_dependencies_without_dependencies:
            if self.node_end not in self.reverse_dependencies[node]:
                self.reverse_dependencies[node].append(self.node_end)


    def add_dependencies(self, nodea: Job, node_list: List[Job]) -> None:
        self._add_normal_dep(nodea, node_list)
        self._add_rev_dep(nodea, node_list)

    def isCyclicRecursive(self, current: Job, visited, recStack):
        visited[current] = True
        recStack[current] = True

        for neighbour in self._get_dependencies_list(current):
            if visited.get(neighbour, False) == False:
                if self.isCyclicRecursive(neighbour, visited, recStack) == True:
                    return True
            elif recStack.get(neighbour, False):
                logging.warning(f"Cyclic found between {current} and {neighbour}")
                return True

        recStack[current] = False
        return False

    # Returns true if graph is cyclic else false
    def is_cyclic(self, root_node: Job=None):
        if root_node is None:
            root_node = self.node_start
        visited = dict()
        recStack = dict()
        for node in self._get_dependencies_list(root_node):
            if visited.get(node, False) == False:
                if self.isCyclicRecursive(node, visited, recStack) == True:
                    return True
        return False

    def get_jobs_ready(self) -> List[Job]:
        for job, rdeps in self.reverse_dependencies.items():
            if(all(rdep.status == Status.ENDED_OK for rdep in rdeps)):
                job.status = Status.READY
        return [node for node in self.get_all_nodes(self.node_start) if node.status == Status.READY]

    def is_dependency_of(self, current: Job, seek: Job) -> bool:
        """
        Check recursively if seek in a dependency of current
        :param current:
        :param seek:
        :return:
        """
        visited = dict()
        stack = []
        stack.append(current)

        while (len(stack)):
            current = stack[-1]
            stack.pop()
            if seek is current:
                return True
            if current not in visited.keys():
                visited[current] = True

            for node in self._get_dependencies_list(current):
                if node not in visited.keys():
                    stack.append(node)

        return False

    def get_all_nodes(self, current: Job=None) -> List[Job]:
        list = []
        if current is None:
            current = self.node_start
        visited = dict()
        stack = []
        stack.append(current)

        while (len(stack)):
            current = stack[-1]
            stack.pop()

            if current not in visited.keys():
                list.append(current)
                visited[current] = True

            for node in self._get_dependencies_list(current):
                if node not in visited.keys():
                    stack.append(node)
        return list



    def write_dot_file(self, root_node: Job=None, filepath: str= 'launch.dot') -> None:
        colorDict = {
            Status.READY : '[fillcolor=green style=filled]',
            Status.FAILED: '[fillcolor=red style=filled]',
            Status.RUNNING: '[fillcolor=blue style=filled]',
            Status.ENDED_OK: '[fillcolor=blue style=filled]',
            Status.NOT_READY:'[fillcolor=grey85 style=filled]'
        }
        node_colored_written = dict()
        if root_node is None:
            root_node = self.node_start
        file = open(filepath, 'w')
        file.write("digraph dagger {\nbgcolor = white;\n")
        visited = dict()
        stack = []
        stack.append(root_node)

        while (len(stack)):
            current = stack[-1]
            stack.pop()

            if current not in visited.keys():
                visited[current] = True

            for node in self._get_dependencies_list(current):
                if node not in node_colored_written.keys():
                    node_colored_written[node] = 1
                    file.write("{} {}\n".format(
                        node, ' ' + colorDict[node.status] if node.status in colorDict.keys() else ''))
                if current not in node_colored_written.keys():
                    node_colored_written[current] = 1
                    file.write("{} {}\n".format(current,
                    ' ' + colorDict[current.status] if current.status in colorDict.keys() else ''))
                file.write("\"{}\" -> \"{}\";\n".format(current, node))
                if node not in visited.keys():
                    stack.append(node)
        file.write("}\n")
        file.close()