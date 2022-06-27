import socket

from common.comm import new_socket, send_str
from common import log
from common.message import MESSAGE_BUILDERS
from .defs import LOGGER_NAME
from .command import Command

logger = log.logger(LOGGER_NAME)

class Client:
    CLOSE_CONNECTION = "close connection"
    LIST_EQUIPMENT = "list equipment"
    # request information from <id_equipment>
    REQUEST_INFORMATION = "request information from"

    QUIT = "quit"

    def __init__(self, config):
        self._server_addr = config.server_addr
        self._server_port = config.server_port

        self._sock = None

        self._equipments_in_network = []

    def init(self):
        self._connect()
        self._register_equipment()

    def run(self):
        try:
            command_str = ""
            while True:
                command_str = input()
                
                command = self._parse_command(command_str)
                if command.type == self.QUIT:
                    break
                
                self._process_command(command)

        except Exception as e:
            logger.critical(f"Received unexpected error: {e}. Terminating client",
                            exc_info=True)

            try:
                self._close()
            except Exception as e:
                logger.error("Error closing connection: {}".format(e))

    def _parse_command(self, command_str):
        command_str = command_str.strip()
        if command_str.startswith(self.CLOSE_CONNECTION):
            return Command(self.CLOSE_CONNECTION)
        elif command_str.startswith(self.LIST_EQUIPMENT):
            return Command(self.LIST_EQUIPMENT)
        elif command_str.startswith(self.REQUEST_INFORMATION):
            return Command(self.REQUEST_INFORMATION)
        elif command_str.startswith(self.QUIT):
            return Command(self.QUIT)
        else:
            raise ValueError(f"Invalid command '{command_str}'")

    def _process_command(self, command):
        if command.type == self.CLOSE_CONNECTION:
            self._close()
        elif command.type == self.LIST_EQUIPMENT:
            pass
        elif command.type == self.REQUEST_INFORMATION:
            pass
        else:
            raise ValueError(f"Malformed command with type '{command.type}'")

    def _register_equipment(self):
        builder = MESSAGE_BUILDERS["01"]
        msg = builder()
        self._send(msg)

    def _send(self, msg):
        send_str(self._sock, msg)

    def _connect(self):
        logger.info(f"Connecting client to {self._server_addr}:{self._server_port}")
        self._sock = new_socket()
        self._sock.connect((self._server_addr, self._server_port))
        logger.info(f"Established connection to {self._server_addr}:"+
                    f"{self._server_port}")

    def _close(self):
        logger.info(f"Closing connection to {self._server_addr}:{self._server_port}")
        self._sock.close()
