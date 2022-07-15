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
from common.code import (CODE_EQUIPMENT_NOT_FOUND,
                         CODE_SOURCE_EQUIPMENT_NOT_FOUND,
                         CODE_TARGET_EQUIPMENT_NOT_FOUND,
                         CODE_EQUIPMENT_LIMIT_EXCEEDED,

                         CODE_SUCCESSFUL_REMOVAL,
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

        # _client_socks is map equipid -> socket
        self._client_socks = {}
        self._client_socks_mutex = threading.Lock()

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
            except Exception as e:
                logger.error(f"Error trying to close socket: {e}")

    def _accept_conn(self):
        client_sock, client_addr = self._sock.accept()
        logger.info(f"Received connection from address {client_addr}")

        self._dispatch_worker(client_sock, client_addr)

    def _dispatch_worker(self, client_sock, client_addr):
        logger.info("Dispatching worker for address '{}'".format(client_addr))
        sockid = self._push_client_sock(client_sock)
        worker = threading.Thread(target=self._recv,
                                  args=(sockid, client_sock, client_addr))
        worker.start()

    def _recv(self, sockid, client_sock, client_addr):
        tid = threading.get_ident()

        logger.info("({}) Starting communication with client address '{}'".format(
            tid, client_addr))

        try:
            done = False
            while not done:
                req = recv_request(client_sock, print_incoming=True)
                done = self._process_request(sockid, client_sock, req)
        except ConnectionResetError as e:
            logger.info("Peer reset connection: {}".format(e))
            self._cleanup_sock(sockid, client_sock)
            try:
                self._pop_client_sock(sockid)
                client_sock.close()
            except Exception as e:
                logger.error("Error cleaning up: {}".format(e))
        except InvalidMessageError as e:
            logger.info("Received invalid message: {}".format(e))
            self._cleanup_sock(sockid, client_sock)
        except Exception as e:
            logger.critical("Caught unexpected exception: {}".format(e),
                            exc_info=True)

        logger.info("({}) Ended communication with client address '{}'".format(
            tid, client_addr))

    def _process_request(self, sockid, sock, req):
        if isinstance(req, ReqAdd):
            len_client_socks = self._len_client_socks()
            if len_client_socks >= MAX_CONNECTIONS:
                resp = Error(destid="{}".format(len_client_socks),
                             payload=CODE_EQUIPMENT_LIMIT_EXCEEDED.id)
                send_msg(sock, resp)
                return True

            added_equipid = self._add_equipid()
            print("Equipment {} added".format(added_equipid))
            resp = ResAdd(payload=added_equipid)
            self._broadcast(resp)

            resp = ResList(payload=" ".join([equipid for equipid in
                                             self._used_equipids
                                             if equipid != added_equipid]))
            send_msg(sock, resp)
        elif isinstance(req, ReqRem):
            equipid = req.originid
            equip_exists = self._rmv_equipid(equipid)
            if not equip_exists:
                resp = Error(payload=CODE_EQUIPMENT_NOT_FOUND.id)
                send_msg(sock, resp)
            else:
                resp = Ok(destid=equipid, payload=CODE_SUCCESSFUL_REMOVAL.id)
                send_msg(sock, resp)
                self._cleanup_sock(sockid, sock)

            resp_rem = ReqRem(originid=equipid)
            self._broadcast(resp_rem)

            return True

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

        return False

    def _broadcast(self, msg, except_sockid=None):
        self._client_socks_mutex.acquire()
        logger.debug("Broadcasting message: {}".format(msg))
        for sockid in self._client_socks:
            if except_sockid == sockid:
                continue
            logger.debug("Sending message to socket {}".format(sockid))
            send_msg(self._client_socks[sockid], msg)
        logger.debug("Successfully performed broadcast")
        self._client_socks_mutex.release()

    def _cleanup_sock(self, sockid, sock):
        try:
            self._pop_client_sock(sockid)
            sock.close()
        except Exception as e:
            logger.error("Error cleaning up: {}".format(e))

    def _add_equipid(self):
        self._equipids_mutex.acquire()
        assert len(self._free_equipids) > 0
        equipid = self._free_equipids.pop(0)
        self._used_equipids.append(equipid)
        self._equipids_mutex.release()
        return equipid

    def _rmv_equipid(self, equipid):
        self._equipids_mutex.acquire()

        if equipid not in self._used_equipids:
            self._equipids_mutex.release()
            return False

        assert len(self._used_equipids) > 0
        self._used_equipids.remove(equipid)
        self._free_equipids.append(equipid)

        self._equipids_mutex.release()

        return True

    def _push_client_sock(self, client_sock):
        self._client_socks_mutex.acquire()
        sockid = 0
        while sockid in self._client_socks:
            sockid += 1
        self._client_socks[sockid] = client_sock
        self._client_socks_mutex.release()
        return sockid

    def _pop_client_sock(self, sockid):
        self._client_socks_mutex.acquire()
        client_sock = self._client_socks.pop(sockid)
        self._client_socks_mutex.release()
        return client_sock

    def _len_client_socks(self):
        self._client_socks_mutex.acquire()
        len_client_socks = len(self._client_socks)
        self._client_socks_mutex.release()
        return len_client_socks
