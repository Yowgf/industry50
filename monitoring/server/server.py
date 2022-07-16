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

        # Used as global mutex for client_socks and free_equipids objects
        self._salt_mutex = threading.Lock()

        # _client_socks is map equipid -> socket
        self._client_socks = {}

        self._free_equipids = ["{:02d}".format(i)
                               # i \in {1, 2, ..., MAX_EQUIPMENTS}
                               for i in range(1, MAX_EQUIPMENTS+1)]

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
        worker = threading.Thread(target=self._recv,
                                  args=(client_sock, client_addr))
        worker.start()

    def _recv(self, client_sock, client_addr):
        tid = threading.get_ident()

        logger.info("({}) Starting communication with client address '{}'".format(
            tid, client_addr))

        equipid = None
        try:
            done = False
            while not done:
                req = recv_request(client_sock, print_incoming=True)
                done, new_equipid = self._process_request(client_sock, req)
                if equipid == None:
                    equipid = new_equipid
        except ConnectionResetError as e:
            logger.info(f"({tid}) Peer reset connection: {e}")
            self._cleanup_sock(equipid, client_sock)
        except InvalidMessageError as e:
            logger.info(f"({tid}) Received invalid message: {e}")
            self._cleanup_sock(equipid, client_sock)
        except Exception as e:
            logger.error(f"({tid}) Caught unexpected exception: {e}",
                            exc_info=True)
            self._cleanup_sock(equipid, client_sock)

        logger.info("({}) Ended communication with client address '{}'".format(
            tid, client_addr))

    def _process_request(self, sock, req):
        if isinstance(req, ReqAdd):
            num_open_connections = self._num_open_connections()
            if num_open_connections >= MAX_CONNECTIONS:
                resp = Error(destid="{}".format(num_open_connections),
                             payload=CODE_EQUIPMENT_LIMIT_EXCEEDED.id)
                send_msg(sock, resp)
                return True, None

            added_equipid = self._add_equipid(sock)
            print("Equipment {} added".format(added_equipid))
            resp = ResAdd(payload=added_equipid)
            self._broadcast(resp)

            equipids = self._get_equipids()
            equipids.remove(added_equipid)
            resp = ResList(payload=" ".join(equipids))
            send_msg(sock, resp)

            return False, added_equipid
        elif isinstance(req, ReqRem):
            equipid = req.originid
            equip_exists = self._rmv_equipid(equipid)
            if not equip_exists:
                resp = Error(payload=CODE_EQUIPMENT_NOT_FOUND.id)
                send_msg(sock, resp)
            else:
                resp = Ok(destid=equipid, payload=CODE_SUCCESSFUL_REMOVAL.id)
                send_msg(sock, resp)
                self._cleanup_sock(equipid, sock)

            resp_rem = ReqRem(originid=equipid)
            self._broadcast(resp_rem)

            return True, None
        elif isinstance(req, ReqInf):
            originid = req.originid
            destid = req.destid
            equip_exists = self._equipid_exists(originid)
            if originid == destid or not equip_exists:
                print("Equipment {} not found".format(originid))
                resp = Error(destid=originid,
                             payload=CODE_SOURCE_EQUIPMENT_NOT_FOUND.id)
                send_msg(sock, resp)
            else:
                equip_exists = self._equipid_exists(destid)
                if not equip_exists:
                    print("Equipment {} not found".format(destid))
                    resp = Error(destid=destid,
                                 payload=CODE_TARGET_EQUIPMENT_NOT_FOUND.id)
                    send_msg(sock, resp)
                else:
                    self._send(destid, req)
        elif isinstance(req, ResInf):
            originid = req.originid
            destid = req.destid
            equip_exists = self._equipid_exists(originid)
            if originid == destid or not equip_exists:
                print("Equipment {} not found".format(originid))
                resp = Error(destid=originid,
                             payload=CODE_SOURCE_EQUIPMENT_NOT_FOUND.id)
                send_msg(sock, resp)
            else:
                equip_exists = self._equipid_exists(destid)
                if not equip_exists:
                    print("Equipment {} not found".format(destid))
                    resp = Error(destid=destid,
                                 payload=CODE_TARGET_EQUIPMENT_NOT_FOUND.id)
                    send_msg(sock, resp)
                else:
                    self._send(destid, req)
        else:
            raise ValueError("Received unexpected request type: {}".format(req))

        return False, None

    def _send(self, equipid, msg):
        self._salt_mutex.acquire()
        if equipid not in self._client_socks:
            logger.error(f"No socket associated with equipment id "+
                         f"'{equipid}'")
            self._salt_mutex.release()
            return
        try:
            client_sock = self._client_socks[equipid]
            send_msg(client_sock, msg)
        except Exception as e:
            logger.error(f"Error sending message to socket for equipment "+
                         f"id {equipid}: {e}")
        finally:
            self._salt_mutex.release()

    def _broadcast(self, msg, except_equipid=None):
        self._salt_mutex.acquire()
        logger.debug("Broadcasting message: {}".format(msg))
        for equipid in self._client_socks:
            if except_equipid == equipid:
                continue
            logger.debug("Sending message to socket {}".format(equipid))
            send_msg(self._client_socks[equipid], msg)
        logger.debug("Successfully performed broadcast")
        self._salt_mutex.release()

    def _cleanup_sock(self, equipid, sock):
        try:
            self._rmv_equipid(equipid)
            sock.close()
        except Exception as e:
            logger.error("Error cleaning up: {}".format(e))

    def _add_equipid(self, client_sock):
        self._salt_mutex.acquire()
        assert len(self._free_equipids) > 0
        equipid = self._free_equipids.pop(0)
        self._client_socks[equipid] = client_sock
        self._salt_mutex.release()
        return equipid

    def _rmv_equipid(self, equipid):
        self._salt_mutex.acquire()

        if equipid not in self._client_socks:
            self._salt_mutex.release()
            return False

        assert len(self._client_socks) > 0
        self._client_socks.pop(equipid)
        self._free_equipids.append(equipid)
        logger.debug(f"Equipment id {equipid} removed")

        self._salt_mutex.release()

        return True

    def _equipid_exists(self, equipid):
        self._salt_mutex.acquire()
        exists = equipid in self._client_socks
        self._salt_mutex.release()
        return exists

    def _get_equipids(self):
        self._salt_mutex.acquire()
        equipids = list(self._client_socks.keys())
        self._salt_mutex.release()
        return equipids

    def _num_open_connections(self):
        self._salt_mutex.acquire()
        len_client_socks = len(self._client_socks)
        self._salt_mutex.release()
        return len_client_socks
