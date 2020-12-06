from Configuration.Manager import ConfigurationManager

if __name__ == '__main__':
    import logging.config
    logging.config.fileConfig('logging.conf')
    log = logging.getLogger()
    cm = ConfigurationManager(f'../configuration.xml')
    cm.display_template('template_test')
    jobs = cm.load_all_templates()
    j = cm.load_node('test')
    job1 = jobs.pop()
    job1('start')