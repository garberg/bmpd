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

"""Border Gateway Protocol - various constants and functions."""

__author__ = "sstuart@google.com (Stephen Stuart)"
__version__ = "4.0"

import array
import math
import socket
import struct
import sys
import indent

# In general, see RFC4271 for details.
#
# The length of the fixed header part of a BGP message.
#
HEADER_LEN = 19
MIN_LENGTH = HEADER_LEN
MAX_LENGTH = 4096

# Message types, see RFC4271 and RFC2918.
#
OPEN = 1
UPDATE = 2
NOTIFICATION = 3
KEEPALIVE = 4
ROUTE_REFRESH = 5
MSG_TYPE_STR = {OPEN: "OPEN",
                UPDATE: "UPDATE",
                NOTIFICATION: "NOTIFICATION",
                KEEPALIVE: "KEEPALIVE",
                ROUTE_REFRESH: "ROUTE-REFRESH"}

# Attribute types.
#
ATTR_TYPE_ORIGIN = 1
ATTR_TYPE_AS_PATH = 2
ATTR_TYPE_NEXT_HOP = 3
ATTR_TYPE_MULTI_EXIT_DISC = 4
ATTR_TYPE_LOCAL_PREF = 5
ATTR_TYPE_ATOMIC_AGGREGATE = 6
ATTR_TYPE_AGGEGATOR = 7
ATTR_TYPE_COMMUNITIES = 8
ATTR_TYPE_ORIGINATOR_ID = 9
ATTR_TYPE_CLUSTER_LIST = 10
ATTR_TYPE_DPA = 11
ATTR_TYPE_ADVERTISER = 12
ATTR_TYPE_RCID_PATH = 13
ATTR_TYPE_MP_REACH_NLRI = 14
ATTR_TYPE_MP_UNREACH_NLRI = 15
ATTR_TYPE_AS4_PATH = 17
ATTR_TYPE_AS4_AGGREGATOR = 18

ATTR_TYPE_STR = {ATTR_TYPE_ORIGIN: "ORIGIN",
                 ATTR_TYPE_AS_PATH: "AS_PATH",
                 ATTR_TYPE_NEXT_HOP: "NEXT_HOP",
                 ATTR_TYPE_MULTI_EXIT_DISC: "MULTI_EXIT_DISC",
                 ATTR_TYPE_LOCAL_PREF: "LOCAL_PREF",
                 ATTR_TYPE_ATOMIC_AGGREGATE: "ATOMIC_AGGREGATE",
                 ATTR_TYPE_AGGEGATOR: "AGGREGATOR",
                 ATTR_TYPE_COMMUNITIES: "COMMUNITIES",
                 ATTR_TYPE_ORIGINATOR_ID: "ORIGINATOR_ID",
                 ATTR_TYPE_CLUSTER_LIST: "CLUSTER_LIST",
                 ATTR_TYPE_DPA: "DPA",
                 ATTR_TYPE_ADVERTISER: "ADVERTISER",
                 ATTR_TYPE_RCID_PATH: "RCID_PATH",
                 ATTR_TYPE_MP_REACH_NLRI: "MP_REACH_NLRI",
                 ATTR_TYPE_MP_UNREACH_NLRI: "MP_UNREACH_NLRI",
                 ATTR_TYPE_AS4_PATH: "AS4_PATH",
                 ATTR_TYPE_AS4_AGGREGATOR: "AS4_AGGREGATOR"}

# Attribute flag values.
#
ATTR_FLAG_OPTIONAL = 128
ATTR_FLAG_TRANSITIVE = 64
ATTR_FLAG_PARTIAL = 32
ATTR_FLAG_EXT_LEN = 16

# Values for the ORIGIN attribute.
#
ORIGIN_IGP = 0
ORIGIN_EGP = 1
ORIGIN_INCOMPLETE = 2
ORIGIN_STR = {ORIGIN_IGP: "IGP",
              ORIGIN_EGP: "EGP",
              ORIGIN_INCOMPLETE: "incomplete"}

