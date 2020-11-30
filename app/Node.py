import logging
from enum import Enum
from typing import List, Optional


class State(Enum):
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
    UNDEFINED = -1


class BlkCmd(object):
    pass


class Cmd(object):
    def __init__(self, stdin: str,
                 on_success: Optional[BlkCmd] = None,
                 on_failure: Optional[BlkCmd] = None,
                 always: Optional[BlkCmd] = None,
                 level: int = 1):
        self.stdin = stdin
        self.stdout = None
        self.stderr = None
        self.level = level
        self.on_success = on_success
        self.on_failure = on_failure
        self.always = always


    def __repr__(self):
        return '[{}:{}]'.format(self.__class__.__name__,
                                ','.join(["({}={})".format(k,repr(v)) for k, v in self.__dict__.items()]))


class BlkCmd(object):
    def __init__(self, commands: List[Cmd] = []):
        self.commands = commands
        self.return_code = ReturnCode.UNDEFINED

    def __call__(self, *args, **kwargs):
        for cmd in self.commands:
            cmd()

    def __repr__(self):
        return '[{}:{}]'.format(self.__class__.__name__,
                                ','.join(["({}={})".format(k,repr(v)) for k, v in self.__dict__.items()]))



class Job(object):
    def __init__(self, name: str, state: State = State.NOT_READY, action: Action = Action.CHECK,
                 start_cmd: BlkCmd = None, stop_cmd: BlkCmd = None, status: BlkCmd = None):
        self.name = name
        self.state = state
        self.action = action
        self.start_cmd = start_cmd
        self.stop_cmd = stop_cmd
        self.status_cmd = status

    def __call__(self, *args, **kwargs) -> State:
        """
        Return 0 if the action occured without issue
        :param args:
        :param kwargs:
        :return:
        """
        logging.debug("Calling {}".format(self.name))
        self.state = State.RUNNING
        if self.action == Action.START:
            rc = self.start(*args, **kwargs)
        elif self.action == Action.STOP:
            rc = self.stop(*args, **kwargs)
        elif self.action == Action.CHECK:
            rc = self.standalone_check(*args, **kwargs)
        else:
            raise RuntimeError("Unsupported action on {}".format(self.name))
        if rc == ReturnCode.OK:
            self.state = State.ENDED_OK
        else:
            self.state = State.FAILED

        return self.state


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
        return '[{}:{}]'.format(self.__class__.__name__,
                                ','.join(["({}={})".format(k,repr(v)) for k, v in self.__dict__.items()]))






