#! /usr/bin/python
#
#
#

import logging
import psycopg2
import time
import pickle
from multiprocessing import Process, Queue, get_logger
import os

import BMP

Q_INSERT_RAW = """INSERT INTO raw_log
    (ts, bmp_src, bgp_src, bgp_data)
    VALUES
    (%s, %s, %s, %s)"""

Q_FIND_PATH = """SELECT id FROM adj_rib_in
    WHERE
        bmp_src = %s
        AND neighbor_addr = %s
        AND prefix = %s
        AND %s >= valid_from AND %s < valid_to"""

Q_INVALIDATE_PATH = """UPDATE adj_rib_in SET
    valid_to = %s
    WHERE id = %s"""

Q_INVALIDATE_NEIGHBOR = """UPDATE adj_rib_in
    SET
        valid_to = %s
    WHERE
        bmp_src = %s AND
        neighbor_addr = %s AND
        valid_to > %s"""

Q_INSERT_PATH = """INSERT INTO adj_rib_in
    (
        valid_from,
        valid_to,
        bmp_src,
        neighbor_addr,
        neighbor_as,
        next_hop,
        lpref,
        origin,
        med,
        prefix,
        aspath,
        communities
    ) VALUES (
        %(valid_from)s,
        %(valid_to)s,
        %(bmp_src)s,
        %(neighbor_addr)s,
        %(neighbor_as)s,
        %(next_hop)s,
        %(lpref)s,
        %(origin)s,
        %(med)s,
        %(prefix)s,
        %(aspath)s,
        %(communities)s
    )"""

DUMP_FILE_PATH = "/tmp/bmpd.dump"


