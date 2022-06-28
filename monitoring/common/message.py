import json

from .errors import InvalidMessageError
from common import log

logger = log.logger("industry50-common")

EQID_LEN = 2

class Message:
    MSGNAME_KEY = "type"
    MSGID_KEY = "id"
    ORIGINID_KEY = "originid"
    DESTID_KEY = "destid"
    PAYLOAD_KEY = "payload"

    def __init__(self, msgname, msgid, originid=None,
                 destid=None, payload=None):
        self.msgname = msgname
        self.msgid = msgid
        self.originid = originid
        self.destid = destid
        self.payload = payload

    def encode(self):
        m = "{}".format(self.msgid)
        if self.originid == None:
            m += "-"
        else:
            m += str(self.originid)
        if self.destid == None:
            m += "-"
        else:
            m += str(self.destid)
        if self.payload == None:
            m += str(self.payload)
        else:
            m += "-"
        return m.encode('ascii')

class ReqAdd(Message):
    def __init__(self, originid=None, destid=None, payload=None):
        logger.debug("Constructing message of type req add")
        super().__init__("REQ_ADD", "01")

class ReqRem(Message):
    def __init__(self, originid=None, destid=None, payload=None):
        logger.debug("Constructing message of type req rem")
        super().__init__("REQ_REM", "02", originid=originid)

class ResAdd(Message):
    def __init__(self, originid=None, destid=None, payload=None):
        logger.debug("Constructing message of type res add")
        super().__init__("RES_ADD", "03", payload=payload)

class ResList(Message):
    def __init__(self, originid=None, destid=None, payload=None):
        logger.debug("Constructing message of type res list")
        super().__init__("RES_LIST", "04", payload=payload)

class ReqInf(Message):
    def __init__(self, originid=None, destid=None, payload=None):
        logger.debug("Constructing message of type req inf")
        super().__init__("REQ_INF", "05", originid=originid, destid=destid)

class ResInf(Message):
    def __init__(self, originid=None, destid=None, payload=None):
        logger.debug("Constructing message of type res inf")
        super().__init__("RES_INF", "06", originid=originid, destid=destid,
                         payload=payload)

class Error(Message):
    def __init__(self, originid=None, destid=None, payload=None):
        logger.debug("Constructing message of type error")
        super().__init__("ERROR", "07", destid=destid, payload=payload)

class Ok(Message):
    def __init__(self, originid=None, destid=None, payload=None):
        logger.debug("Constructing message of type ok")
        super().__init__("OK", "08", destid=destid, payload=payload)

MESSAGE_BUILDERS = {
    "01": ReqAdd,
    "02": ReqRem,
    "03": ResAdd,
    "04": ResList,
    "05": ReqInf,
    "06": ResInf,
    "07": Error,
    "08": Ok,
}

def decode(stream):
    stream = stream.decode('ascii')
    if len(stream) == 0:
        raise InvalidMessageError(stream)

    def component(stream, begin, offset=None):
        ss = None
        if stream[begin] == "-":
            begin += 1
        else:
            if offset == None:
                ss = stream[begin:]
                begin = len(stream)
            else:
                ss = stream[begin:begin+offset]
                begin += offset
        return ss, begin

    stream_pos = 0
    msgid, stream_pos = component(stream, stream_pos, EQID_LEN)
    originid, stream_pos = component(stream, stream_pos, EQID_LEN)
    destid, stream_pos = component(stream, stream_pos, EQID_LEN)
    payload, stream_pos = component(stream, stream_pos)

    builder = MESSAGE_BUILDERS[msgid]
    return builder(originid=originid, destid=destid, payload=payload)
