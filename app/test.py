from Configuration.Manager import ConfigurationManager

if __name__ == '__main__':
    import logging.config
    logging.config.fileConfig('logging.conf')
    log = logging.getLogger()
    cm = ConfigurationManager(f'/tempate1.xml')
    jobs = cm.load()
    job1 = jobs.pop()
    job1('start')