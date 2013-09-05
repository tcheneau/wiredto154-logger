import pyglet
import socket, struct

from logger.network import multicast_listener
from logger.parser import LOG_HEADER, OUTBOUND_FRAME,\
                          parse_packet, \
                          parse_onenode, parse_twonodes, parse_manynodes, \
                          TYPE_ONENODE, TYPE_TWONODES, TYPE_MANYNODES
from logger.tools import PRINT
from entities import S_GREEN, S_RED, TRANSPARENT_GREEN, TRANSPARENT_GREY, \
                     HARD_GREY, HARD_RED, HARD_BLUE

class Dispatcher(object):
    def __init__(self, address, port, sensor_map):
        self.sensor_map = sensor_map
        self.sock = multicast_listener(address, port)
        self.sock.setblocking(False)
        pyglet.clock.schedule_interval(self.process_packet, 1./60)

    def process_packet(self, dt):
        data = True
        while data:
            try:
                data, addr = self.sock.recvfrom(65535)
            except socket.error: # if the socket is empty
                return

            if data:
                self.dispatch(data)

    def dispatch(self, data):
        if ord(data[0]) == LOG_HEADER:
            PRINT("parsing log message")
            self.dispatch_log(data)
        elif ord(data[0]) == OUTBOUND_FRAME:
            PRINT("parsing data frame")
            self.dispatch_packet(data)

    def dispatch_packet(self, data):
        if len(data) <= 4:
            return
        self.animate_packet(parse_packet(data[1:]))

    def dispatch_log(self, data):
        if len(data) <= 4:
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

        self.animate_log(log_entry)

    def animate_packet(self, packet_info):
        node = packet_info['node']
        good_nodes = packet_info['good_nodes']
        bad_nodes = packet_info['bad_nodes']
        if good_nodes or bad_nodes:
            # good nodes in green
            self.sensor_map.arrows_create(node, good_nodes, lifetime = 0.4, color = TRANSPARENT_GREEN)
            # bad nodes in grey
            self.sensor_map.arrows_create(node, bad_nodes, lifetime = 0.4, color = TRANSPARENT_GREY)

    def animate_log(self, entry):
        subtype = entry['subtype']
        if subtype == 1: # node join
            PRINT("node %d joins simulation" % entry['nodes'][0])
            self.sensor_map.node_status_change_color(entry['nodes'][0], S_GREEN)
        elif subtype == 2: # node leaves
            PRINT("node %d leaves simulation" % entry['nodes'][0])
            self.sensor_map.node_status_change_color(entry['nodes'][0], S_RED)
        elif subtype == 4: # AKM link authentication state
            if entry['data'] == "AUTHENTICATED":
                self.sensor_map.line_add(entry['nodes'][0], entry['nodes'][1])
            elif entry['data'] == "PENDING_SEND_CHALLENGE": # on hold for sending beacon
                self.sensor_map.line_add(entry['nodes'][0], entry['nodes'][1], color=HARD_RED)
            elif entry['data'] == "CHALLENGE_SENT_WAITING_FOR_OK": # you sent a challenge, and wait for a reply
                self.sensor_map.line_add(entry['nodes'][0], entry['nodes'][1], color=HARD_BLUE)
            elif entry['data'] == "OK_SENT_WAITING_FOR_ACK": # challenge went fine, waiting for the node to ACK the authentication
                self.sensor_map.line_add(entry['nodes'][0], entry['nodes'][1], color=HARD_GREY)
            elif entry['data'] == "UNAUTHENTICATED":
                self.sensor_map.line_del(entry['nodes'][0], entry['nodes'][1])
        elif subtype == 6: # AKM node authentication state
            if entry['data'] == "AUTHENTICATED":
                self.sensor_map.node_change_color(entry['nodes'][0], S_GREEN)
            elif entry['data'] == "UNAUTHENTICATED":
                self.sensor_map.node_change_color(entry['nodes'][0], S_RED)