# AS_PATH attribute path segment type codes.
#
AS_SET = 1
AS_SEQUENCE = 2
AS_CONFED_SET = 3
AS_CONFED_SEQUENCE = 4
AS_PATH_SEG_STR = {AS_SET: "set",
                   AS_SEQUENCE: "sequence",
                   AS_CONFED_SET: "confed_set",
                   AS_CONFED_SEQUENCE: "confed_seq"}
AS_PATH_SEG_FORMAT = {AS_SET: "{ %s }",
                      AS_SEQUENCE: "%s",
                      AS_CONFED_SET: "( %s )",
                      AS_CONFED_SEQUENCE: "( %s )"}

# NOTIFICATION codes.
#
MSG_HEADER_ERR = 1
OPEN_MSG_ERR = 2
UPD_MSG_ERR = 3
HOLD_TIMER_EXPIRED = 4
FSM_ERR = 5
CEASE = 6
NOTIFICATION_CODE = {MSG_HEADER_ERR: "Message Header Error",
                     OPEN_MSG_ERR: "Open Message Error",
                     UPD_MSG_ERR: "Update Message Error",
                     HOLD_TIMER_EXPIRED: "Hold Timer Expired",
                     FSM_ERR: "FSM Error",
                     CEASE: "Cease"}

# NOTIFICATION subcodes.
#
NOTIFICATION_SUBCODE = {MSG_HEADER_ERR: {1: "Connection Not Synchronized",
                                         2: "Bad Message Length",
                                         3: "Bad Message Type"},
                        OPEN_MSG_ERR: {1: "Unsupported Version Number",
                                       2: "Bad Peer AS",
                                       3: "Bad BGP Identifier",
                                       4: "Unsupported Optional Parameter",
                                       5: "[Deprecated per RFC4271]",
                                       6: "Unacceptable Hold Time"},
                        UPD_MSG_ERR: {1: "Malformed Attribute List",
                                      2: "Unrecognized Well-known Attribute",
                                      3: "Missing Well-known Attribute",
                                      4: "Attribute Flags Error",
                                      5: "Attribute Length Error",
                                      6: "Invalid ORIGIN Attribute",
                                      7: "[Deprecated per RFC4271]",
                                      8: "Invalid NEXT_HOP Attribute",
                                      9: "Optional Attribute Error",
                                      10: "Invalid Network Field",
                                      11: "Malformed AS_PATH"}}

# Well-known community values.
#
WELL_KNOWN_COMM = {0xFFFFFF01: "NO_EXPORT",
                   0xFFFFFF02: "NO_ADVERTISE",
                   0xFFFFFF03: "NO_EXPORT_SUBCONFED"}

# Address families, per RFC1700.
#
AF_IP = 1
AF_IP6 = 2
AF_STR = {AF_IP: "IPv4",
          AF_IP6: "IPv6"}

# Multiprotocol Subsequent Address Family Identifier (SAFI) per RFC2858.
#
MP_SAFI_STR = {1: "unicast",
               2: "multicast",
               3: "unicast+multicast"}


def BytesForPrefix(prefix_len):
  """Determine # of octets required to hold a prefix of length per RFC4271.

  Args:
    prefix_len: length of the prefix in bits.

  Returns:
    An int indicating how many octets are used to hold the prefix.

  Raises:
    ValueError: indicates that prefix_len has an invalid value
  """

  if prefix_len < 0 or prefix_len > 128:
    raise ValueError("prefix_len %d is out of range" % prefix_len)
  return int(math.ceil(prefix_len / 8.0))


def BytesForSnpa(snpa_len):
  """Determine # of octets required to hold an SNPA per RFC2858.

  Args:
    snpa_len: length of the SNPA in semi-octets.

  Returns:
    An int indicating how many octets are used to hold the prefix.

  Raises:
    ValueError: indicates that snpa_len has an invalid value
  """

  # You have to read RFC2858 to believe this. SNPA lengths are expressed
  # in semi-octets.
  #
  if snpa_len < 1 or snpa_len > 256:
    raise ValueError("snpa_len %d is out of range" % snpa_len)
  return int(math.ceil(snpa_len / 2.0))


def DumpHexString(buff, start, length):
  """Convert hex data to text.

  Args:
    buff: a buffer of hex data to convert to text.
    start: starting offset of data to convert.
    length: length of data to convert.

  Returns:
    String of text.
  """

  hex_dump = []
  for x in range(length):
    hex_dump.append("%02x" % struct.unpack_from("B", buff, x + start))
  return " ".join(hex_dump)


