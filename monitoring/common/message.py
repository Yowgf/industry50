import json

from .errors import InvalidMessageError

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

    def decode(stream):
        if len(stream) == 0:
            raise InvalidMessageError(stream)

        m = json.loads(stream)
        if Message.MSGNAME_KEY not in m:
            raise ValueError("Invalid message JSON '{}'. Missing key '{}'".format(
                stream, Message.MSGNAME_KEY))
        if Message.MSGID_KEY not in m:
            raise ValueError("Invalid message JSON '{}'. Missing key '{}'".format(
                stream, Message.MSGID_KEY))
        msgname = m[Message.MSGNAME_KEY]
        msgid = m[Message.MSGID_KEY]
        originid = None
        destid = None
        payload = None
        if Message.ORIGINID_KEY in m:
            originid = m[Message.ORIGINID_KEY]
        if Message.DESTID_KEY in m:
            destid = m[Message.DESTID_KEY]
        if Message.PAYLOAD_KEY in m:
            payload = m[Message.PAYLOAD_KEY]
        return Message(msgname, msgid, originid=originid, destid=destid,
                       payload=payload)

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

def req_add():
    return Message("REQ_ADD", "01")

def req_rem(originid):
    return Message("REQ_REM", "02", originid=originid)

def res_add(payload):
    return Message("RES_ADD", "03", payload=payload)

def res_list(payload):
    return Message("RES_LIST", "04", payload=payload)

def req_inf(originid, destid):
    return Message("REQ_INF", "05", originid=originid, destid=destid)

def res_inf(originid, destid, payload):
    return Message("RES_INF", "06", originid=originid, destid=destid,
                   payload=payload)

def error(destid, payload):
    return Message("ERROR", "07", destid=destid, payload=payload)

def ok(destid, payload):
    return Message("OK", "08", destid=destid, payload=payload)

MESSAGE_BUILDERS = {
    "01": req_add,
    "02": req_rem,
    "03": res_add,
    "04": res_list,
    "05": req_inf,
    "06": res_inf,
    "07": error,
    "08": ok,
}
