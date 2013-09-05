"""simulation log message parser"""
import struct, time
from threading import Timer
from tools import PRINT, simulation_end

# protocol constants

OUTBOUND_FRAME = 2 # data messages within the simulation
LOG_HEADER = 128 # events destined to the logger
SIM_END = 3 # server asks for the simulation to end, and thus the logger to shut down
TYPE_ONENODE = 1
TYPE_TWONODES = 2
TYPE_MANYNODES = 3

class mydefaultdict(dict):
    def __missing__(self, key):
        value = self[key] = "unknown-%d" % key
        return value

# define additional types here
onenode_subtypes_l = [(1, "node join"), (2, "node exit"), (3, "node out of sync"),
                      (6, "AKM node state")]
twonode_subtypes_l = [(4, "AKM link state")]
manynode_subtypes_l = []

onenode_subtypes = mydefaultdict()
for subtype, label in onenode_subtypes_l:
      onenode_subtypes[subtype] = label
twonode_subtypes = mydefaultdict()
for subtype, label in twonode_subtypes_l:
    twonode_subtypes[subtype] = label
manynode_subtypes = mydefaultdict()
for subtype, label in manynode_subtypes_l:
    manynode_subtypes[subtype] = label

subtypes = { TYPE_ONENODE: onenode_subtypes,
            TYPE_TWONODES: twonode_subtypes,
            TYPE_MANYNODES: manynode_subtypes}

class TextLogger(object):
    fd = None
    subtype_max_len = 0
    def __init__(self, filename):
        self.start_time = None
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
        if not self.start_time:
            self.start_time = time.time()
        subtype_name = TextLogger.compact_subtypename(subtypes[log['type']][log['subtype']])

        msg = "{0:<18.6f} {1} [{2}] ({3})\n".format(
            time.time() - self.start_time,
            subtype_name + " " * (1 + self.subtype_max_len - len(subtype_name)),
            ", ".join([str(node) for node in log['nodes']]),
            log['data'])
        self.fd.write(msg)
        self.fd.flush()

def dispatcher(data, logger):
    # parse the message
    if len(data) == 1 and ord(data[0]) == SIM_END:
        print "received simulation end message, shutting down simulation in five seconds"
        Timer(5.0, simulation_end).start()
        return

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

def parse_packet(data):
    # frame format:
    # - node_id (2 bytes)
    # - num_good_nodes (2 bytes)
    # - good_node * num_good_nodes (n * 2 bytes)
    # - num_bad_nodes (2 bytes)
    # - bad_node * num_bad_nodes (n * 2 bytes)
    # - misc.data
    good_nodes = []
    bad_nodes = []

    node, = struct.unpack(">H", data[:2])

    offset = 2

    num_good_nodes, = struct.unpack(">H", data[offset:offset + 2])
    offset += 2
    for x in range(num_good_nodes):
        good_nodes.append(struct.unpack(">H", data[offset:offset + 2])[0])
        offset +=  2

    num_bad_nodes, = struct.unpack(">H", data[offset:offset + 2])
    offset += 2
    for x in range(num_bad_nodes):
        bad_nodes.append(struct.unpack(">H", data[offset:offset + 2])[0])
        offset += 2

    return {'node': node, 'good_nodes': good_nodes, 'bad_nodes': bad_nodes}

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