def ParseBgpAsPath(update, start, end, rfc4893_updates):
  """Parse BGP AS_PATH path attribute information into text per RFC4271.

  Args:
    update: a buffer containing a BGP message.
    start: offset at which AS_PATH parsing is to start.
    end: offset at which AS_PATH parsing is to stop.
    rfc4893_updates: true if AS_PATH conforms to RFC4893, otherwise false

  Returns:
    A list of strings containing the text representation of the path attribute.
  """

  path_text = []

  # We're going to try this with the default value of rfc4893_updates,
  # and try again with it forced to True if we get an exception.
  #
  try:

    offset = start

    # Walk through the path segments.
    #
    while offset < end:

      # Get type and length.
      #
      path_seg_type = update[offset]
      offset += 1
      path_seg_len = update[offset]
      offset += 1
      path_seg_val = []

      # Step through AS numbers in path.
      #
      for _ in range(path_seg_len):

        # RFC4893-style updates have 4-octet ASNs, otherwise 2-octet ASNs.
        #
        if rfc4893_updates:
          path_seg_val.append(str(struct.unpack_from(">L",
                                                     update,
                                                     offset)[0]))
          offset += 4
        else:
          path_seg_val.append(str(struct.unpack_from(">H",
                                                     update,
                                                     offset)[0]))
          offset += 2

      # Turn the list of AS numbers into text, using a format string
      # appropriate to the segment type.
      #
      path_seg_str = " ".join(path_seg_val)
      path_text.append(AS_PATH_SEG_FORMAT[path_seg_type] % path_seg_str)

  # If we get a KeyError exception and the rfc4893_updates flag is not
  # set, tell the user to try using the rfc4893 switch; reraise the exception.
  #
  except KeyError, esc:
    if not rfc4893_updates:
      sys.stderr.write("ParseBgpAsPath parsing error, try --rfc4893 switch\n")
    raise esc

  return path_text


def ParseBgpCommunities(update, start, end):
  """Parse BGP COMMUNITIES path attribute information into text.

  Args:
    update: a buffer containing a BGP message.
    start: offset at which community parsing is to start.
    end: offset at which community parsing is to stop.

  Returns:
    A list of strings containing the text representation of the path attribute.
  """

  comm_text = []
  offset = start

  # Walk through the community values.
  #
  while offset < end:

    # Get a value.
    #
    x = struct.unpack_from(">L", update, offset)[0]

    # If a well-known community, use its name; else unpack it again for
    # presentation.
    #
    if x in WELL_KNOWN_COMM:
      comm_text.append(WELL_KNOWN_COMM[x])
    else:
      high, low = struct.unpack_from(">HH", update, offset)
      comm_text.append("%d:%d" % (high, low))

    # On to the next.
    #
    offset += 4

  return comm_text


def ParseBgpHeader(header, verbose=False):
  """Parse a BGP header into text, see RFC4271 section 4.1.

  Args:
    header: a buffer containing a BGP message header.
    verbose: be chatty, or not.

  Returns:
    An int indicating the length of the rest of the BGP message,
    an int indication the type of the message,
    a list of strings to print.

  Raises:
    ValueError: an invalid value was found in the message.
  """

  print_msg = []
  indent_str = indent.IndentLevel(indent.BGP_HEADER_INDENT)

  try:

    # Verify that the marker is correct, raise a ValueError exception if
    # it is not.
    #
    for x in range(0, 15):
      if header[x] != 255:
        raise ValueError("BGP marker octet %d != 255" % x)

    # Unpack the length and type.
    #
    length, msg_type = struct.unpack(">HB", header[16:19])
    if length < MIN_LENGTH or length > MAX_LENGTH:
      raise ValueError("BGP message length %d incorrect" % length)
    if msg_type not in MSG_TYPE_STR:
      raise ValueError("BGP message type %d unknown" % msg_type)
    print_msg.append("%sBGP %s" % (indent_str, MSG_TYPE_STR[msg_type]))
    if verbose:
      print_msg.append(" length %d\n" % (length - HEADER_LEN))
    else:
      print_msg.append("\n")

    # Return the length of the rest of the PDU, its type, and the list
    # of strings representing the collected message
    #
    return length - HEADER_LEN, msg_type, print_msg

  # In case of any exception, dump the hex of the message to help
  # debug what's wrong with the message, and re-raise the exception.
  #
  except Exception, esc:
    if verbose:
      print DumpHexString(header, 0, HEADER_LEN)
    raise esc


