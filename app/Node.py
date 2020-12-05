import logging
import subprocess
import shlex
import logging
log = logging.getLogger()
from enum import Enum
from typing import List, Optional
from collections.abc import  Sequence

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
        self.return_code = ReturnCode.UNDEFINED

    def __call__(self, *args, **kwargs):
        """Reset default values"""
        self.return_code = ReturnCode.UNDEFINED
        self.stderr = None
        self.stdout = None
        _cmd = shlex.split(self.stdin)
        logging.info("Launching Cmd: {}".format(self.stdin))
        process = subprocess.Popen(_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.stdout, self.stderr = process.communicate()
        if process.returncode == 0:
            self.return_code = ReturnCode.OK
        else:
            self.return_code = ReturnCode.KO
        logging.info("Cmd RC: {} = {}".format(self.stdin, self.return_code))
        if self.return_code == ReturnCode.OK and self.on_success:
            logging.debug("Launching on_success")
            self.on_success()
        elif self.return_code != ReturnCode.OK and self.on_failure:
            logging.debug("Launching on_failure")
            self.on_failure()
        if self.always:
            logging.debug("Launching always")
            self.always()
        return self


    def __repr__(self):
        return '[{}:{}]'.format(self.__class__.__name__,
                                ','.join(["({}={})".format(k,repr(v)) for k, v in self.__dict__.items()]))


class BlkCmd(object):
    def __init__(self):
        self.commands = list()
        self.return_code = None

    def add_commands(self, cmd: Cmd):
        self.commands.append(cmd)

    def __call__(self, *args, **kwargs):
        self.return_code = ReturnCode.UNDEFINED
        for cmd in sorted(self.commands, key=lambda x: x.level):
            rc = cmd().return_code
            if self.return_code == ReturnCode.UNDEFINED:
                self.return_code = rc
            elif self.return_code == ReturnCode.OK and rc == ReturnCode.OK:
                pass
            elif self.return_code == ReturnCode.KO and rc == ReturnCode.KO:
                pass
            else:
                self.return_code = ReturnCode.UNKNOWN
        return self

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

        # Sanity check
        rc = self.standalone_check()
        if rc == ReturnCode.OK:
            logging.info("{} already started".format(self.name))
            return ReturnCode.OK
        elif rc == ReturnCode.KO:
            logging.info("starting {}".format(self.name))
            self.start_cmd()
        elif rc == ReturnCode.UNKNOWN:
            logging.info("{} cannot be started with an unexpected check return code = \"{}\"".format(
                self.name, rc))
        else:
            logging.exception("{} cannot be stopped with an unexpected check return code = \"{}\"".format(
                self.name, rc))
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
            logging.info("stopping {}".format(self.name))
            self.stop_cmd()
        elif rc == ReturnCode.KO:
            logging.info("{} already stopped".format(self.name))
            return ReturnCode.OK
        elif rc == ReturnCode.UNKNOWN:
            logging.info("{} cannot be stopped with an unexpected check return code = \"{}\"".format(
                self.name, rc))
        else:
            logging.exception("{} cannot be stopped with an unexpected check return code = \"{}\"".format(
                self.name, rc))

        return ReturnCode.OK if self.standalone_check() == ReturnCode.KO else 1

    def check(self, *args, **kwargs) -> ReturnCode:
        return ReturnCode.OK if self.standalone_check() == ReturnCode.KO else 1

    def standalone_check(self, *args, **kwargs) -> ReturnCode:
        logging.info("Checking {}".format(self.name))
        rc = self.status_cmd().return_code
        logging.info("{} status = {}".format(self.name, rc))
        return rc

    def __repr__(self):
        return '[{}:{}]'.format(self.__class__.__name__,
                                ','.join(["({}={})".format(k,repr(v)) for k, v in self.__dict__.items()]))






