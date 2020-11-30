from collections import defaultdict
from Node import Job, State
import logging
from typing import List


class Graph:
    def __init__(self):
        self.reversed = False
        self.dependencies = defaultdict(list)
        self.reverse_dependencies = defaultdict(list)
        self.node_start = Job("node_start", State.READY)
        self.node_end = Job("node_end", State.NOT_READY)

    def _get_dependencies_list(self) -> List[Job]:
        if self.reversed is False:
            return self.dependencies
        else:
            return self.reverse_dependencies

    def _get_reverse_dependencies_list(self) -> List[Job]:
        if self.reversed is False:
            return self.reverse_dependencies
        else:
            return self.dependencies

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

    def build_reverse_dependencies(self):
        self.reverse_dependencies.clear()
        for node, deps in self.dependencies.items():
            for dep in deps:
                if node not in self.reverse_dependencies.get(dep, []):
                    self.reverse_dependencies[dep].extend([node])

    def add_dependencies(self, nodea: Job, node_list: List[Job]) -> None:
        self._add_normal_dep(nodea, node_list)
        # self._add_rev_dep(nodea, node_list)

    def isCyclicRecursive(self, current: Job, visited, recStack):
        visited[current] = True
        recStack[current] = True

        for neighbour in self._get_dependencies_list()[current]:
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
        for node in self._get_dependencies_list()[root_node]:
            if visited.get(node, False) == False:
                if self.isCyclicRecursive(node, visited, recStack) == True:
                    return True
        return False

    def get_jobs_ready(self) -> List[Job]:
        """
        Set job as READY if all reverse dependencies are in status ENDED_OK
        """
        for job, rdeps in self._get_reverse_dependencies_list().items():
            if job.state == State.NOT_READY:
                if(all(rdep.state == State.ENDED_OK for rdep in rdeps)):
                    job.state = State.READY
        return [node for node in self.get_all_nodes(self.node_start) if node.state == State.READY]

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

            for node in self._get_dependencies_list()[current]:
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

            for node in self._get_dependencies_list()[current]:
                if node not in visited.keys():
                    stack.append(node)
        return list



    def write_dot_file(self, root_node: Job=None, filepath: str= 'launch.dot') -> None:
        colorDict = {
            State.READY : '[fillcolor=green style=filled]',
            State.FAILED: '[fillcolor=red style=filled]',
            State.RUNNING: '[fillcolor=blue style=filled]',
            State.ENDED_OK: '[fillcolor=blue style=filled]',
            State.NOT_READY: '[fillcolor=grey85 style=filled]'
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

            for node in self._get_dependencies_list()[current]:
                if node not in node_colored_written.keys():
                    node_colored_written[node] = 1
                    file.write("{} {}\n".format(
                        node, ' ' + colorDict[node.state] if node.state in colorDict.keys() else ''))
                if current not in node_colored_written.keys():
                    node_colored_written[current] = 1
                    file.write("{} {}\n".format(current,
                    ' ' + colorDict[current.state] if current.state in colorDict.keys() else ''))
                file.write("\"{}\" -> \"{}\";\n".format(current, node))
                if node not in visited.keys():
                    stack.append(node)
        file.write("}\n")
        file.close()