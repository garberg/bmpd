Overview
--------
bmpd is a daemon which receives BGP updates through the BGP Monitoring Protocol
and uses it to maintain a local copy of the adj-rib-in of the routers which are
being monitored stored in a PostgreSQL database. When updates are received, the
changes are stored so that the adj-rib-in for the monitored routers for any
point in time can be queried.

This project ows much to bmpreceiver (http://code.google.com/p/bmpreceiver/) on
which it was originally based.

State
-----
bmpd is in an early development state and currently not very usable...
Hopefully this will change in a not too distant future!

Requirements
------------
The following is required to run bmpd:
* PostgreSQL with:
  * ip4r (http://pgfoundry.org/projects/ip4r)
* PyBGP (https://launchpad.net/pybgp) modified for 32-bit AS support and
  OrderedDicts which are serializable over a multiprocessing.Queue
  (https://github.com/garberg/pybgp)
* python-daemon (http://pypi.python.org/pypi/python-daemon/)
