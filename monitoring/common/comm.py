import socket

from .message import (Message,
                      decode as decode_msg,
                      MESSAGE_DELIMITER,
)

from . import log

logger = log.logger('common-logger')

MAX_MSG_SIZE = 1024

def new_socket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#    sock.setblocking(False)
    return sock

def send_msg(sock, msg):
    logger.debug("Sending message {} to socket {}".format(msg, sock))
    encoded_msg = msg.encode()
    sock.send(encoded_msg)
    logger.debug("Message sent")

def recv_msg(sock):
    logger.debug("Receiving message from socket {}".format(sock))
    
    num_bytes = 0
    msg_str = ""
    last_char = ""
    while last_char != MESSAGE_DELIMITER and num_bytes < MAX_MSG_SIZE:
        msg_byte = sock.recv(1)
        last_char = msg_byte.decode('ascii')
        msg_str += last_char

    msg = decode_msg(msg_str)
    return msg
