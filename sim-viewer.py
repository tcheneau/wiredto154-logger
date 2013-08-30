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

import time, os

# TODO:
# -in an async code:
#   - read the log
#   - read the packet being sent
# - print the node position
# - add node status
# - authentication status
# - add detailed information on the Node

from viewer.entities import SensorMap, Node, Line
import viewer.entities

# pyglet related code

# common colors obtained by subtracting existing ones
S_GREEN = (50, 200, 50)
S_BLUE  = (200, 50, 50)
S_RED   = (50, 50, 200)

# common colors
BLACK = (255, 255, 255)
BLUE  = (0,0,255)

import pyglet
from pyglet.window import key, mouse

sim_window = pyglet.window.Window(caption = "Simulation visualizer", vsync=True, resizable=True)
pyglet.resource.path = ['images']
pyglet.resource.reindex()


on_resize_event_obj = []
on_mouse_motion_event_obj = []

sensor_map = None

@sim_window.event
def on_draw():
    sim_window.clear()
    viewer.entities.batch.draw()

@sim_window.event
def on_key_press(symbol, modifiers):
    if symbol == key.S:
        pyglet.image.get_buffer_manager().get_color_buffer().save(time.strftime("screenshot-%y-%m-%d-%H:%M:%U.png"))
    elif symbol == key.PLUS:
        sensor_map.node_scale_up()
    elif symbol == key.MINUS:
        sensor_map.node_scale_down()
    elif symbol == key.UP:
        sensor_map.view_trans(0,10)
    elif symbol == key.DOWN:
        sensor_map.view_trans(0, -10)
    elif symbol == key.LEFT:
        sensor_map.view_trans(-10, 0)
    elif symbol == key.RIGHT:
        sensor_map.view_trans(10, 0)
    elif symbol == key.R:
        sensor_map.reset_view()

@sim_window.event
def on_mouse_scroll(x, y, scroll_x, scroll_y):
    if scroll_y > 0:
        for i in xrange(scroll_y):
            sensor_map.view_scale_up()
    else:
        scroll_y = - scroll_y
        for i in xrange(scroll_y):
            sensor_map.view_scale_down()

@sim_window.event
def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
    if buttons & mouse.LEFT:
        sensor_map.view_trans(dx, dy)

@sim_window.event
def on_resize(width, height):
    for obj in on_resize_event_obj:
        obj.on_resize(width, height)

@sim_window.event
def on_mouse_motion(x, y, dx, dy):
    for obj in on_mouse_motion_event_obj:
        obj.on_mouse_motion(x, y, dx, dy)


# XML related code
def parse_xml(filename):
    import xml.etree.ElementTree as ET
    tree = ET.parse(os.path.expanduser(filename))
    root = tree.getroot()
    nodes = []
    for node in root.find("nodes").getiterator("node"):
        nodes.append((node.get("id"), float(node.get("x")), float(node.get("y"))))

    return nodes

if __name__ == "__main__":
    # parse arguments
    import argparse
    parser = argparse.ArgumentParser(usage= "display events coming from a wiredto154 simulation",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-f", "--filename", help="simulation file", type=str, default="simulation.xml")
    parser.add_argument("-e", "--emu-addr", help="IP address of the PHY emulator (wiredto154)", default="127.0.0.1")
    parser.add_argument("-a", "--mcast-addr", help="IP address of the multicast group", default="224.1.1.1")
    parser.add_argument("-p", "--mcast-port", help="port to listen on (for the multicast address)", type=int, default=10000)

    args = parser.parse_args()

    print "reading configuration file"
    # read XML file and prepare command line
    nodes = parse_xml(args.filename)

    # initialize graphics
    viewer.entities.init()

    sensor_map = SensorMap()
    on_mouse_motion_event_obj.append(sensor_map)
    on_resize_event_obj.append(sensor_map)
    for (identifier, x, y)  in nodes:
        print "adding node %s (%f, %f)" % (identifier, x, y)
        sensor_map.add_node(Node(identifier, x, y))

    # set background color to white
    pyglet.gl.glClearColor(1, 1, 1, 1)

    pyglet.app.run()