def ParseBgpMpAttr(update, start, end, has_snpa):
  """Parse a BGP MP_REACH_NLRI or MP_UNREACH_NLRI attribute into text.

  Args:
    update: a buffer containing a BGP message.
    start: offset at which attribute parsing is to start.
    end: offset at which attribute parsing is to stop.
    has_snpa: True if there's an SNPA section, False otherwise

  Returns:
    A list of strings containing the text representation of the attribute.
  """

  mpattr_text = []
  offset = start

  # Start with AFI, SAFI, length of next hop.
  #
  afi, safi, nhl = struct.unpack_from(">HBB", update, offset)
  offset += 4

  # NEXT_HOP depends on length of next hop.
  #
  if afi == AF_IP:
    next_hop = socket.inet_ntop(socket.AF_INET, update[offset:offset+4])
  elif afi == AF_IP6:
    next_hop = socket.inet_ntop(socket.AF_INET6,
                                update[offset:offset+16])
  else:
    next_hop = "unknown for afi %d" % afi
  mpattr_text.append("NEXT_HOP %s\n" % next_hop)

  # Turn AFI, SAFI into text.
  #
  if afi in AF_STR:
    afi_str = AF_STR[afi]
  else:
    afi_str = str(afi)
  if safi in MP_SAFI_STR:
    safi_str = MP_SAFI_STR[safi]
  else:
    safi_str = str(safi)
  mpattr_text.append("AFI %s SAFI %s\n" % (afi_str, safi_str))

  # On to the next.
  #
  offset += nhl

  # Next might be SNPA.
  #
  if has_snpa:

    # Unpack the number of SNPAs.
    #
    num_snpa = struct.unpack_from(">B", update, offset)[0]
    offset += 1

    # Dump the SNPAs as hex.
    #
    for _ in range(num_snpa):

      # Get the length.
      #
      snpa_len = struct.unpack_from(">B", update, offset)[0]
      offset += 1

      # You have to read RFC2858 to believe this.
      #
      snpa_len_octets = BytesForSnpa(snpa_len)
      mpattr_text.append("SNPA %s\n" % DumpHexString(update,
                                                     offset,
                                                     snpa_len_octets))
      offset += snpa_len_octets

  # Next section is NLRI information.
  #
  nlri_text = ParseBgpNlri(update, offset, end, afi)
  for nlri_str in nlri_text:
    mpattr_text.append("mp_nlri %s\n" % nlri_str)

  # Return list of strings.
  #
  return mpattr_text


def ParseBgpNlri(update, start, end, afi, debug=False):
  """Parse BGP NLRI into text.

  Args:
    update: a buffer containing a BGP message.
    start: offset at which NLRI parsing is to start.
    end: offset at which NLRI parsing is to stop.
    afi: address family, per RFC1700.
    debug: true if debug messages should be printed, otherwise false.

  Returns:
    A list of strings containing the text representation of the NLRI.

  Raises:
    ValueError: unexpected value found for AFI.
  """

  nlri_text = []
  offset = start

  # Walk through NLRI values
  #
  while offset < end:

    # Get prefix length, and figure out how much we need to take from
    # update to represent it.
    #
    prefix_len = update[offset]
    if debug:
      print "prefix_len %d at %d" % (prefix_len, offset)
    need_bytes = BytesForPrefix(prefix_len)
    offset += 1

    # Override AFI if it's AF_IP and we know that the number of octets
    # necessary to hold the NLRI is more than is valid for AF_IP. This
    # is done because it appears that JUNOS 9.5 sends AF_IP6 withdraws
    # in the regular withdraw section of a BGP UPDATE message, rather
    # than constructing an MP_UNREACH path attribute and putting the
    # AF_IP6 withdraws there.
    #
    if (need_bytes > 4) and (afi == AF_IP):
      if debug:
        sys.stderr.write("".join(["ParseBgpNlri overriding AFI ",
                                  " bytes needed for prefix length\n"]))
      afi = AF_IP6

    # Get a buffer of correct size for address family, and pick the
    # right AFI for the socket library (which varies from platform to
    # platform and does not correspond to the RFC1700 values for AFI).
    #
    if afi == AF_IP:
      socket_afi = socket.AF_INET
      prefix = array.array("B", [0] * 4)
    elif afi == AF_IP6:
      socket_afi = socket.AF_INET6
      prefix = array.array("B", [0] * 16)
    else:
      raise ValueError("unexpected value %d for AFI" % afi)

    # Copy from update into buffer and advance pointer.
    #
    for x in range(need_bytes):
      prefix[x] = update[x + offset]
    offset += need_bytes

    # Convert to presentation.
    #
    nlri_text.append("%s/%d" % (socket.inet_ntop(socket_afi, prefix),
                                prefix_len))

  return nlri_text


