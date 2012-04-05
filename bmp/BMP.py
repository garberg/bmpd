#!/usr/bin/python2.5  # pylint: disable-msg=C6301,C6409
#
# Copyright 2009 Google Inc.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""BGP Monitoring Protocol - various constants."""

__author__ = "sstuart@google.com (Stephen Stuart)"
__version__ = "0.1"

import socket
import struct
import time
import indent

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


def ParseBmpHeader(header, verbose=False):
  """Parse a BMP header.

  Args:
    header: array containing BMP message header.
    verbose: be chatty, or not.

  Returns:
    An int indicating the type of message that follows the header,
    and a list of strings to print.

  Raises:
    ValueError: an unexpected value was found in the message
  """

  indent_str = indent.IndentLevel(indent.BMP_HEADER_INDENT)
  print_msg = []

  version, msg_type, peer_type, peer_flags = struct.unpack(">BBBB",
                                                           header[0:4])
  if peer_flags & PEER_FLAG_IPV6:
    peer_address = socket.inet_ntop(socket.AF_INET6, header[12:28])
  else:
    peer_address = socket.inet_ntop(socket.AF_INET, header[24:28])
  peer_as, time_sec = struct.unpack(">LxxxxL",
                                    header[28:40])

  # If we have a version mismatch, we're pretty much done here.
  #
  if version != VERSION:
    raise ValueError("Found BMP version %d, expecting %d" % (version,
                                                             VERSION))

  # Decide what to format as text
  #
  print_msg.append("%sBMP version %d type %s peer %s AS %d\n" %
                   (indent_str,
                    version,
                    MSG_TYPE_STR[msg_type],
                    peer_address,
                    peer_as))
  if verbose:
    print_msg.append("%speer_type %s" % (indent_str,
                                         PEER_TYPE_STR[peer_type]))
    print_msg.append(" peer_flags 0x%x" % peer_flags)
    print_msg.append(" router_id %s\n" % socket.inet_ntoa(header[32:36]))
    print_msg.append("%stime %s\n" % (indent_str, time.ctime(time_sec)))

  # Return the message type so the caller can decide what to do next,
  # and the list of strings representing the collected message.
  #
  return msg_type, print_msg


# A function indication whether or not a BMP Peer Down message comes
# with a BGP notification
#
def PeerDownHasBgpNotification(reason):
  """Determine whether or not a BMP Peer Down message as a BGP notification.

  Args:
    reason: the Peer Down reason code (from the draft)

  Returns:
    True if there will be a BGP Notification, False if not
  """

  return reason == 1 or reason == 3
