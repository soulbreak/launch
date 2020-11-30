import xml.etree.ElementTree as ET
from Node import Job, BlkCmd, Cmd

class ConfigurationManager(object):
    def __init__(self, path_name):
        self.path_name = path_name
        self.tree = ET.parse(self.path_name)
        self.root = self.tree.getroot()


    def load_blkcmd_object(self, node):
        if node is None:
            return

        blkcmd = BlkCmd()
        for cmd_node in list(node):
            cmd = Cmd(cmd_node.find('stdin').text)
            cmd.level = cmd_node.attrib.get('level', 1)
            if cmd_node.find('on_success'):
                cmd.on_success = self.load_blkcmd_object(cmd_node.find('on_success').find('BlkCmd'))
            if cmd_node.find('on_failure'):
                cmd.on_failure = self.load_blkcmd_object(cmd_node.find('on_failure').find('BlkCmd'))
            if cmd_node.find('always'):
                cmd.always = self.load_blkcmd_object(cmd_node.find('always').find('BlkCmd'))
            blkcmd.commands.append(cmd)
        return blkcmd



    def load(self):
        created = list()
        element = ['start_cmd', 'stop_cmd', 'status_cmd']
        for node in self.root.findall('node'):
            j = Job(node.attrib.get('name'))
            for elm in element:
                if node.find(elm) is None:
                    continue
                for o in list(node.find(elm)):
                    setattr(j, elm, self.load_blkcmd_object(o))


            print(j)











if __name__ == '__main__':
    cm = ConfigurationManager(f'/home/soulbreak/PycharmProjects/launch/conf.xml')
    cm.load()