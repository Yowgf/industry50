import threading

from common.comm import new_socket
from common import log
from .limits import MAX_CONNECTIONS
from .defs import LOGGER_NAME

logger = log.logger(LOGGER_NAME)

class Server:
    def __init__(self, config):
        self._port = config.server_port

    def init(self):
        self._sock = new_socket()

        self._conn_threads = []
        self._conn_threads_mutex = threading.Lock()

    def run(self):
        # bind "" == bind INADDR_ANY
        self._sock.bind(("", self._port))
        self._sock.listen(MAX_CONNECTIONS)

        try:
            while True:
                self._accept_conn()

        except Exception as e:
            logger.critical(f"Received unexpected error: {e}", exc_info=True)
        finally:
            try:
                self._sock.close()
                raise
            except Exception as e:
                logger.error(f"Error trying to close socket: {e}")

    def _accept_conn(self):
        client_sock, client_addr = self._sock.accept()
        logger.info(f"Received connection from address {client_addr}")

        len_conn_threads = self._len_conn_threads()
        if len_conn_threads >= MAX_CONNECTIONS:
            self._refuse_equipment_registration(client_sock, client_addr)
        else:
            self._dispatch_worker(client_sock, client_addr)

    def _push_conn_thread(self, sock):
        self._conn_threads_mutex.acquire()
        self._conn_threads.append(sock)
        self._conn_threads_mutex.release()

    def _pop_conn_thread(self):
        self._conn_threads_mutex.acquire()
        conn_thread = self._conn_threads.pop()
        len_conn_threads = len(self._conn_threads)
        self._conn_threads_mutex.release()
        return conn_thread, len_conn_threads

    def _len_conn_threads(self):
        self._conn_threads_mutex.acquire()
        len_conn_threads = len(self._conn_threads)
        self._conn_threads_mutex.release()
        return len_conn_threads

    # TODO: test
    def _refuse_equipment_registration(self, client_sock, client_addr):
        pass

    def _dispatch_worker(self, client_sock, client_addr):
        logger.info("Dispatching worker for address '{}'".format(client_addr))
        dispatched_worker = threading.Thread(target=self._recv,
                                             args=(client_sock, client_addr))
        self._conn_threads.append(dispatched_worker)

    def _recv(self, client_sock, client_addr):
        tid = threading.get_ident()

        logger.info("({}) Starting communication with client address '{}'".format(
            tid, client_addr))

        try:
            while True:
                req = recv_request(client_sock, print_incoming=True)
                resp = self._process_request(req)
                send_str(client_sock, resp)
        finally:
            client_sock.close()

        logger.info("({}) Ended communication with client address '{}'".format(
            tid, client_addr))
