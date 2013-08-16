#!/bin/env python

# Conditions Of Use
#
# This software was developed by employees of the National Institute of
# Standards and Technology (NIST), and others.
# This software has been contributed to the public domain.
# Pursuant to title 15 United States Code Section 105, works of NIST
# employees are not subject to copyright protection in the United States
# and are considered to be in the public domain.
# As a result, a formal license is not needed to use this software.
#
# This software is provided "AS IS."
# NIST MAKES NO WARRANTY OF ANY KIND, EXPRESS, IMPLIED
# OR STATUTORY, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT
# AND DATA ACCURACY.  NIST does not warrant or make any representations
# regarding the use of the software or the results thereof, including but
# not limited to the correctness, accuracy, reliability or usefulness of
# this software.

from signal import signal, SIGINT
from collections import defaultdict
from sys import stdout
import socket, time, struct, itertools

# global variables
logger = None

# protocol constants

LOG_HEADER = 128 # events destined to the logger
TYPE_ONENODE = 1
TYPE_TWONODES = 2
TYPE_MANYNODES = 3

def constant_factory(value):
    return itertools.repeat(value).next

onenode_subtypes = defaultdict(constant_factory("unknown"))
onenode_subtypes_l = [(1, "node join"), (2, "node exit"), (3, "node out of sync")]
for subtype, label in onenode_subtypes_l:
      onenode_subtypes[subtype] = label
twonode_subtypes = defaultdict(constant_factory("unknown"))
twonode_subtypes_l = []
for subtype, label in twonode_subtypes_l:
    twonode_subtypes[subtype] = label
manynode_subtypes = defaultdict(constant_factory("unknown"))
manynode_subtypes_l = []
for subtype, label in manynode_subtypes_l:
    manynode_subtypes[subtype] = label

subtypes = { TYPE_ONENODE: onenode_subtypes,
            TYPE_TWONODES: twonode_subtypes,
            TYPE_MANYNODES: manynode_subtypes}

def PRINT(* args): pass
def verbose_print(* args):
    """a more verbose print"""
    for arg in args:
        print arg,
    print

class prettyfile(object):
    """a class of file that prints out nicely when str() or repr() is called"""
    fileobj = None
    def __init__(self, fileobj):
        self.fileobj = fileobj
    def __str__(self):
        return self.fileobj.name
    def write(self, data):
        self.fileobj.write(data)

def multicast_listener(address, port):
    """start a multicast listener on the specified address and port
    or throw an exception trying"""
    from socket import inet_pton, AF_INET, AF_INET6, \
            SOCK_DGRAM, IPPROTO_IP, IPPROTO_UDP, IPPROTO_IPV6, \
            IPV6_JOIN_GROUP, SOL_SOCKET, \
            SO_REUSEADDR, INADDR_ANY, IP_ADD_MEMBERSHIP

    sock = None

    try:
        inet_pton(AF_INET, address)
        address_type = "IPv4"
    except socket.error:
        try:
            inet_pton(AF_INET6, address)
            address_type = "IPv6"
        except: # could not parse the address
            return sock

    if address_type == "IPv4":
        sock = socket.socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        sock.bind(('', port))
        mreq = struct.pack("4sl", inet_pton(AF_INET, address), INADDR_ANY)
        sock.setsockopt(IPPROTO_IP, IP_ADD_MEMBERSHIP, mreq)
    else: # IPv6
        sock = socket.socket(AF_INET6, SOCK_DGRAM, IPPROTO_UDP)
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        sock.bind(('',port))
        mreq = inet_pton(AF_INET6, address)
        ifn = struct.pack("I", 0) # system choses the interface
        # if we wanted to constrain to a specific interface
        # sock.setsockopt(IPPROTO_IPV6, IPV6_MULTICAST_IF, ifn)
        sock.setsockopt(IPPROTO_IPV6, IPV6_JOIN_GROUP, mreq + ifn)

    return sock