def ParseBgpNotification(notification, length, verbose=False):
  """Parse a BGP Notification message, see RFC4271 section 4.5.

  Args:
    notification: the body of a BGP Notification message.
    length: the length of the message body.
    verbose: be chatty, or not.

  Returns:
    A list of strings to print

  Raises:
    ValueError: a code or subcode value is invalid per RFC4271
  """

  print_msg = []
  indent_str = indent.IndentLevel(indent.BGP_CONTENT_INDENT)

  code, subcode = struct.unpack(">BB", notification[0:2])
  if code not in NOTIFICATION_CODE:
    raise ValueError("BGP NOTIFICATION code %d is invalid" % code)

  code_str = NOTIFICATION_CODE[code]
  if code in NOTIFICATION_SUBCODE:
    if subcode not in NOTIFICATION_SUBCODE[code]:
      raise ValueError("BGP NOTIFICATION code %d subcode %d is invalid" %
                       (code, subcode))
    else:
      subcode_str = NOTIFICATION_SUBCODE[code][subcode]
    print_msg.append("%sNOTIFICATION code %s subcode %s\n" % (indent_str,
                                                              code_str,
                                                              subcode_str))
  else:
    print_msg.append("%sNOTIFICATION code %s\n" % (indent_str, code_str))

  # If there are data bytes, convert them to text as hex digits.
  #
  if length > 2 and verbose:
    print_msg.append("%sNOTIFICATION data " % indent_str)
    print_msg.append(DumpHexString(notification, 3, length - 1))
    print_msg.append("\n")

  # Return the list of strings representing collected message.
  #
  return print_msg


def ParseBgpRouteRefresh(message, length):
  """Parse a BGP ROUTE-REFRESH message; see RFC2918.

  Args:
    message: the body of a BGP ROUTE-REFRESH message.
    length: the length of the message.

  Returns:
    A list of strings to print

  Raises:
    ValueError: an unexpected value was found in the message
  """

  print_msg = []
  indent_str = indent.IndentLevel(indent.BGP_CONTENT_INDENT)
  offset = 0

  # the length is fixed, check it
  #
  if length is not 4:
    raise ValueError("unexpected length %d for ROUTE-REFRESH message" % length)

  # ROUTE-REFRESH messages are very simple: AFI, reserved octet, SAFI.
  #
  afi, reserved, safi = struct.unpack_from(">HBB", message, offset)

  # validate the message parts
  #
  if afi not in AF_STR:
    raise ValueError("unknown AFI %d in ROUTE-REFRESH message" % afi)
  if reserved:
    raise ValueError("reserved not zero in ROUTE-REFRESH message")
  if safi not in MP_SAFI_STR:
    raise ValueError("unknown SAFI %d in ROUTE-REFRESH message" % safi)

  # construct and return a text representation of the message
  #
  print_msg.append("%sAFI %s SAFI %s\n" % (indent_str,
                                           AF_STR[afi],
                                           MP_SAFI_STR[safi]))
  return print_msg


