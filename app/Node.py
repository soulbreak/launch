import logging
from enum import Enum

class Status(Enum):
    NOT_READY = 0
    READY = 1
    RUNNING = 2
    FAILED = 3
    ENDED_OK = 4

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

    def __call__(self, *args, **kwargs) -> Status:
        """
        Return 0 if the action occured without issue
        :param args:
        :param kwargs:
        :return:
        """
        logging.info("calling {}".format(self.name))
        self.status = Status.RUNNING
        if self.action == Action.START:
            rc = self.start(*args, **kwargs)
        elif self.action == Action.STOP:
            rc = self.stop(*args, **kwargs)
        elif self.action == Action.CHECK:
            rc = self.standalone_check(*args, **kwargs)
        else:
            raise RuntimeError("Unsupported action on {}".format(self.name))
        if rc == ReturnCode.OK:
            self.status = Status.ENDED_OK
        else:
            self.status = Status.FAILED

        return self.status


    def start(self, *args, **kwargs) -> ReturnCode:
        """
        Check, start the job if needed, re-check the result
        :param args:
        :param kwargs:
        :return:
        """
        rc = self.standalone_check()
        if rc == ReturnCode.OK:
            logging.info("{} already started".format(self.__repr__()))
            return ReturnCode.OK
        elif rc == ReturnCode.KO:
            logging.info("starting {}".format(self.__repr__()))
        elif rc == ReturnCode.UNKNOWN:
            logging.info("{} cannot be started with an unexpected check return code = \"{}\"".format(
                self.__repr__(), rc))
        else:
            logging.exception("{} cannot be stopped with an unexpected check return code = \"{}\"".format(
                self.__repr__(), rc))
        return ReturnCode.OK if self.standalone_check() == ReturnCode.OK else 1

    def stop(self, *args, **kwargs) -> ReturnCode:
        """
        Check, stop the job if needed, re-check the result
        :param args:
        :param kwargs:
        :return:
        """
        rc = self.standalone_check()
        if rc == ReturnCode.OK:
            logging.info("stopping {}".format(self.__repr__()))
        elif rc == ReturnCode.KO:
            logging.info("{} already stopped".format(self.__repr__()))
            return ReturnCode.OK
        elif rc == ReturnCode.UNKNOWN:
            logging.info("{} cannot be stopped with an unexpected check return code = \"{}\"".format(
                self.__repr__(), rc))
        else:
            logging.exception("{} cannot be stopped with an unexpected check return code = \"{}\"".format(
                self.__repr__(), rc))

        return ReturnCode.OK if self.standalone_check() == ReturnCode.KO else 1

    def check(self, *args, **kwargs) -> ReturnCode:
        """
        Check
        :param args:
        :param kwargs:
        :return:
        """
        return ReturnCode.OK if self.standalone_check() == ReturnCode.KO else 1

    def standalone_check(self, *args, **kwargs) -> ReturnCode:
        rc = ReturnCode.UNKNOWN
        logging.info("Checking {}".format(self.name))
        rc = ReturnCode.OK
        logging.info("Status {} = {}".format(self.name, rc))
        return rc

    def __repr__(self):
        return self.name


