import socket

from .message import (Message,
                      decode as decode_msg)

MAX_MSG_SIZE = 1024

def new_socket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setblocking(True)
    return sock

def send_msg(sock, msg):
    encoded_msg = msg.encode()
    sock.send(encoded_msg)

def recv_request(sock, print_incoming=False):
    msg_bytes = sock.recv(MAX_MSG_SIZE)
    msg = decode_msg(msg_bytes)
    if print_incoming:
        print(msg)
    return msg
