#
# A BMP protocol parser
#
# A lot of code here has been more or less stolen from
# bmpreceiver (http://code.google.com/p/bmpreceiver/)!
#

import struct
import socket
import logging
from datetime import datetime

from pybgp import proto

# The length of the fixed header part of a BMP message.
#
HEADER_LEN = 44

# Version of the protocol, as specified in the header.
#
VERSION = 1

# Message types.
#
MSG_TYPE_ROUTE_MONITORING = 0
MSG_TYPE_STATISTICS_REPORT = 1
MSG_TYPE_PEER_DOWN_NOTIFICATION = 2
MSG_TYPE_STR = {MSG_TYPE_ROUTE_MONITORING: "Route Monitoring",
                MSG_TYPE_STATISTICS_REPORT: "Statistics Report",
                MSG_TYPE_PEER_DOWN_NOTIFICATION: "Peer Down Notification"}

# Peer types.
#
PEER_TYPE_GLOBAL = 0
PEER_TYPE_L3_VPN = 1
PEER_TYPE_STR = {PEER_TYPE_GLOBAL: "Global",
                 PEER_TYPE_L3_VPN: "L3 VPN"}

# Peer flags.
#
PEER_FLAG_IPV6 = 0x80

# Statistics report type codes.
#
SR_TYPE_STR = {0: "prefixes rejected by inbound policy",
               1: "(known) duplicate prefix advertisements",
               2: "(known) duplicate withdraws",
               3: "updates invalidated due to CLUSTER_LIST loop",
               4: "updates invalidated due to AS_PATH loop"}

# Peer down reason codes.
#
PEER_DOWN_REASON_STR = {1: "Local system closed session, notification sent",
                        2: "Local system closed session, no notification",
                        3: "Remote system closed session, notification sent",
                        4: "Remote system closed session, no notification"}

# BGP header length
#
BGP_HEADER_LEN = 19

class BMPMessage:

    version = None
    msg_type = None
#    source_address = None
    peer_type = None
    peer_flags = None
    peer_as = None
    peer_address = None
    time = None
    raw_header = ""
    raw_payload = ""

    state = "INIT"
    length = 44
    _logger = None


    def __str__(self):
        """ Return string representation of BMP message
        """

        return "BMP version %d message of type %d" % (self.version, self.msg_type)

    def __init__(self):
        """ Create BMPMessage
        """

        self._logger = logging.getLogger(self.__class__.__name__)


    def header_from_bytes(self, header):

        self.raw_header = header

        self.version, self.msg_type, self.peer_type, self.peer_flags = struct.unpack(">BBBB", header[0:4])

        if self.peer_flags & PEER_FLAG_IPV6:
            self.peer_address = socket.inet_ntop(socket.AF_INET6, header[12:28])
        else:
            self.peer_address = socket.inet_ntop(socket.AF_INET, header[24:28])

        self.peer_as, time_tmp = struct.unpack(">LxxxxL", header[28:40])
        self.time = datetime.fromtimestamp(time_tmp)

        # If we have a version mismatch, we're pretty much done here.
        #
        if self.version != VERSION:
            raise ValueError("Found BMP version %d, expecting %d" % (self.version, VERSION))

        if self.msg_type == MSG_TYPE_ROUTE_MONITORING:
            #self._logger.debug("Got route monitoring message")
            self.length = BGP_HEADER_LEN
            self.state = 'PARSE_BGP_HEADER'

        elif self.msg_type == MSG_TYPE_STATISTICS_REPORT:
            #self._logger.debug("Got route statistics report message")
            self.length = 4
            self.state = 'PARSE_BMP_STAT_REPORT'

        elif self.msg_type == MSG_TYPE_PEER_DOWN_NOTIFICATION:
            #self._logger.debug("Got route peer down notification message")
            self.length = 1
            self.state = 'PARSE_BMP_PEER_DOWN'

        else:
            self._logger.error("unknown BMP message type %d" % self.msg_type)


    def consume(self, data):
        """ Consume data...
        """

        assert len(data) == self.length

        if self.state == 'INIT':
            # parse BMP header

            self.header_from_bytes(data)


        elif self.state == 'PARSE_BMP_PEER_DOWN':
            # parse BMP peer down message

            self.raw_payload += data

            self.reason = ord(data)

            # For reason 1 or 3 we also get a BGP notification
            if self.reason == 1 or self.reason == 3:
                self.state = 'PARSE_BGP_NOTIFICATION'
                self.length = 2

            else:
                # done!
                return True


        elif self.state == 'PARSE_BGP_NOTIFICATION':
            # parse BGP notification
            self.notification = proto.Notification.from_bytes(data)

            self.raw_payload += data

            # done!
            return True


        elif self.state == 'PARSE_BGP_HEADER':
            # parse a BGP header

            self.raw_payload += data

            self.bgp_auth, tmp_len, self.bgp_type = struct.unpack('!16sHB', data)
            #self._logger.debug("Parsed a BGP header. type: %d size: %d" % (self.bgp_type, self.length))
            self.state = 'PARSE_BGP_UPDATE'
            self.length = tmp_len - BGP_HEADER_LEN


        elif self.state == 'PARSE_BGP_UPDATE':
            # parse a BGP update

            self.raw_payload += data

#            self._logger.debug("Parsing BGP update")
#            try:
            self.update = proto.Update.from_bytes(data, True)
#            except Exception, e:
#                self._logger.error("BGP update parse failed: %s" % str(e))

            # done!
            return True


        elif self.state == 'PARSE_BMP_STAT_REPORT':
            # parse a BMP stat report header

            self.raw_payload += data

            self.statistics_left = struct.unpack(">L", data)[0]
            self.statistics = {}
            self.state = 'PARSE_BMP_STAT_ELEMENT_TYPE_LENGTH'
            self.length = 4


        elif self.state == 'PARSE_BMP_STAT_ELEMENT_TYPE_LENGTH':
            # parse a BMP statistics element type & length

            self.raw_payload += data

            if self.statistics_left == 0:
                # done!
                return True

            self.stat_elem_type, self.length = struct.unpack(">HH", data)
            assert self.stat_elem_type in SR_TYPE_STR
            assert self.length == 4

            self.state == 'PARSE_BMP_STAT_ELEMENT_VALUE'


        elif self.state == 'PARSE_BMP_STAT_ELEMENT_VALUE':
            # parse a BMP statistics element value

            self.raw_payload += data

            self.statistics[SR_TYPE_STR[self.stat_elem_type]] = struct.unpack('>L', data)[0]
            self.statistics_left -= 1

            if self.statistics_left == 0:
                return True

            self.state = 'PARSE_BMP_STAT_ELEMENT_TYPE_LENGTH'


        else:
            # ERROR
            self._logger.error("State not implemented: %s" % self.state)

        return False
