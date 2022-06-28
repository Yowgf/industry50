import threading

from common.comm import (new_socket,
                         recv_request,
                         send_msg)
from common.message import (ReqAdd,
                            ReqRem,
                            ResAdd,
                            ResList,
                            ReqInf,
                            ResInf,
                            Error,
                            Ok,
)
from common.errors import InvalidMessageError
from common import log
from .limits import MAX_CONNECTIONS, MAX_EQUIPMENTS
from .defs import LOGGER_NAME

logger = log.logger(LOGGER_NAME)

class Server:
    def __init__(self, config):
        self._port = config.server_port

    def init(self):
        self._sock = new_socket()

        self._conn_threads = []
        self._conn_threads_mutex = threading.Lock()

        self._free_equipids = ["{:02d}".format(i)
                               # i \in {1, 2, ..., MAX_EQUIPMENTS}
                               for i in range(1, MAX_EQUIPMENTS+1)]
        self._used_equipids = []
        self._equipids_mutex = threading.Lock()

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
        worker = threading.Thread(target=self._recv,
                                  args=(client_sock, client_addr))
        worker.start()
        self._conn_threads.append(worker)

    def _recv(self, client_sock, client_addr):
        tid = threading.get_ident()

        logger.info("({}) Starting communication with client address '{}'".format(
            tid, client_addr))

        try:
            # TODO: this 'while true' is very wrong.
            while True:
                req = recv_request(client_sock, print_incoming=True)
                self._process_request(client_sock, req)
        except ConnectionResetError as e:
            logger.info("Peer reset connection: {}".format(e))
        except InvalidMessageError as e:
            logger.info("Received invalid message: {}".format(e))
        finally:
            client_sock.close()

        logger.info("({}) Ended communication with client address '{}'".format(
            tid, client_addr))

    def _process_request(self, sock, req):
        if isinstance(req, ReqAdd):
            added_equipid = self._add_equipid()
            print("Equipment {} added".format(added_equipid))
            resp = ResAdd(payload=added_equipid)
            send_msg(sock, resp)

            resp = ResList(payload=" ".join([equipid for equipid in
                                             self._used_equipids
                                             if equipid != added_equipid]))
            send_msg(sock, resp)
        elif isinstance(req, ReqRem):
            equipid = req.originid
            self._rmv_equipid(equipid)
        # elif isinstance(req, ResAdd):
        #     pass
        # elif isinstance(req, ResList):
        #     pass
        elif isinstance(req, ReqInf):
            pass
        # elif isinstance(req, ResInf):
        #     pass
        # elif isinstance(req, Error):
        #     pass
        # elif isinstance(req, Ok):
        #     pass
        else:
            raise ValueError("Received unexpected request type: {}".format(req))

    def _add_equipid(self):
        self._equipids_mutex.acquire()
        assert len(self._free_equipids) > 0
        equipid = self._free_equipids.pop(0)
        self._used_equipids.append(equipid)
        self._equipids_mutex.release()
        return equipid

    def _rmv_equipid(self, equipid):
        self._equipids_mutex.acquire()
        assert len(self._used_equipids) > 0
        self._used_equipids.remove(equipid)
        self._free_equipids.append(equipid)
        self._equipids_mutex.release()
