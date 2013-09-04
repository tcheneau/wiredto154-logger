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

# Tony Cheneau <tony.cheneau@nist.gov>

from signal import signal, SIGINT
from sys import stdout
from logger.network import multicast_listener
from logger.parser import dispatcher, TextLogger
from logger.tools import PRINT, verbose_print
import socket

class prettyfile(object):
    """a class of file that prints out nicely when str() or repr() is called"""
    fileobj = None
    def __init__(self, fileobj):
        self.fileobj = fileobj
    def __str__(self):
        return self.fileobj.name
    def write(self, data):
        self.fileobj.write(data)
    def flush(self):
        self.fileobj.flush()


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

    print "starting logger loop (hit CTRL+C to exit)"

    processing = True

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

        dispatcher(data, logger)

    print "program is exiting gracefully"

