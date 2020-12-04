import xml.etree.ElementTree as ET
from Node import Job, BlkCmd, Cmd
from typing import List
import logging
log = logging.getLogger()

class ConfigurationManager(object):
    def __init__(self, path_name):
        self.path_name = path_name
        self.tree = ET.parse(self.path_name)
        self.root = self.tree.getroot()

    def load_blkcmd_object(self, node):
        if node is None:
            return

        new_blkcmd = BlkCmd()
        for cmd_node in list(node):
            if cmd_node.find('stdin') is None:
                log.fatal("Cmd need at least a stdin element")
            cmd = Cmd(cmd_node.find('stdin').text)
            cmd.level = cmd_node.attrib.get('level', 1)
            if cmd_node.find('on_success'):
                cmd.on_success = self.load_blkcmd_object(cmd_node.find('on_success').find('BlkCmd'))
            if cmd_node.find('on_failure'):
                cmd.on_failure = self.load_blkcmd_object(cmd_node.find('on_failure').find('BlkCmd'))
            if cmd_node.find('always'):
                cmd.always = self.load_blkcmd_object(cmd_node.find('always').find('BlkCmd'))
            new_blkcmd.add_commands(cmd)
        return new_blkcmd

    def load(self) -> List[Job]:
        created = list()
        element = ['start_cmd', 'stop_cmd', 'status_cmd']
        for node in self.root.findall('node'):
            j = Job(node.attrib.get('name'))
            for elm in element:
                if node.find(elm) is not None:
                    elm_node = node.find(elm)
                    if elm_node.find('BlkCmd') is not None:
                        blk_to_load = elm_node.find('BlkCmd')
                        setattr(j, elm, self.load_blkcmd_object(blk_to_load))
                    else:
                        log.error('BlkCmd is missing in node')

            created.append(j)
        return created




