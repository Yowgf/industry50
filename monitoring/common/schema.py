class Message:
    def __init__(self, message_name, msgid, originid=None,
                 destid=None, payload=None):
        self.message_name = message_name
        self.msgid = msgid
        self.originid = originid
        self.destid = destid
        self.payload = payload

MESSAGES = [
    Message("REQ_ADD", "01"),
    Message("REQ_REM", "02", originid=True),
    Message("RES_ADD", "03", payload=True),
    Message("RES_LIST", "04", payload=True),
    Message("REQ_INF", "05", originid=True, destid=True),
    Message("RES_INF", "06", originid=True, destid=True, payload=True),
    Message("ERROR", "07", destid=True, payload=True),
    Message("OK", "08", destid=True, payload=True),
]
