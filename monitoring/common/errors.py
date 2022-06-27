class InvalidMessageError(Exception):
    def __init__(self, msg):
        super().__init__(f"Invalid message '{msg}'")
