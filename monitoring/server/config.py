from common import log

class Config:
    def __init__(self, server_port):
        self.server_port = server_port

def parse_config(args):
    min_args = 1
    if len(args) < min_args:
        raise ValueError(f"Need at least {min_args} arguments for the program")

    server_port = args[0]

    return Config(server_port)
