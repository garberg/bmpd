#! /usr/bin/python
#
#
#

import logging
import psycopg2
import time
import pickle

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
        AND CURRENT_TIMESTAMP >= valid_from AND CURRENT_TIMESTAMP < valid_to"""

Q_INVALIDATE_PATH = """UPDATE adj_rib_in SET
    valid_to = %s
    WHERE id = %s"""

Q_INSERT_PATH = """INSERT INTO adj_rib_in
    (
        valid_from,
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
        %(time)s,
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
    conn = None
    time_select = 0.0
    time_update = 0.0
    time_insert = 0.0
    nmsg = 0
    npref_add = 0
    last_npref_add = 0
    npref_del = 0
    last_npref_del = 0
    nmsg = 0
    last_ts = None
    dump_file = None


    def __init__(self):
        # Create store instance

        self._logger = logging.getLogger(self.__class__.__name__)
        self.conn = psycopg2.connect(host='127.0.0.1', user='bmp', password='bmp', database='bmp')
        self.curs = self.conn.cursor()

        # open file to pickle unknown data to
        try:
            self.dump_file = open(DUMP_FILE_PATH, 'a')
        except IOError, e:
            self._logger.error("Could not open dump file: %s" % e.message)


    def store(self, msg, src):
        # save BMP message

        if msg.msg_type == BMP.MSG_TYPE_ROUTE_MONITORING:
            self.store_route_mon(msg, src)

        elif msg.msg_type == BMP.MSG_TYPE_STATISTICS_REPORT:
            self.store_stat_report(msg, src)

        elif msg.msg_type == BMP.MSG_TYPE_PEER_DOWN_NOTIFICATION:
            self.store_peer_down(msg, src)

        else:
            self.store_other(msg, src)



    def store_route_mon(self, msg, src):
        """ Store a route monitoring message
        """

        if self.last_ts is None:
            self.last_ts = time.time()


        # save raw BGP packet
        self.curs.execute(Q_INSERT_RAW, (msg.time, src.host, msg.peer_address, psycopg2.Binary(msg.raw_payload)))

        #
        # update adj_rib_in table
        #

        # withdrawals
        for pref in msg.update.withdraw:
            self._logger.debug("Withdrawal of prefix %s" % pref)
            self.npref_del += 1

            self.curs.execute(Q_FIND_PATH, (src.host, msg.peer_address, pref))
            if self.curs.rowcount > 0:
                row = self.curs.fetchone()
                try:
                    self.curs.execute(Q_INVALIDATE_PATH, (msg.time, row[0]))
                except psycopg2.Error, e:
                    self._logger.error("Unable to withdraw prefix %s (id %d) in message %s: %s " %
                        (pref, row[0], msg, e))
            else:
                self._logger.error("Got withdrawal for unknown prefix %s from host %s, peer %s" %
                    (pref, src.host, msg.peer_address))

        # nlri
        for pref in msg.update.nlri:

            # does prefix exist? If so, end validity.
            start_select = time.time()
            self.curs.execute(Q_FIND_PATH, (src.host, msg.peer_address, pref.prefix))
            self.time_select += time.time() - start_select

            if self.curs.rowcount > 0:
                row = self.curs.fetchone()
                start_update = time.time()
                try:
                    self.curs.execute(Q_INVALIDATE_PATH, (msg.time, row[0]))
                except psycopg2.Error, e:
                    self._logger.error("Unable to invalidate prefix %s (id %d) in message %s: %s " % (pref, row[0], msg, e))
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
                'time': msg.time,
                'bmp_src': src.host,
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

        self.nmsg += 1

        if self.nmsg % 10000 == 0:
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


    def store_peer_down(self, msg, src):
        """ Store a peer down message
        """

        # pickle data
        if self.dump_file is not None:
            pickle.dump(msg, self.dump_file)


    def store_stat_report(self, msg, src):
        """ Store a statistics report
        """

        # pickle data
        if self.dump_file is not None:
            pickle.dump(msg, self.dump_file)


    def store_other(msg, src):
        """ Store other message type
        """

        # pickle data
        if self.dump_file is not None:
            pickle.dump(msg, self.dump_file)
