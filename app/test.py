def createFilesystemsGraph(rootdir):
    import os
    g = Graph()
    dirDict = {}
    for root, dirs, files in os.walk(rootdir):

        root = os.path.join(*os.path.normpath(root).split(os.path.sep))
        if root not in dirDict.keys():
            dirDict[root] = Node(os.path.basename(root))
        dir = dirDict.get(root)
        parent = os.path.join(*os.path.normpath(root).split(os.path.sep)[0:-1])
        if parent not in dirDict.keys():
            dirDict[parent] = Node(os.path.basename(parent))
        parent = dirDict.get(parent)
        if os.path.join(*os.path.normpath(root).split(rootdir)) != root:
            g.add_dependencies(parent, [dir])

        for file in files:
            f = Node(file)
            g.add_dependencies(dir, [f])
    g.write_dot_file(filepath='graph.dot')