import sys

from common import log
from .server import Server
from .config import parse_config

logger = log.logger('industry50-server')

def main():
    try:
        log.parse_config_log_level(sys.argv[1:])

        logger.info("Starting industry50 server.")

        logger.info(f"Program got arguments: {sys.argv[1:]}")

        config = parse_config(sys.argv[1:])
        server = Server(config)
        server.init()
        server.run()

        logger.info("Successfully ran industry50 server. Terminating gracefully.")

    except Exception as e:
        logger.critical(f"Encountered fatal error: {e}", exc_info=True)
