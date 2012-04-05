# /usr/bin/python
#
# A simple BMP server
#

import logging
from twisted.internet.protocol import Factory, Protocol

class BMPProtocol(Protocol):
    """ A class for handling the BGP Monitoring Protocol
    """

    _logger = None
    factory = None


    def __init__(self, factory):
        self.factory = factory
        self._logger = logging.getLogger(self.__class__.__name__)


    def connectionMade(self):
        """ What to do when a connection has been made?
        """


    def connectionLost(self):
        """ What to do when a connection has been lost?
        """


    def dataReceived(self):
        """ Data has been received.
        """



class BMPFactory(Factory):
    """ A factory for the BMP protocol
    """

    protocol = BMPProtocol
