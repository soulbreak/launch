from Configuration.Manager import ConfigurationManager
from Workflow.Execution import run
from Workflow.Structure import Graph

if __name__ == '__main__':
    import logging.config
    logging.config.fileConfig('logging.conf')
    log = logging.getLogger()
    cm = ConfigurationManager(f'../configuration.xml')
    cm.display_template('template_test')
    #jobs = cm.load_all_templates()
    graph = Graph()
    cm.load_nodes_with_dependencies(graph, ["test"])
    run(graph, 'start')