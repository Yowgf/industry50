import socket

from .message import (Message,
                      decode as decode_msg)

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

def recv_request(sock, print_incoming=False):
    logger.debug("Receiving message from socket {}".format(sock))
    msg_bytes = sock.recv(MAX_MSG_SIZE)
    msg = decode_msg(msg_bytes)
    if print_incoming:
        print(msg)
    return msg
