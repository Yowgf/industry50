import socket

from .message import (Message,
                      decode as message_decode)

MAX_MSG_SIZE = 1024

def encode_msg(msg):
    return msg.encode()

def decode_msg(msg_bytes):
    return message_decode(msg_bytes)

def new_socket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setblocking(True)
    return sock

def send_str(sock, msg):
    encoded_msg = encode_msg(msg)
    sock.send(encoded_msg)

def recv_request(sock, print_incoming=False):
    msg_bytes = sock.recv(MAX_MSG_SIZE)
    msg = decode_msg(msg_bytes)
    if print_incoming:
        print(msg)
    return msg
