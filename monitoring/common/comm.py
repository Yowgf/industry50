import socket

def new_socket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setblocking(True)
    return sock

def send_str(sock, msg_str):
    encoded_msg = encode_msg(msg_str)
    sock.send(encoded_msg)

def recv_request(sock, print_incoming=False):
    msg_bytes = sock.recv(MAX_MSG_SIZE)
    msg = decode_msg(msg_bytes)
    if print_incoming:
        print(msg)
    decoded_request = decode_request(msg)
    return decoded_request
