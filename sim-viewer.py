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

# pyglet related code

# common colors obtained by subtracting existing ones
GREEN = (50, 200, 50)
BLUE = (200, 50, 50)
RED = (50, 50, 200)

import pyglet
from pyglet.window import key, mouse

sim_window = pyglet.window.Window(caption = "Simulation visualizer", vsync=True, resizable=True)
pyglet.resource.path = ['images']
pyglet.resource.reindex()
batch = pyglet.graphics.Batch()

on_resize_event_obj = []

sensor_map = None

@sim_window.event
def on_draw():
    sim_window.clear()
    batch.draw()

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

# XML related code
def parse_xml(filename):
    import xml.etree.ElementTree as ET
    tree = ET.parse(os.path.expanduser(filename))
    root = tree.getroot()
    nodes = []
    for node in root.find("nodes").getiterator("node"):
        nodes.append((node.get("id"), float(node.get("x")), float(node.get("y"))))

    return nodes

class SensorNode(pyglet.sprite.Sprite):
    def __init__(self, *args, **kwargs):
        super(SensorNode, self).__init__(img=pyglet.resource.image('node.png'),
                                         *args[1:],
                                         **kwargs)
        self.anchor_x = self.width/2
        self.anchor_y = self.height/2

class NodeStatus(pyglet.sprite.Sprite):
    def __init__(self, *args, **kwargs):
        super(NodeStatus, self).__init__(img=pyglet.resource.image('status.png'),
                                         *args[1:],
                                         **kwargs)

class Status():
    pass

class Node(object):
    def __init__(self, identifier, x, y):
        self.identifier = identifier
        self.x = x
        self.y = y

    def __str__(self):
        return "\n".join(self.identifier, str(self.x), str(self.y))

class SensorMap(object):
    def __init__(self):
        self.x_min = 0
        self.y_min = 0
        self.x_max = 0
        self.y_max = 0
        self.node_scale = 0.4
        self.nodes = []
        self.nodes_img = []
        self.nodes_status = []
        self.nodes_label = []
        self.view_scale = 1
        self.view_trans_x = 0
        self.view_trans_y = 0

    def add_node(self, node):
        self.nodes.append(node)
        sensor_node = SensorNode(batch=batch)
        sensor_node.scale=self.node_scale
        sensor_status = NodeStatus(batch=batch)
        sensor_status.scale=self.node_scale
        label = pyglet.text.Label(text=node.identifier,
                                  anchor_x='center',
                                  anchor_y='center',
                                  color=(0,0,0,255),
                                  batch=batch)
        self.nodes_img.append(sensor_node)
        self.nodes_label.append(label)
        self.nodes_status.append(sensor_status)
        self.compute_bounding_box()

    def compute_bounding_box(self):
        x_min, y_min, x_max, y_max = 0, 0, 0, 0

        for node in self.nodes:
            if node.x < x_min:
                x_min = node.x
            if node.x > x_max:
                x_max = node.x
            if node.y < y_min:
                y_min = node.y
            if node.y > y_max:
                y_max = node.y

        self.x_min, self.y_min, self.x_max, self.y_max = x_min, y_min, x_max, y_max

    def node_change_color(self, identifier, color):
        for (i, node) in enumerate(self.nodes):
            if node.identifier == identifier:
                print "found it"
                self.nodes_img[i].color = color
                break

    def reset_view(self):
        self.view_scale = 1
        self.view_trans_x = 0
        self.view_trans_y = 0

        self.refresh_view_with_params(self.width, self.height)

    def view_trans(self, x, y):
        self.view_trans_x += x
        self.view_trans_y += y

        self.refresh_view_with_params(self.width, self.height)

    def view_scale_up(self):
        self.view_scale += 0.1

        self.refresh_view_with_params(self.width, self.height)

    def view_scale_down(self):
        if self.view_scale > 0.1:
            self.view_scale -= 0.1

            self.refresh_view_with_params(self.width, self.height)
        else:
            self.view_scale = 0.1

    def node_scale_up(self):
        self.node_scale += 0.05
        for (i, node) in enumerate(self.nodes):
            self.nodes_img[i].scale = self.node_scale
            self.nodes_status[i].scale = self.node_scale

        self.refresh_view_with_params(self.width, self.height)

    def node_scale_down(self):
        if self.node_scale > 0.05:
            self.node_scale -= 0.05
            for (i, node) in enumerate(self.nodes):
                self.nodes_img[i].scale = self.node_scale
                self.nodes_status[i].scale = self.node_scale

            self.refresh_view_with_params(self.width, self.height)
        else:
            self.node_scale = 0.05

    def compute_fit_map_to_window_params(self, width, height):
        """compute translation and scale factors to map the bounding box to a specific area"""
        map_width = self.x_max - self.x_min
        map_height = self.y_max - self.y_min

        if map_width == 0:
            scale_x = 1
        else:
            scale_x = float(width)/map_width

        if map_height == 0:
            scale_y = 1
        else:
            scale_y = float(height)/map_height

        trans_x = - self.x_min
        trans_y = - self.y_min

        return min(scale_x, scale_y), trans_x, trans_y

    def refresh_view_with_params(self, width, height):
        if len(self.nodes):
            scale, trans_x, trans_y = self.compute_fit_map_to_window_params(width - self.nodes_img[0].width,
                                                                            height - self.nodes_img[0].height)
            self.apply_tranform(scale, trans_x, trans_y)

    def apply_tranform(self, scale, trans_x, trans_y):
        for (i, node) in enumerate(self.nodes):
            # the nodes image
            self.nodes_img[i].x = self.view_scale * scale * (node.x + trans_x) + self.view_trans_x
            self.nodes_img[i].y = self.view_scale * scale * (node.y + trans_y) + self.view_trans_y
            # the nodes_label must be inside the node
            self.nodes_label[i].x = self.view_scale * scale * (node.x + trans_x) + self.view_trans_x + self.nodes_img[i].width // 2
            self.nodes_label[i].y = self.view_scale * scale * (node.y + trans_y) + self.view_trans_y + self.nodes_img[i].height // 2
            # status is on the upper right corner of the image
            self.nodes_status[i].x = self.view_scale * scale * (node.x + trans_x) + self.view_trans_x + \
                                     self.nodes_img[i].width - self.nodes_status[i].width
            self.nodes_status[i].y = self.view_scale * scale * (node.y + trans_y) + self.view_trans_y + \
                                     self.nodes_img[i].height - self.nodes_status[i].height

    def update(self, dt):
        pass

    def on_resize(self, width, height):
        self.width = width
        self.height = height

        self.refresh_view_with_params(width, height)


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
    sensor_map = SensorMap()
    on_resize_event_obj.append(sensor_map)
    for (identifier, x, y)  in nodes:
        print "adding node %s (%f, %f)" % (identifier, x, y)
        sensor_map.add_node(Node(identifier, x, y))

    # set background color to white
    pyglet.gl.glClearColor(1, 1, 1, 1)

    pyglet.app.run()
