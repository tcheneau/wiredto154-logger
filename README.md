Logging tool for wiredto154 simulations
=======================================

This document describes a logger tool works alongside *[wiredto154][]* simulation.

This tool was written to parse logging message of one of our research item
(the Adaptive Keying Management protocol) and probably needs to be adapted to
match one's need. It has been written with adaptability in mind.

Rationale
---------

In a simulation, all participating nodes need to report *events* so as to
monitor various aspects, such as their actions or their current state.
In order to gather the event from different node in near real-time, we choose a
multicast based approach with a logger listening on the multicast group. This
is because participating nodes already belong to a  multicast group and have a
multicast-enabled socket. That way, the logger can be placed anywhere in the
network and will not slow down the simulation.

Format of the logging messages
------------------------------

This section describes the general format of the logging messages.
Unless mentioned otherwise, the following rules always apply:

* byte ordering is big endian
* a node identifier is stored on 2 bytes

### Generic format

      0                   1                   2                   3
      0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     | Message Type  |   Entry Type  | Entry Sub-Type|    Data       |
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     |                                                               |
     .                                                               .
     .                        Data (continued)                       .
     .                                                               .
     |                                                               |
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

* *Message Type* indicates this is a logging message. This value is reserved and is 128.
* *Entry Type* indicates the type of entry: one node event, two nodes event, many nodes event.
* *Data* is the payload associated with the *entry type*, it can be an ASCII encoded
  string or arbitrary binary data. It is not processed before being stored.

### One node event

A single node, whose Identifier is *Node ID*, report an event.

      0                   1                   2                   3
      0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     | 132 (MT)      | 1 (Entry Type)| Entry Sub-Type|  Node ID ...  |
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     | Node ID (ct'd)|                Data                           |
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     |                                                               |
     .                                                               .
     .                        Data (continued)                       .
     .                                                               .
     |                                                               |
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

* *Entry Type* is 1
* *Node ID* is the ID of the node

#### Node joining simulation event

* Entry Sub-Type is 1.
* no *data* follows

#### Node leaving simulation event

* Entry Sub-Type is 2.
* no *data* follows

#### Node out of synchronization event

* Entry Sub-Type is 3.
* no *data* follows

### Two nodes event

A node (node A) report an event that occurred between him and a second node (node B).

      0                   1                   2                   3
      0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     | 132 (MT)      | 1 (Entry Type)| Entry Sub-Type|Node A ID ...  |
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     |Node A ID(ct'd)|          Node B ID            | Data          |
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     |                                                               |
     .                                                               .
     .                           Data (continued)                    .
     .                                                               .
     |                                                               |
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

* *Entry Type* is 2

### Many nodes event

A node (node A) report an event that occurred between him and a group of nodes.

      0                   1                   2                   3
      0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     | 132 (MT)      | 3 (Entry Type)| Entry Sub-Type| # of Nodes    |
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     | # of N. (ct'd)|        Node A ID              | Node B ID     |
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     |Node B ID(ct'd)|       [Node C ID]             |[Add Node IDs] .
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     |                                                               |
     .                                                               .
     .           [Additional Node IDs (continued)]                   .
     .                                                               .
     |                                                               |
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     |                                                               |
     .                                                               .
     .                           Data                                .
     .                                                               .
     |                                                               |
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

* *Entry Type* is 3
* \# *of nodes* represents the number of nodes. The value of this field must be at least 1.
* *Node A ID* represents the Node Identifier of the node who reported the event.


Usage
-----

    usage: Log events coming from a wiredto154 simulation
    
    optional arguments:
      -h, --help            show this help message and exit
      -f FILENAME, --filename FILENAME
                            output file (default: <stdout>)
      -a ADDRESS, --address ADDRESS
                            IP address of the multicast group (default: 224.1.1.1)
      -p PORT, --port PORT  port to listen on (default: 10000)
      -v, --verbose         make this tool more verbose (default: False)

Example of use
--------------

If the simulation sends its event on the default multicast address and default port
and you want to see the output of the logger on the standard output (stdout),
you can run the logger with no parameters:

    ./logger.py

If your simulation sends event on the address 224.2.2.2 and port 5000 and you
want the output to be stored in a file named "log.txt":

    ./logger.py -a 224.2.2.2 -p 5000 -f log.txt

The logger.py will exit gracefully upon receiving the interrupt signal (Ctrl+C).

Calling the logging API from Contiki
------------------------------------

We are currently working on an extension of the Contiki native target to use
UDP communication and connect to [wiredto154][]. This code also contains API to
log messages using the logging facilities described in this page.

In order to use logging messages, you must include the logging header:

    #include <sys/logger.h>

You can then call any of the following function (depending on the situation):

* *int log_msg_one_node(uint8_t subtype, char * msg, size_t msg_len)*
    * log message involving only this node (the node calling this function)
    * *subtype* describes the subtype of message, it could be any of the sub-types
      defined above, or a completely different one (in this case you might want to
      extend logger.py to print out this message name more nicely)
    * *msg* is a string and *msg_len* is its size

* *int log_msg_two_nodes(uint8_t subtype, uint16_t other_node_id, char * msg, size_t msg_len)*
    * log message involving two nodes (the node calling this function and other_node_id)
    * *subtype* describes the subtype of message. No reserved values defined so far, feel free to define them in logger.py.
    * *msg* is a string and *msg_len* is its size

* *int log_msg_many_nodes(uint8_t subtype, uint16_t * other_nodes_id, char * msg, size_t msg_len)*
    * log message involving multiple nodes (the node calling this function and other_nodes_id)
    * *subtype* describes the subtype of message. No reserved values defined so far, feel free to define them in logger.py.
    * *other_nodes_id* contains the list of nodes being involved (this array must end with 0)
    * *msg* is a string and *msg_len* is its size



[wiredto154]: https://github.com/tcheneau/wiredto154
