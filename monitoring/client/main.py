import sys

from common import log
from .client import Client
from .config import parse_config

logger = log.logger('industry50-client')

def main():
    try:
        log.parse_config_log_level(sys.argv[1:])

        logger.info("Starting industry50 client.")

        logger.info(f"Program got arguments: {sys.argv[1:]}")

        config = parse_config(sys.argv[1:])
        client = Client(config)
        client.init()
        client.run()

        logger.info("Successfully ran industry50 client. Terminating gracefully.")

    except Exception as e:
        logger.critical(f"Encountered fatal error: {e}", exc_info=True)