def ParseBgpUpdate(update, length, rfc4893_updates=False, verbose=False):
  """Parse a BGP Update message; see RFC1997, RFC2858, RFC4271 4.3, RFC4893.

  Args:
    update: the body of a BGP UPDATE message.
    length: the length of the message.
    rfc4893_updates: true if update conforms to RFC4893.
    verbose: be chatty, or not.

  Returns:
    A list of strings to print

  Raises:
    ValueError: an unexpected value was found in the message
  """

  print_msg = []
  indent_str = indent.IndentLevel(indent.BGP_CONTENT_INDENT)
  offset = 0

  # First section is withdrawn routes.
  #
  withdrawn_route_len = struct.unpack_from(">H", update[0:2], offset)[0]
  if verbose:
    print_msg.append("%swithdrawn at %d length %d\n" % (indent_str,
                                                        offset,
                                                        withdrawn_route_len))
  offset += 2

  # If any withdrawn routes are present, process them.
  #
  if withdrawn_route_len:
    withdrawn_text = ParseBgpNlri(update,
                                  offset,
                                  offset + withdrawn_route_len,
                                  AF_IP)
    if withdrawn_text:
      prepend_str = "%swithdraw " % indent_str
      sep = "\n%s" % prepend_str
      print_msg.append("%s%s\n" % (prepend_str, sep.join(withdrawn_text)))

    offset += withdrawn_route_len

  # Next section is path attributes
  #
  path_attr_len = struct.unpack_from(">H", update, offset)[0]
  if verbose:
    print_msg.append("%spath attributes at %d length %d\n" % (indent_str,
                                                              offset,
                                                              path_attr_len))
  offset += 2

  # If there are path attributes present, process them.
  #
  path_attr_end = offset + path_attr_len
  while offset < path_attr_end:

    # Get flags and type code.
    #
    attr_flags, attr_type = struct.unpack_from(">BB", update, offset)

    # If we're being verbose, describe the details of the path attribute.
    # We haven't updated offset yet in order to be able to report the
    # offset of the path attribute section in the verbose text.
    #
    if verbose:
      print_msg.append("%spath attr %s at %d" % (indent_str,
                                                 ATTR_TYPE_STR[attr_type],
                                                 offset))
      print_msg.append(" flags 0x%x (" % attr_flags)
      attr_list = []
      if (attr_flags & ATTR_FLAG_OPTIONAL) == ATTR_FLAG_OPTIONAL:
        attr_list.append("optional")
      if (attr_flags & ATTR_FLAG_TRANSITIVE) == ATTR_FLAG_TRANSITIVE:
        attr_list.append("transitive")
      if (attr_flags & ATTR_FLAG_PARTIAL) == ATTR_FLAG_PARTIAL:
        attr_list.append("partial")
      if (attr_flags & ATTR_FLAG_EXT_LEN) == ATTR_FLAG_EXT_LEN:
        attr_list.append("extended-length")
      print_msg.append(" ".join(attr_list))

    # Now increment the offset, check for extended length, and get the
    # length (whose size depends on the extended length flag).
    #
    offset += 2
    if (attr_flags & ATTR_FLAG_EXT_LEN) == ATTR_FLAG_EXT_LEN:
      attr_len = struct.unpack_from(">H", update, offset)[0]
      offset += 2
    else:
      attr_len = update[offset]
      offset += 1

    # Finish up the verbose processing of the path attribute's details.
    #
    if verbose:
      print_msg.append(") len %d\n" % attr_len)

    # Now we can process the specific types of path attribute, see:
    # RFC4271
    # RFC2858
    #
    # ORIGIN
    #
    if attr_type == ATTR_TYPE_ORIGIN:

      # we know both length and possible values of the ORIGIN attribute,
      # raise a ValueError exception if we find something unexpected
      #
      if attr_len != 1:
        raise ValueError("BGP ORIGIN attr_len %d wrong, expected 1" % attr_len)
      if update[offset] not in ORIGIN_STR:
        raise ValueError("BGP ORIGIN value %d wrong" % update[offset])
      print_msg.append("%s%s %s\n" % (indent_str,
                                      ATTR_TYPE_STR[attr_type],
                                      ORIGIN_STR[update[offset]]))

    # AS_PATH (Autonomous System path)
    #
    elif attr_type == ATTR_TYPE_AS_PATH:
      print_msg.append("%s%s " % (indent_str, ATTR_TYPE_STR[attr_type]))
      path_text = ParseBgpAsPath(update,
                                 offset,
                                 offset + attr_len,
                                 rfc4893_updates)
      print_msg.append("%s\n" % " ".join(path_text))

    # NEXT_HOP
    #
    elif attr_type == ATTR_TYPE_NEXT_HOP:
      next_hop = update[offset:offset + 4]
      print_msg.append("%s%s %s\n" % (indent_str,
                                      ATTR_TYPE_STR[attr_type],
                                      socket.inet_ntoa(next_hop)))

    # MED (Multi-Exit Discriminator)
    #
    elif attr_type == ATTR_TYPE_MULTI_EXIT_DISC:
      med_val = struct.unpack_from(">L", update, offset)[0]
      print_msg.append("%s%s %d\n" % (indent_str,
                                      ATTR_TYPE_STR[attr_type],
                                      med_val))

    # LOCAL_PREF (Local Preference)
    #
    elif attr_type == ATTR_TYPE_LOCAL_PREF:
      pref_val = struct.unpack_from(">L", update, offset)[0]
      print_msg.append("%s%s %d\n" % (indent_str,
                                      ATTR_TYPE_STR[attr_type],
                                      pref_val))

    # ATOMIC_AGGREGATE
    #
    elif attr_type == ATTR_TYPE_ATOMIC_AGGREGATE:
      if attr_len:
        raise ValueError("attr_len %d for ATOMIC_AGGREGATE must be zero" %
                         attr_len)
      print_msg.append("%s%s\n" % (indent_str,
                                   ATTR_TYPE_STR[attr_type]))

    # COMMUNITIES
    #
    elif attr_type == ATTR_TYPE_COMMUNITIES:
      print_msg.append("%s%s " % (indent_str, ATTR_TYPE_STR[attr_type]))
      comm_text = ParseBgpCommunities(update, offset, offset + attr_len)
      print_msg.append("%s\n" % " ".join(comm_text))

    # MP_REACH
    #
    elif attr_type == ATTR_TYPE_MP_REACH_NLRI:
      print_msg.append("%s%s\n" % (indent_str, ATTR_TYPE_STR[attr_type]))
      try:
        mpattr_text = ParseBgpMpAttr(update, offset, offset + attr_len, True)
      except Exception, esc:
        print "".join(print_msg),
        for x in range(offset, offset + attr_len):
          print " %02x" % update[x],
        raise esc
      mp_indent = indent.IndentLevel(indent.BGP_MPATTR_INDENT)
      for mpattr in mpattr_text:
        print_msg.append("%s%s" % (mp_indent, mpattr))

    # MP_UNREACH
    #
    elif attr_type == ATTR_TYPE_MP_UNREACH_NLRI:
      print_msg.append("%s%s\n" % (indent_str, ATTR_TYPE_STR[attr_type]))
      mpattr_text = ParseBgpMpAttr(update, offset, offset + attr_len, False)
      mp_indent = indent.IndentLevel(indent.BGP_MPATTR_INDENT)
      for mpattr in mpattr_text:
        print_msg.append("%s%s" % (mp_indent, mpattr))

    # Here we have a catch-all for attributes that we don't parse out
    # in detail (yet) - one for when we have a text representation
    # for the type code, and finally one for when we don't.
    #
    elif attr_type in ATTR_TYPE_STR:
      print_msg.append("%s%s\n" % (indent_str, ATTR_TYPE_STR[attr_type]))
    else:
      print_msg.append("%sBGP path attrbute type %d\n" % (indent_str,
                                                          attr_type))

    # adjust the offset past the path attributes
    #
    offset += attr_len

  # Next section is prefixes reachable according to what's in the path
  # attributes section, parse and add to print_msg.
  #
  if verbose:
    print_msg.append("%sNLRI portion of update at %d\n" % (indent_str, offset))
  nlri_text = ParseBgpNlri(update, offset, length, AF_IP)
  if nlri_text:
    prepend_str = "%snlri " % indent_str
    sep = "\n%s" % prepend_str
    print_msg.append("%s%s\n" % (prepend_str, sep.join(nlri_text)))

  # Return list of strings representing collected message.
  #
  return print_msg
