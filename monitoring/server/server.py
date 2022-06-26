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
                self._recycle_finished_sockets()
                self._accept_conn()

        except Exception as e:
            logger.critical(f"Received unexpected error: {e}", exc_info=True)
        finally:
            try:
                self._sock.close()
            except Exception as e:
                logger.error(f"Error trying to close socket: {e}")

    def _recycle_finished_sockets(self):
        dead_thread_idxs = []
        for i in range(len(self._conn_threads)-1, -1, -1):
            if not conn_threads[i].is_alive():
                dead_thread_idxs.append(i)
        for tidx in dead_thread_idxs:
            self._conn_threads.pop(tidx)

    def _accept_conn(self):
        len_client_socks = self._len_client_sock()

        if len_client_socks >= MAX_CONNECTIONS:
            self._refuse_equipment_registration(client_sock)
            self._push_client_sock(client_sock)
        else:
            self._dispatch_worker(client_sock)

    def _push_client_sock(self, sock):
        self._client_socks_mutex.acquire()
        self._client_socks.append(sock)
        self._client_socks_mutex.release()

    def _pop_client_sock(self):
        self._client_socks_mutex.acquire()
        client_sock = self._client_socks.pop()
        len_client_socks = len(self._client_socks)
        self._client_socks_mutex.release()
        return client_sock, len_client_socks

    def _len_client_socks(self):
        self._client_socks_mutex.acquire()
        len_client_socks = len(self._client_socks)
        self._client_socks_mutex.release()
        return len_client_socks

    # TODO: test
    def _refuse_equipment_registration(self, client_sock):
        pass

    def _dispatch_worker(self, client_sock):
        client_socket, client_addr = client_sock.accept()
        logger.info(f"Received connection from address {client_addr}")

        dispatched_worker = threading.Thread(target=self._recv,
                                             args=(client_socket, client_addr))
        self._conn_threads.append(dispatched_worker)

    def _recv(self, client_socket, client_addr):
        try:
            req = recv_request(client_socket, print_incoming=True)
            resp = self._process_request(req)
            send_str(client_socket, resp)
        except InvalidMessageError as e:
            logger.info(f"Received invalid message error: {e}")
        except InvalidSensorError as e:
            logger.info(f"Received invalid sensor error: {e}")
            send_str(client_socket, "invalid sensor")
        except InvalidEquipmentError as e:
            logger.info(f"Received invalid equipment error: {e}")
            send_str(client_socket, "invalid equipment")
