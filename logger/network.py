"""network code for listening to simulation events"""

from socket import inet_pton, AF_INET, AF_INET6, \
        SOCK_DGRAM, IPPROTO_IP, IPPROTO_UDP, IPPROTO_IPV6, \
        IPV6_JOIN_GROUP, SOL_SOCKET, \
        SO_REUSEADDR, INADDR_ANY, IP_ADD_MEMBERSHIP
import socket, struct

def multicast_listener(address, port):
    """start a multicast listener on the specified address and port
    or throw an exception trying"""

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
