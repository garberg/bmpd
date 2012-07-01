# /usr/bin/python
#
# A simple BMP server
#

import logging

from twisted.internet.protocol import Factory, Protocol

from bmp import BMP, store


class BMPProtocol(Protocol):
    """ A class for handling the BGP Monitoring Protocol
    """

    _logger = None
    factory = None
    consumer = None
    message = None
    buf = ""


    def __init__(self, factory):
        self.factory = factory
        self._logger = logging.getLogger(self.__class__.__name__)
        self.message = BMP.BMPMessage()


    def connectionMade(self):
        """ What to do when a connection has been made?
        """

        self._logger.info("Host %s connected" % self.transport.getPeer().host)


    def connectionLost(self, reason):
        """ What to do when a connection has been lost?
        """
        self._logger.info("Host %s disconnected (%s)" % (self.transport.getPeer().host, reason))


    def dataReceived(self, data):
        """ Data has been received.
        """

        self.buf += data

        while len(self.buf) > self.message.length:

#            self._logger.debug("Iterating; buf_len: %d msg_len: %d" % (len(self.buf), self.message.length))

            tmp = self.buf[0:self.message.length]
            self.buf = self.buf[self.message.length:]

            if self.message.consume(tmp):
                # message completely parsed

                # fetch message source and save data
                self.message.source = self.transport.getPeer()
                self.factory.store.store(self.message)

                # create new message
                self.message = BMP.BMPMessage()



class BMPFactory(Factory):
    """ A factory for the BMP protocol
    """

    conn = None
    curs = None
    protocol = BMPProtocol
    store = None


    def __init__(self, store):
        self.store = store


    def buildProtocol(self, addr):
        return BMPProtocol(self)
