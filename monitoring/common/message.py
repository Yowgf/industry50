import json

from .errors import InvalidMessageError
from .code import (CODE_EQUIPMENT_NOT_FOUND,
                   CODE_SOURCE_EQUIPMENT_NOT_FOUND,
                   CODE_TARGET_EQUIPMENT_NOT_FOUND,
                   CODE_EQUIPMENT_LIMIT_EXCEEDED,
                   CODE_SUCCESSFUL_REMOVAL,
)
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
        if self.payload == None or self.payload == "":
            m += "-"
        else:
            m += str(self.payload)
        return m.encode('ascii')

class ReqAdd(Message):
    MSG_NAME = "REQ_ADD"
    MSGID = "01"
    def __init__(self, originid=None, destid=None, payload=None):
        logger.debug("Constructing message of type req add")
        super().__init__(self.MSG_NAME, self.MSGID)

class ReqRem(Message):
    MSG_NAME = "REQ_REM"
    MSGID = "02"
    def __init__(self, originid=None, destid=None, payload=None):
        logger.debug("Constructing message of type req rem. Originid: {}".format(
            originid))
        super().__init__(self.MSG_NAME, self.MSGID, originid=originid)

class ResAdd(Message):
    MSG_NAME = "RES_ADD"
    MSGID = "03"
    def __init__(self, originid=None, destid=None, payload=None):
        logger.debug("Constructing message of type res add. Payload: {}".format(
            payload))
        super().__init__(self.MSG_NAME, self.MSGID, payload=payload)

class ResList(Message):
    MSG_NAME = "RES_LIST"
    MSGID = "04"
    def __init__(self, originid=None, destid=None, payload=None):
        logger.debug("Constructing message of type res list. Payload: {}".format(
            payload))
        super().__init__(self.MSG_NAME, self.MSGID, payload=payload)

    def equipments(self):
        if self.payload == None:
            return []
        return self.payload.split(" ")

class ReqInf(Message):
    MSG_NAME = "REQ_INF"
    MSGID = "05"
    def __init__(self, originid=None, destid=None, payload=None):
        logger.debug("Constructing message of type req inf. originid={} destid={}".
                     format(originid, destid))
        super().__init__(self.MSG_NAME, self.MSGID, originid=originid, destid=destid)

class ResInf(Message):
    MSG_NAME = "RES_INF"
    MSGID = "06"
    def __init__(self, originid=None, destid=None, payload=None):
        logger.debug("Constructing message of type res inf. originid={originid} "+
                     f"destid={destid} payload={payload}")
        super().__init__(self.MSG_NAME, self.MSGID, originid=originid, destid=destid,
                         payload=payload)

class Error(Message):
    MSG_NAME = "ERROR"
    MSGID = "07"

    def __init__(self, originid=None, destid=None, payload=None):
        logger.debug(f"Constructing message of type error. destid={destid} "+
                     "payload={payload}")
        super().__init__(self.MSG_NAME, self.MSGID, destid=destid, payload=payload)

    def error(self):
        if self.payload == "01":
            return "Equipment not found"
        elif self.payload == "02":
            return "Source equipment not found"
        elif self.payload == "03":
            return "Target equipment not found"
        elif self.payload == "04":
            return "Equipment limit exceeded"
        else:
            raise ValueError(f"Unable to decode error for payload '{self.payload}'")

class Ok(Message):
    MSG_NAME = "OK"
    MSGID = "08"

    CODES = {
        CODE_SUCCESSFUL_REMOVAL.id: CODE_SUCCESSFUL_REMOVAL,
    }

    def __init__(self, originid=None, destid=None, payload=None):
        logger.debug("Constructing message of type ok")
        super().__init__(self.MSG_NAME, self.MSGID, destid=destid, payload=payload)

    def description(self):
        return self.CODES[self.payload].description

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

    logger.debug(f"Decoding stream '{stream}'")

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
