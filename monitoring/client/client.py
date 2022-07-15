import socket
import select
import sys
import threading

from common.comm import (new_socket,
                         send_msg,
                         MAX_MSG_SIZE)
from common import log
from common.message import (MESSAGE_BUILDERS,
                            EQID_LEN,
                            decode as decode_msg,

                            ReqAdd,
                            ReqRem,
                            ResAdd,
                            ResList,
                            ReqInf,
                            ResInf,
                            Error,
                            Ok,
)
from .defs import LOGGER_NAME
from .command import Command

logger = log.logger(LOGGER_NAME)

class Client:
    CLOSE_CONNECTION = "close connection"
    LIST_EQUIPMENT = "list equipment"
    # request information from <id_equipment>
    REQUEST_INFORMATION = "request information from"

    QUIT = "quit"

    _SELECT_TIMEOUT = 0.01 # Seconds

    def __init__(self, config):
        self._server_addr = config.server_addr
        self._server_port = config.server_port

        self._sock = None
        # _listener is the thread that listens for messages from the server.
        self._equipid = None
        self._other_equipids = []

    def init(self):
        self._connect()
        self._register_equipment()

    def run(self):
        try:
            logger.info("Running industry 5.0 client")

            command_str = ""
            while True:
                incoming = select.select([self._sock], [], [],
                                         self._SELECT_TIMEOUT)
                if incoming[0]:
                    self._process_incoming()

                command_exists = select.select([sys.stdin], [], [],
                                               self._SELECT_TIMEOUT)
                if not command_exists[0]:
                    continue
                else:
                    command_str = sys.stdin.readline()
                    logger.debug("Received command {}".format(command_str))
                    command = self._parse_command(command_str)
                    done = self._process_command(command)
                    if done:
                        break

        except Exception as e:
            logger.critical(f"Received unexpected error: {e}. Terminating client",
                            exc_info=True)
            try:
                self._sock.close()
            except Exception as e:
                logger.error("Error closing socket: {}".format(e))

    def _parse_command(self, command_str):
        command_str = command_str.strip()
        if command_str.startswith(self.CLOSE_CONNECTION):
            return Command(self.CLOSE_CONNECTION)
        elif command_str.startswith(self.LIST_EQUIPMENT):
            return Command(self.LIST_EQUIPMENT)
        elif command_str.startswith(self.REQUEST_INFORMATION):
            args = command_str[len(self.REQUEST_INFORMATION):].lstrip().split(" ")
            return Command(self.REQUEST_INFORMATION, args)
        elif command_str.startswith(self.QUIT):
            return Command(self.QUIT)
        else:
            raise ValueError(f"Invalid command '{command_str}'")

    def _process_command(self, command):
        if command.type == self.QUIT:
            return True
        elif command.type == self.CLOSE_CONNECTION:
            self._close()
            return True
        elif command.type == self.LIST_EQUIPMENT:
            self._list_equipment()
        elif command.type == self.REQUEST_INFORMATION:
            if len(command.args) == 0:
                raise ValueError(f"Malformed command with type '{command.type}'. "+
                                 f"Expected at least one argument.")

            dest_equipid = command.args[0]
            assert len(dest_equipid) == EQUIPID_LEN
            self._request_information(dest_equipid)
        else:
            raise ValueError(f"Malformed command with type '{command.type}'")

    def _process_incoming(self):
        logger.debug("Processing incoming message from server")

        resp_str = self._recv()
        resp_msg = decode_msg(resp_str)
        if resp_msg.MSGID == ReqRem.MSGID:
            removed_equipid = resp_msg.originid
            self._other_equipids.remove(removed_equipid)
            logger.debug("Removed equipment id {}".format(removed_equipid))
        elif resp_msg.MSGID == ResAdd.MSGID:
            new_equipid = resp_msg.equipid()
            self._other_equipids.append(new_equipid)
            logger.debug("Added equipment id {}".format(new_equipid))
            print("Equipment {} added".format(new_equipid))
        elif resp_msg.MSGID == ResList.MSGID:
            self._other_equipids = resp_msg.equipments()
            logger.debug("New list of equipment ids: {}".format(
                self._other_equipids))

    def _register_equipment(self):
        logger.debug("Registering equipment")

        req_builder = MESSAGE_BUILDERS["01"]
        msg = req_builder()
        self._send(msg)

        # Expect to receive message with my ID in the network
        resp_str = self._recv()
        resp_msg = decode_msg(resp_str)

        if resp_msg.msgid == Error.MSGID:
            print(resp_msg.error())
        elif resp_msg.msgid == ResAdd.MSGID:
            self._equipid = resp_msg.payload
            print("New ID: {}".format(self._equipid))

            resp_str = self._recv()
            resp_msg = decode_msg(resp_str)
            self._other_equipids = resp_msg.equipments()

    def _list_equipment(self):
        print(" ".join(self._other_equipids))

    # TODO
    def _request_information(self, destid):
        builder = MESSAGE_BUILDERS["05"]
        msg = builder(originid=TODO)
        self._send(msg)

    def _send(self, msg):
        send_msg(self._sock, msg)

    def _recv(self):
        bs = self._sock.recv(MAX_MSG_SIZE)
        return bs

    def _connect(self):
        logger.info(f"Connecting client to {self._server_addr}:{self._server_port}")
        self._sock = new_socket()
        self._sock.connect((self._server_addr, self._server_port))
        logger.info(f"Established connection to {self._server_addr}:"+
                    f"{self._server_port}")

    def _close(self):
        logger.info(f"Closing connection to {self._server_addr}:{self._server_port}")

        req_builder = MESSAGE_BUILDERS["02"]
        remove_equip_msg = req_builder(originid=self._equipid)
        self._send(remove_equip_msg)

        resp_str = self._recv()
        resp_msg = decode_msg(resp_str)
        if resp_msg.msgid == Error.MSGID:
            print(resp_msg.error())
        elif resp_msg.msgid == Ok.MSGID:            
            print(resp_msg.description())

        self._sock.close()