class TextLogger(object):
    fd = None
    subtype_max_len = 0
    def __init__(self, filename):
        if isinstance(filename, str):
            self.fd = open(filename, mode='w')
        else: # if we pass a file descriptor directly
            self.fd = filename
        subtype_names = [TextLogger.compact_subtypename(subtype) for m_type in subtypes.values()\
                         for subtype in m_type.values()]
        self.subtype_max_len = max(map(len, subtype_names))

    @staticmethod
    def compact_subtypename(type_name):
        return "".join(type_name.upper().split())

    def write(self, log):
        subtype_name = TextLogger.compact_subtypename(subtypes[log['type']][log['subtype']])

        msg = "{0:<18.6f} {1} [{2}] ({3})\n".format(
            time.time(),
            subtype_name + " " * (1 + self.subtype_max_len - len(subtype_name)),
            ", ".join([str(node) for node in log['nodes']]),
            log['data'])
        self.fd.write(msg)
        self.fd.flush()


def dispatcher(data):
    # parse the message
    if len(data) <= 4 or ord(data[0]) != LOG_HEADER :
        return

    # log the event accordingly
    m_type = ord(data[1])
    try:
        if m_type == TYPE_ONENODE:
            log_entry = parse_onenode(data[2:])
        elif m_type == TYPE_TWONODES:
            log_entry = parse_twonodes(data[2:])
        elif m_type == TYPE_MANYNODES:
            log_entry = parse_manynodes(data[2:])
        else:
            PRINT("message type %d is not recognized")
            return
        log_entry['type'] = m_type
    except struct.error:
        PRINT("could not parse message of type %d" % m_type)
        return

    logger.write(log_entry)
    try:
        pass
    except:
        PRINT("could not write to the logger")

def parse_onenode(data):
    d_format = "!BH"
    subtype, node_id= struct.unpack(d_format, data[:struct.calcsize(d_format)])
    data = data[struct.calcsize(d_format):]
    PRINT("parsing a one node event for node %d" % node_id)
    return { 'subtype': subtype, 'nodes': [node_id], 'data': data }

def parse_twonodes(data):
    d_format = "!BHH"
    subtype, node_a_id, node_b_id = struct.unpack(d_format, data[:struct.calcsize(d_format)])
    data = data[struct.calcsize(d_format):]
    PRINT("parsing a two nodes event between node %d and node %d" % (node_a_id, node_b_id))
    return { 'subtype': subtype, 'nodes': [node_a_id, node_b_id], 'data': data }

def parse_manynodes(data):
    d_format = "!BH"
    subtype, n_nodes = struct.unpack(d_format, data[:struct.calcsize(d_format)])
    nodes = []
    offset = struct.calcsize(d_format)

    for node in xrange(n_nodes):
        (node_id,) = struct.unpack("!H", data[offset + node*2: offset + node*2 +2])
        nodes.append(node_id)

    data = data[offset + node*2 + 2:]
    PRINT("parsing a many nodes event")
    return { 'subtype': subtype, 'nodes': nodes, 'data': data }

def sig_handler(signal, frame):
    pass

if __name__ == "__main__":
    import argparse
    stdout = prettyfile(stdout)
    parser = argparse.ArgumentParser(usage= "log events coming from a wiredto154 simulation",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-f", "--filename", help="output file", type=str, default=stdout)
    parser.add_argument("-a", "--address", help="IP address of the multicast group", default="224.1.1.1")
    parser.add_argument("-p", "--port", help="port to listen on", type=int, default=10000)
    parser.add_argument("-v", "--verbose", help="make this tool more verbose", action="store_true")

    args = parser.parse_args()

    if args.verbose:
        PRINT = verbose_print

    # set the signal to end the process gracefully
    signal(SIGINT, sig_handler)

    logger = TextLogger(args.filename)

    sock = multicast_listener(args.address, args.port)

    processing = True

    print "starting logger loop (hit CTRL+C to exit)"

    while processing:
        try:
            PRINT("waiting for a new multicast message")
            data, addr = sock.recvfrom(65535)
            if data:
                PRINT("received %d bytes" % len(data))
            else:
                processing = False
        except socket.error:
            processing = False
            continue

        dispatcher(data)

    print "program is exiting gracefully"

