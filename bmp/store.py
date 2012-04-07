#! /usr/bin/python
#
#
#

import logging

import BMP

class Store:

    def __init__(self):
        # Create saver instance

        self._logger = logging.getLogger(self.__class__.__name__)


    def store(self, msg):
        # save BMP message 

        if msg.msg_type == BMP.MSG_TYPE_ROUTE_MONITORING:
            self._logger.debug("Got a route monitoring message")

            self._logger.debug("nlri: %s withdraw: %s patattr: %s" % (msg.update.nlri, msg.update.withdraw, msg.update.pathattr))

        elif msg.msg_type == BMP.MSG_TYPE_STATISTICS_REPORT:
            self._logger.debug("Got a statistics report message")
            
        elif msg.msg_type == BMP.MSG_TYPE_PEER_DOWN_NOTIFICATION:
            self._logger.debug("Got a peer down notification message")

        else:
            self._logger.debug("Other message")

