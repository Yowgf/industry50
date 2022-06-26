from common import log

class Config:
    def __init__(self, server_addr, server_port):
        self.server_addr = server_addr
        self.server_port = server_port

def parse_config(args):
    min_args = 2
    if len(args) < min_args:
        raise ValueError(f"Need at least {min_args} arguments for the program")

    server_addr = args[0]
    server_port = args[1]

    return Config(server_addr, server_port)
