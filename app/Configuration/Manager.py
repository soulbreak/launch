import xml.etree.ElementTree as ET
from Node import Job, BlkCmd, Cmd, Msg
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
        block_attribs = ['retry_end_on_rc', 'maxtime', 'sleep']
        myBlkCmd = BlkCmd()

        for attrib in block_attribs:
            if attrib in node.attrib:
                setattr(myBlkCmd, attrib, int(node.attrib[attrib]))

        for blkinput in list(node):
            blkinput_obj = None
            if blkinput.tag == 'Cmd':
                blkinput_obj = Cmd(blkinput.find('stdin').text)
            elif blkinput.tag == 'Msg':
                blkinput_obj = Msg(blkinput.find('stdin').text)

            if blkinput.find('on_success'):
                blkinput_obj.on_success = self.load_blkcmd_object(blkinput.find('on_success/BlkCmd'))
            if blkinput.find('on_failure'):
                blkinput_obj.on_failure = self.load_blkcmd_object(blkinput.find('on_failure/BlkCmd'))
            if blkinput.find('always'):
                blkinput_obj.always = self.load_blkcmd_object(blkinput.find('always/BlkCmd'))
            myBlkCmd.add_commands(blkinput_obj)
        return myBlkCmd

    def load(self) -> List[Job]:
        created = list()
        for node in self.root.findall('template'):
            j = Job(node.attrib.get('name'))
            for item in node.findall('trigger'):
                logging.debug("Loading {}".format(item.attrib['name']))
                if item.find('BlkCmd') is not None:
                    blk_to_load = item.find('BlkCmd')
                    setattr(j, item.attrib['name'], self.load_blkcmd_object(blk_to_load))
                else:
                    log.error('BlkCmd is missing in node {}'.format(item.attrib['name']))
            created.append(j)
        return created