class Store:


    _logger = None
    _dbproc = None
    _msg_queues = None
    _data_queue = None
    _proc_id = None

    conn = None
    time_select = 0.0
    time_update = 0.0
    time_insert = 0.0
    nmsg = 0
    nmsg_q = 0
    npref_add = 0
    last_npref_add = 0
    npref_del = 0
    last_npref_del = 0
    last_ts = None
    dump_file = None


    def __init__(self, nproc=1):
        """ Create store instance

            The parameter nproc determines how many database processes to
            start.
        """

        self._dbproc = {}
        self._logger = logging.getLogger(self.__class__.__name__)

        # Create message queue for transport of received BMP messages from main
        # process to database process. Then initialize database process.
        self._data_queue = Queue()
        self._msg_queues = {}
        for i in range(nproc):
            self._msg_queues[i] = Queue()
            self._proc_id = i
            dbproc = Process(target=self._init_dbproc, name="dbproc")
            dbproc.start()
            self._dbproc[i] = dbproc

        self._proc_id = None

        # open file to pickle unknown data to
        try:
            self.dump_file = open(DUMP_FILE_PATH, 'a')
        except IOError, e:
            self._logger.error("Could not open dump file: %s" % e.message)


    def store(self, msg):
        """ Store message

            Place message in queue for transport to database process.
        """

        if self.nmsg_q % 100 == 0:
            self._logger.debug("Placed %d messages in queue. Approx. queue length: %d" %
                (self.nmsg_q, self._data_queue.qsize()))
            if self._data_queue.qsize() > 20000:
                 self._logger.info("Queue length over 20000. Pausing receiver for 10 seconds.")
                 time.sleep(10)

        msg._logger = None
        self._data_queue.put(msg)
        self.nmsg_q += 1


    def close(self):
        """ Close store

            Tries to close database processes as nicely as possible
        """

        # send message to processes
        for key in self._dbproc:
            self._logger.info("Sending close message to process %d" % key)
            self._msg_queues[key].put('close')

        while len(self._dbproc) > 0:
            to_del = []

            for key in self._dbproc:
                self._dbproc[key].join(1)
                if not self._dbproc[key].is_alive():
                    self._logger.info("Process %d dead")
                    to_del.append(key)
                else:
                    self._logger.info("Join of process %d timed out")

            for key in to_del:
                del self._dbproc[key]


    def _init_dbproc(self):
        """ Initialize the database process
        """

        # create new logger
        logging.basicConfig()
        self._logger = logging.getLogger("%s-%d" % (self.__class__.__name__, self._proc_id))
        self._logger.setLevel(logging.DEBUG)

        self._logger.debug('Starting database process, pid %d.' % os.getpid())

        # open database connection
        self.conn = psycopg2.connect(host='127.0.0.1', user='bmp', password='bmp', database='bmp')
        self.curs = self.conn.cursor()

        # fetch element from queue, forever
        n = 0
        while True:

            # Any message in message queue?
            # Perhaps this should not be done every iteration?
            if not self._msg_queues[self._proc_id].empty():
                msg = self._msg_queues[self._proc_id].get()
                if msg == 'close':
                    break
                else:
                    self._logger.warning("Received unknown message %s" % msg)

            # Store data from data queue
            self._store_any(self._data_queue.get())
            n += 1

            if n % 100 == 0:
                self._logger.debug("Fetched %d messages from queue. Approx. queue length %d." %
                    (n, self._data_queue.qsize()))

        # infinite loop ended - clean up


    def _store_any(self, msg):
        # save BMP message

        if msg.msg_type == BMP.MSG_TYPE_ROUTE_MONITORING:
            self.store_route_mon(msg)

        elif msg.msg_type == BMP.MSG_TYPE_STATISTICS_REPORT:
            self.store_stat_report(msg)

        elif msg.msg_type == BMP.MSG_TYPE_PEER_DOWN_NOTIFICATION:
            self.store_peer_down(msg)

        else:
            self.store_other(msg)

        self.nmsg += 1


    def store_route_mon(self, msg):
        """ Store a route monitoring message
        """

        if self.last_ts is None:
            self.last_ts = time.time()

        # save raw BGP packet
        self.curs.execute(Q_INSERT_RAW,
            (msg.time, msg.source.host, msg.peer_address, psycopg2.Binary(msg.raw_payload)))

        #
        # update adj_rib_in table
        #

        # withdrawals
        for pref in msg.update.withdraw:
            self._logger.debug("Withdrawal of prefix %s" % pref)
            self.npref_del += 1

            start_select = time.time()
            self.curs.execute(Q_FIND_PATH,
                (msg.source.host, msg.peer_address, pref.prefix, msg.time, msg.time))
            self.time_select += time.time() - start_select
            if self.curs.rowcount > 0:
                row = self.curs.fetchone()
                try:
                    start_update = time.time()
                    self.curs.execute(Q_INVALIDATE_PATH, (msg.time, row[0]))
                    self.time_update += time.time() - start_update
                except psycopg2.Error, e:
                    self._logger.error("Unable to withdraw prefix %s (id %d) in message %s: %s " %
                        (pref, row[0], msg, e))
            else:
                # According to the BMP draft (at least versions up to 05)
                # section "Using BMP", withdrawals sent before the Adj-rib-in
                # has been completely synced can be safely ignored. Hopefully
                # that's the only way we can end up here...
                self._logger.error("Found withdrawal for unknown prefix %s from peer %s, source %s" %
                    (pref.prefix, msg.peer_address, msg.source.host))

        # nlri
        for pref in msg.update.nlri:

            # does valid prefix exist? If so, end validity.
            start_select = time.time()
            self.curs.execute(Q_FIND_PATH, (msg.source.host, msg.peer_address, pref.prefix, msg.time, msg.time))
            self.time_select += time.time() - start_select

            if self.curs.rowcount > 0:
                row = self.curs.fetchone()
                start_update = time.time()
                try:
                    self.curs.execute(Q_INVALIDATE_PATH, (msg.time, row[0]))
                except psycopg2.Error, e:
                    self._logger.error("Unable to invalidate prefix %s (id %d) in message %s: %s " %
                        (pref, row[0], msg, e))
                    self._logger.error("Time: %s" % msg.time)
                    continue

                self.time_update += time.time() - start_update


            # insert path
            aspath = []
            for a in msg.update.pathattr.get('aspath').value:
                if type(a) is set:
                    aspath += list(a)
                elif type(a) is list:
                    aspath += a
                else:
                    aspath.append(a)

            args = {
                'valid_from': msg.time,
                'valid_to': 'infinity',
                'bmp_src': msg.source.host,
                'neighbor_addr': msg.peer_address,
                'neighbor_as': msg.peer_as,
                'next_hop': msg.update.pathattr.get('nexthop').value,
                'origin': msg.update.pathattr.get('origin').value.upper(),
                'lpref': None,
                'med': None,
                'prefix': pref.prefix,
                'aspath': aspath,
                'communities': None
            }

            if 'localpref' in msg.update.pathattr:
                args['lpref'] = msg.update.pathattr.get('localpref').value

            if 'med' in msg.update.pathattr:
                args['med'] = msg.update.pathattr.get('med').value

            if 'extcommunity' in msg.update.pathattr:
                args['communities'] = msg.update.pathattr.get('extcommunity').value

            start_insert = time.time()
            self.curs.execute(Q_INSERT_PATH, args)
            self.time_insert += time.time() - start_insert

            self.npref_add += 1

        if self.nmsg % 1000 == 0:
            now = time.time()
            self._logger.debug('nmsg %d %.1f msg/s; npref_add %d %.1f pref/s npref_del %d %.1f pref/s select: %f update: %f insert: %f' % (
                self.nmsg,
                10000/(now - self.last_ts),
                self.npref_add,
                (self.npref_add - self.last_npref_add)/(now - self.last_ts),
                self.npref_del,
                (self.npref_del - self.last_npref_del)/(now - self.last_ts),
                self.time_select,
                self.time_update,
                self.time_insert
            ))
            self.last_ts = now
            self.last_npref_add = self.npref_add
            self.last_npref_del = self.npref_del

        self.conn.commit()


    def store_peer_down(self, msg):
        """ Store a peer down message
        """

        # invalidate all prefixes from neighbor
        self.logger._debug("Got peer down notification from %s. Invalidating all prefixes from peer %s" %
            (msg.source.address, msg.peer_address))

        # write BGP packet if there is any
        if msg.reason == 1 or msg.reason == 3:
            self.curs.execute(Q_INSERT_RAW,
                (msg.time, msg.source.address, msg.peer_address, psycopg2.Binary(msg.raw_payload)))

        # invalidate all prefixes received from the neighbor by src
        self.curs.execute(Q_INVALIDATE_NEIGHBOR, (msg.time, msg.source.address, msg.peer_address, msg.time))
        self.conn.commit()

        # pickle data
        if self.dump_file is not None:
            pickle.dump(msg, self.dump_file)


    def store_stat_report(self, msg):
        """ Store a statistics report
        """

        self._logger.debug("Got statistics report from %s, peer %s" % (msg.source.host, msg.peer_address))


    def store_other(self, msg):
        """ Store other message type
        """

        # pickle data
        if self.dump_file is not None:
            pickle.dump(msg, self.dump_file)
