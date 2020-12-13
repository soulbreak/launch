import logging
import time
import os
import subprocess
import shlex
import logging
import json
log = logging.getLogger()
from enum import Enum, IntEnum
from Utils.encoder import decode_dict


class State(IntEnum):
    NOT_READY = 0
    READY = 1
    RUNNING = 2
    FAILED = 3
    ENDED_OK = 4


class ReturnCode(IntEnum):
    OK = 0
    KO = 1
    UNKNOWN = 255
    UNDEFINED = -1



class BlkCmd(object):
    pass


class BlkInput(object):
    def __init__(self, level: int = 1):
        self.level = level
        self.on_success = None
        self.on_failure = None
        self.always = None
        self.return_code = ReturnCode.UNDEFINED

    def __call__(self, *args, **kwargs):
        self._pre_call()
        self._call()
        self._post_call()

    def _call(self):
        raise RuntimeError('Implement me')

    def _pre_call(self):
        pass

    def _post_call(self):
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


class Msg(BlkInput):
    def __init__(self, msg: str,
                 level: int = 1):
        super(Msg, self).__init__(level)
        self.msg = msg

    def _call(self):
        self.return_code = ReturnCode.OK
        logging.info("{}".format(self.msg))



class Cmd(BlkInput):
    def __init__(self, stdin: str,
                 level: int = 1):
        super(Cmd, self).__init__(level)
        self.stdin = stdin
        self.stdout = None
        self.stderr = None
        self.shellTrue = False


    def _call(self):
        """Reset default values"""
        self.return_code = ReturnCode.UNDEFINED
        self.stderr = None
        self.stdout = None
        _cmd = None
        if "|" in self.stdin:
            self.shellTrue = True
            _cmd = self.stdin
        else:
            _cmd = shlex.split(self.stdin)
        logging.info("Launching Cmd: {}".format(self.stdin))
        try:
            process = subprocess.Popen(_cmd,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       env=os.environ.copy(),
                                       shell=self.shellTrue)
            self.stdout, self.stderr = process.communicate()
            self.return_code = ReturnCode.OK if process.returncode == 0 else ReturnCode.KO
        except Exception as e:
            self.stderr = str(e)
            self.return_code = ReturnCode.KO
        finally:
            self.shellTrue = False

        logging.info("\tstdin:{}\n\tRC:{}\n\tstdout:{}\n\tstderr:{}".format(
            self.stdin, self.return_code, self.stdout, self.stderr))

    def __repr__(self):
        return '[{}:{}]'.format(self.__class__.__name__,
                                json.dumps(
                                    decode_dict(self.__dict__),
                                    sort_keys=True,
                                    indent=4))


class BlkCmd(object):
    def __init__(self):
        self.blkinputs = list()
        self.return_code = None
        self.maxtime = None
        self.retry_end_on_rc = None
        self.maxtime = 0
        self.sleep = 2
        self.frequency = None
        self.predicate_start_cmd = 0
        self.predicate_stop_cmd = 1

    def add_commands(self, blkinput: BlkInput):
        self.blkinputs.append(blkinput)

    def __call__(self, *args, **kwargs):
        start_block_time = time.time()
        self.return_code = ReturnCode.UNDEFINED
        while self.return_code != self.retry_end_on_rc:
            self.return_code = ReturnCode.UNDEFINED
            for cmd in sorted(self.blkinputs, key=lambda x: x.level):
                cmd()
                rc = cmd.return_code
                if self.return_code == ReturnCode.UNDEFINED:
                    self.return_code = rc
                elif self.return_code == ReturnCode.OK and rc == ReturnCode.OK:
                    pass
                elif self.return_code == ReturnCode.KO and rc == ReturnCode.KO:
                    pass
                else:
                    self.return_code = ReturnCode.UNKNOWN
            current_block_time = time.time()
            if self.maxtime == 0:
                break
            elif (current_block_time - start_block_time) > self.maxtime:
                logging.debug("We reached the end of the loop")
                break
            else:
                logging.info("Sleeping {0} second(s)".format(self.sleep))
                time.sleep(self.sleep)

        return self

    def __repr__(self):
        return '[{}:{}]'.format(self.__class__.__name__,
                                json.dumps(
                                    decode_dict(self.__dict__),
                                    sort_keys=True,
                                    indent=4))

class Job(object):
    def __init__(self, name: str, state: State = State.NOT_READY, trigger: str = None):
        self.name = name
        self.state = state
        self.trigger = trigger

    def __call__(self, trigger_name) -> 'Job':
        logging.debug("Calling {}".format(self.name))
        trigger_blk = getattr(self, trigger_name, None)
        self.state = State.RUNNING
        if trigger_blk:
            rc = trigger_blk()
        else:
            raise RuntimeError("Trigger {0} on {1} does not exist".format(trigger_name, self.name))
        if rc == ReturnCode.OK:
            self.state = State.ENDED_OK
        else:
            self.state = State.FAILED
        return self


    def __repr__(self):
        return '[{}:{}]'.format(self.__class__.__name__,
                                json.dumps(
                                    decode_dict(self.__dict__),
                                    sort_keys=True,
                                    indent=4))




