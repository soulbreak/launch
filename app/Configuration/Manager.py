import xml.etree.ElementTree as ET
import re
from Node import Job, BlkCmd, Cmd, Msg
from typing import List
import logging
log = logging.getLogger()

class ConfigurationManager(object):
    def __init__(self, path_name):
        self.path_name = path_name
        self.tree = ET.parse(self.path_name)
        self.root = self.tree.getroot()

    def display_template(self, template_name):
        node = self.tree.find("template[@name='{0}']".format(template_name))
        template = ET.tostring(node)

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

    def load_all_templates(self) -> List[Job]:
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

    def load_node(self, node_name):
        node = self.root.find("node[@name='{0}']".format(node_name))
        if node is None:
            logging.fatal("{0} does not exist")
        job = Job(node_name)
        template = node.attrib.get('template')
        property_dict = dict()
        stack = []
        for property in node.findall('property'):
            text = property.text
            name = property.attrib['name']
            stack.append((name, text))
        solved = True
        while solved:
            solved = False
            name, text = stack.pop()
            matches = re.findall("({{\s*\w+\s*}})",text)
            if len(matches) == 0:
                property_dict[name] = text
                solved = True
            else:
                for match in matches:
                    properties = re.findall("\w+", match)
                    current_solved = 0
                    if property in property_dict.keys():
                        text = re.sub(match, property_dict[property], text)
                        logging.debug("{} replaced by {}".format(match, text))
                        solved = True
                        current_solved += 1
                    else:
                        stack.append((name, text))
                        break
                    property_dict[name] = text
        if len(stack) != 0:
            logging.fatal("Unsolved properties : {}".format(stack))
        logging.info("Properties loaded : {}".format(property_dict))
        return job


