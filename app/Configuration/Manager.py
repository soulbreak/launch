import xml.etree.ElementTree as ET
import re
from Node import Job, BlkCmd, Cmd, Msg
from typing import List
import logging
import json
log = logging.getLogger()

class ConfigurationManager(object):
    def __init__(self, path_name):
        self.path_name = path_name
        self.tree = ET.parse(self.path_name)
        self.root = self.tree.getroot()

    def display_template(self, template_name):
        node = self.tree.find("template[@name='{0}']".format(template_name))
        template = ET.tostring(node)

    def load_blkcmd_object(self, node, properties=None):
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


    def load_instance(self, job, template_name, properties) -> Job:
        created = list()
        node = self.root.findall("template[@name='{}']".format(template_name))
        if len(node) != 1:
            raise RuntimeError("template[@name='{}'] != 1".format(template_name))
    
        for item in node.findall('trigger'):
            logging.debug("Loading {}".format(item.attrib['name']))
            if item.find('BlkCmd') is not None:
                blk_to_load = item.find('BlkCmd')
                setattr(job, item.attrib['name'], self.load_blkcmd_object(blk_to_load))
            else:
                log.error('BlkCmd is missing in node {}'.format(item.attrib['name']))
        created.append(job)
        return job

    @staticmethod
    def load_properties(properties):
        solved = True
        while solved:
            solved = False
            for k, v in properties.items():
                if v['solved'] is True:
                    continue
                text = v['text']
                matches = re.findall("({{\s*\w+\s*}})", text)
                if len(matches) == 0:
                    v['solved'] = True
                    solved = True
                    continue

                for match in matches:
                    variable = re.findall("\w+", match)
                    if len(variable) != 1:
                        raise RuntimeError("Bad variable name {}".format(variable))
                    variable = variable[0]
                    current_solved = 0
                    if variable in properties.keys() and properties[variable]['solved'] is True:
                        text = re.sub(match, properties[variable]['text'] , text)
                        logging.debug("{} replaced by {}".format(match, text))
                        solved = True
                        current_solved += 1

                if len(matches) == current_solved:
                    v['solved'] = True
                    solved = True
                v['text'] = text
        logging.info("Properties : {}".format(
            json.dumps(
                    properties,
                    sort_keys=True,
                    indent=4))
        )
        if False in [p['solved'] for p in properties.values()]:
            raise RuntimeError("Some properties are not solved : {}".format(
                json.dumps(
                    properties,
                    sort_keys=True,
                    indent=4))
            )


    def load_node(self, node_name):
        node = self.root.find("node[@name='{0}']".format(node_name))
        if node is None:
            logging.fatal("{0} does not exist")
        job = Job(node_name)
        template = node.attrib.get('template')

        properties = dict()
        for prop in node.findall('const'):
            text = prop.text
            name = prop.attrib['name']
            properties[name] = {'text': text, 'solved': False}
        ConfigurationManager.load_properties(properties)
        self.load_instance(job, template, properties)

        return job


