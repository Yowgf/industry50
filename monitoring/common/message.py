import json

from .errors import InvalidMessageError
from common import log

logger = log.logger("industry50-common")

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
        m = {Message.MSGNAME_KEY: self.msgname, Message.MSGID_KEY: self.msgid}
        if self.originid != None:
            m[Message.ORIDINGID_KEY] = self.originid
        if self.destid != None:
            m[Message.DESTID_KEY] = self.destid
        if self.payload != None:
            m[Message.PAYLOAD_KEY] = self.payload
        return json.dumps(m).encode('ascii')

# LEGACY CODE, left here as a message schema reference.
#
# _MESSAGES = [
#     Message("REQ_ADD", "01"),
#     Message("REQ_REM", "02", originid=True),
#     Message("RES_ADD", "03", payload=True),
#     Message("RES_LIST", "04", payload=True),
#     Message("REQ_INF", "05", originid=True, destid=True),
#     Message("RES_INF", "06", originid=True, destid=True, payload=True),
#     Message("ERROR", "07", destid=True, payload=True),
#     Message("OK", "08", destid=True, payload=True),
# ]

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
    stream.decode('ascii')
    if len(stream) == 0:
        raise InvalidMessageError(stream)
    
    m = json.loads(stream)
    if Message.MSGNAME_KEY not in m:
        raise ValueError("Invalid message JSON '{}'. Missing key '{}'".format(
            stream, Message.MSGNAME_KEY))
    if Message.MSGID_KEY not in m:
        raise ValueError("Invalid message JSON '{}'. Missing key '{}'".format(
            stream, Message.MSGID_KEY))
    _ = m[Message.MSGNAME_KEY] # currently not needed
    msgid = m[Message.MSGID_KEY]
    if msgid not in MESSAGE_BUILDERS:
        raise InvalidMessageError(stream)

    originid = None
    destid = None
    payload = None
    if Message.ORIGINID_KEY in m:
        originid = m[Message.ORIGINID_KEY]
    if Message.DESTID_KEY in m:
        destid = m[Message.DESTID_KEY]
    if Message.PAYLOAD_KEY in m:
        payload = m[Message.PAYLOAD_KEY]

    builder = MESSAGE_BUILDERS[msgid]
    return builder(originid=originid, destid=destid, payload=payload)
