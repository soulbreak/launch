import logging
from enum import Enum

class Status(Enum):
    NOT_READY = 0
    READY = 1
    RUNNING = 2
    FAILED = 3
    ENDED_OK = 3

class Action(Enum):
    START = 0
    STOP = 1
    CHECK = 2

class ReturnCode(Enum):
    OK = 0
    KO = 1
    UNKNOWN = 255


class Job(object):
    def __init__(self, name: str, status: Status=Status.NOT_READY, action: Action=Action.CHECK,
                 start_cmd: str=None, stop_cmd: str=None, check_cmd: str=None):
        self.name = name
        self.status = status
        self.action = action
        self.start_cmd = start_cmd
        self.stop_cmd = stop_cmd
        self.check_cmd = check_cmd



    def __call__(self, *args, **kwargs) -> ReturnCode:
        """
        Return 0 if the action occured without issue
        :param args:
        :param kwargs:
        :return:
        """
        if self.action == Action.START:
            return self.start(*args, **kwargs)
        elif self.action == Action.STOP:
            return self.stop(*args, **kwargs)
        elif self.action == Action.CHECK:
            return self.check(*args, **kwargs)
        else:
            raise RuntimeError("Unsupported action on {}".format(self.name))
        logging.info("call {}".format(self.name))

    def start(self, *args, **kwargs) -> ReturnCode:
        rc = self.check()
        if rc == 0:
            logging.info("{} already started".format(self.__repr__()))
        elif rc == 1:
            logging.info("starting {}".format(self.__repr__()))
        elif rc == 255:
            logging.info("{} cannot be started with an unexpected check return code = \"{}\"".format(self.__repr__()))
        else:
            raise RuntimeError("{} cannot be stopped with an unexpected check return code = \"{}\"".format(rc))
        return self.check()

    def stop(self, *args, **kwargs) -> ReturnCode:
        rc = self.check()
        if rc == 0:
            logging.info("stopping {}".format(self.__repr__()))
        elif rc == 1:
            logging.info("{} already stopped".format(self.__repr__()))
        elif rc == 255:
            logging.info("{} cannot be stopped with an unexpected check return code = \"{}\"".format(self.__repr__()))
        else:
            raise RuntimeError("{} cannot be stopped with an unexpected check return code = \"{}\"".format(rc))
        return self.check()

    def check(self, *args, **kwargs) -> ReturnCode:
        rc = ReturnCode.UNKNOWN
        logging.info("checking {}".format(self.name))
        rc = ReturnCode.OK
        return rc

    def __repr__(self):
        return self.name


