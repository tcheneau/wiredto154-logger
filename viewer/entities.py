"""Contains the various entities that will be displayed during the simulation"""
import pyglet
import math
from trig_tools import compute_angle, compute_arrow_points

batch = None

# common colors
HARD_BLACK = (0, 0, 0, 255)
HARD_BLUE  = (0, 0, 255, 255)
TRANSPARENT_RED = (255, 0, 0, 125)
TRANSPARENT_GREEN = (0, 255, 0, 125)
TRANSPARENT_BLUE = (0, 0, 255, 125)

class Layers(object):
    """class that contains displayable layers"""
    background   = pyglet.graphics.OrderedGroup(0)
    middleground = pyglet.graphics.OrderedGroup(1)
    foreground   = pyglet.graphics.OrderedGroup(2)


class Overlay(object):
    """Overlay that is displayed on top of the node"""
    def __init__(self, x, y, string):
        self.box = pyglet.sprite.Sprite(img=pyglet.resource.image('box.png'), x=x, y=y,
                                        group=Layers.foreground, batch=batch)
        self.box.x = self.box.x - self.box.width//2
        self.box.y = self.box.y - self.box.height//2
        self.label = pyglet.text.Label(text=string,
                                       x=x,
                                       y=y,
                                       multiline=True,
                                       width= 0.9 * self.box.width,
                                       anchor_x='center',
                                       anchor_y='center',
                                       color=(0,0,0,255),
                                       group=Layers.foreground,
                                       batch=batch)
    @property
    def width(self):
        return self.box.width

    @property
    def height(self):
        return self.box.height

    def delete(self):
        self.box.delete()
        self.box = None
        self.label.delete()
        self.label = None

class NodeStatus(pyglet.sprite.Sprite):
    def __init__(self, *args, **kwargs):
        super(NodeStatus, self).__init__(img=pyglet.resource.image('status.png'),
                                         *args[1:],
                                         **kwargs)

class Node(object):
    def __init__(self, identifier, x, y):
        self.identifier = identifier
        self.x = x
        self.y = y

    def __str__(self):
        return "x: {0}\ny: {1}\n".format(self.x, self.y)

    def apply_tranform(self, scale, trans_x, trans_y, view_trans_x, view_trans_y):
        return (scale * (self.x + trans_x) + view_trans_x,
                scale * (self.y + trans_y) + view_trans_y)

class SensorNode(pyglet.sprite.Sprite):
    def __init__(self, node_info, *args, **kwargs):
        self.node_info = node_info
        self.node_img = pyglet.sprite.Sprite(img=pyglet.resource.image('node.png'),
                                             group=Layers.middleground,
                                             batch=batch)
        self.node_status = NodeStatus(group=Layers.middleground,
                                      batch=batch)
        self.node_label = pyglet.text.Label(text=node_info.identifier,
                                            anchor_x='center',
                                            anchor_y='center',
                                            color=(0,0,0,255),
                                            group=Layers.middleground,
                                            batch=batch)
        self.overlay = None
        self.center_x = self.node_img.width/2
        self.center_y = self.node_img.height/2

    def get_scale(self):
        return self._scale
    def set_scale(self, value):
        self._scale = value
        self.node_img.scale = value
        self.node_status.scale = value
        self.center_x = self.node_img.width/2
        self.center_y = self.node_img.height/2
    scale = property(get_scale, set_scale)

    @property
    def x(self):
        return self.node_info.x

    @property
    def y(self):
        return self.node_info.y

    @property
    def width(self):
        width, height = self.compute_bounding_box()
        return width

    @property
    def height(self):
        width, height = self.compute_bounding_box()
        return height

    def on_mouse_motion(self, x, y, dx, dy):
        if self.node_img.x < x < self.node_img.x + self.width and  \
           self.node_img.y < y < self.node_img.y + self.height:
            self.enable_overlay(str(self.node_info))
        else:
            self.disable_overlay()

    def enable_overlay(self, string):
        if not self.overlay:
            self.overlay = Overlay(self.node_img.x + self.width//2,
                                   self.node_img.y + self.height//2,
                                   string)

    def disable_overlay(self):
        if self.overlay:
            self.overlay.delete()
            self.overlay = None

    def compute_bounding_box(self):
        """return the size of the bounding box for the object"""
        objs = [self.node_img, self.node_status, self.node_label]
        sizes_x, sizes_y = zip(*[(obj.width, obj.height) for obj in  objs if obj])
        return (max(sizes_x), max(sizes_y))

    def apply_tranform(self, scale, trans_x, trans_y, view_trans_x, view_trans_y):
        self.node_img.x = scale * (self.node_info.x + trans_x) + view_trans_x
        self.node_img.y = scale * (self.node_info.y + trans_y) + view_trans_y
        # the node_label must be inside the node
        self.node_label.x = scale * (self.node_info.x + trans_x) + view_trans_x + self.center_x
        self.node_label.y = scale * (self.node_info.y + trans_y) + view_trans_y + self.center_y
        # status is on the upper right corner of the image
        self.node_status.x = scale * (self.node_info.x + trans_x) + view_trans_x + \
                                    self.node_img.width - self.node_status.width
        self.node_status.y = scale * (self.node_info.y + trans_y) + view_trans_y + \
                                    self.node_img.height - self.node_status.height

class SensorMap(object):
    """Display the sensor in simulation area"""
    def __init__(self):
        self.x_min = 0
        self.y_min = 0
        self.x_max = 0
        self.y_max = 0
        self.node_scale = 0.4
        self.lines = {}
        self.nodes = []
        self.view_scale = 1
        self.view_trans_x = 0
        self.view_trans_y = 0

    def add_node(self, node_info):
        sensor_node = SensorNode(node_info)
        sensor_node.scale=self.node_scale
        self.nodes.append(sensor_node)
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

    def node_lookup(self, identifier):
        """returns the node corresponding to the identifier or None if no node
        is found"""
        node = None
        for n in self.nodes:
            if n.node_info.identifier == identifier:
                node = n
                break
        return node

    def node_change_color(self, identifier, color):
        node = self.node_lookup(identifier)
        if node:
            node.nodes_img.color = color
        else:
            raise "node %s does not exists" % identifier

    def line_add(self, A, B, thickness = 4, color = HARD_BLACK):
        """draw a line between node A and node B according to their simulation identifiers"""
        nodeA = self.node_lookup(A)
        nodeB = self.node_lookup(B)

        if nodeA and nodeB:
            line_id = (nodeA, nodeB) if A < B else (nodeB, nodeA)
            # the following call actually does not print much
            line = Line(thickness=thickness, color=color)
            line.add_batch(batch)
            self.lines[line_id] = line
        else:
            raise "%s or %s is not part of the simulation" % (A, B)

    def line_del(self, A, B):
        nodeA = self.node_lookup(A)
        nodeB = self.node_lookup(B)

        if nodeA and nodeB:
            line_id = (nodeA, nodeB) if A < B else (nodeB, nodeA)
            if self.lines[line_id]:
                self.lines[line_id].delete()
                del self.lines[line_id]


    def arrows_create(self, source, destinations, lifetime=.2, color = HARD_BLACK):
        coordinates = []
        A = self.node_lookup(source)
        for destination in destinations:
            B = self.node_lookup(destination)
            coordinates.append(((A.node_img.x + A.center_x, A.node_img.y + A.center_y),
                                (B.node_img.x + B.center_x, B.node_img.y + B.center_y)))

        return ArrowGroup(coordinates, lifetime, color)


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
            self.nodes[i].scale = self.node_scale

        self.refresh_view_with_params(self.width, self.height)

    def node_scale_down(self):
        if self.node_scale > 0.05:
            self.node_scale -= 0.05
            for (i, node) in enumerate(self.nodes):
                self.nodes[i].scale = self.node_scale

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
            node_size_x, node_size_y = self.nodes[0].compute_bounding_box()
            scale, trans_x, trans_y = self.compute_fit_map_to_window_params(width - node_size_x,
                                                                            height - node_size_y)
            self.apply_tranform(self.view_scale * scale, trans_x, trans_y)

    def apply_tranform(self, scale, trans_x, trans_y):
        # update the nodes
        for node in self.nodes:
            node.apply_tranform(scale, trans_x, trans_y, self.view_trans_x, self.view_trans_y)
        # update the lines
        for nodes, line in self.lines.iteritems():
            node_A, node_B = nodes
            new_A = node_A.node_info.apply_tranform(scale,
                                                    trans_x,
                                                    trans_y,
                                                    self.view_trans_x  + node_A.center_x,
                                                    self.view_trans_y + node_A.center_y)
            new_B = node_B.node_info.apply_tranform(scale,
                                                    trans_x,
                                                    trans_y,
                                                    self.view_trans_x + node_B.center_x,
                                                    self.view_trans_y + node_B.center_y)
            line.update_coordinates(new_A, new_B)

    def update(self, dt):
        pass

    def on_resize(self, width, height):
        self.width = width
        self.height = height

        self.refresh_view_with_params(width, height)

    def on_mouse_motion(self, x, y, dx, dy):
        for node in self.nodes:
            node.on_mouse_motion(x, y, dx, dy)

class Line(object):
    """draw a line"""
    def __init__(self, A=(0.,0.), B=(0.,0.), thickness=6, color=HARD_BLACK):
        self.A = A
        self.B = B
        self.thickness = thickness
        self.color = color
        self.vertexlist = None

    def delete(self):
        if self.vertexlist:
            self.vertexlist.delete()

    def add_batch(self, batch):
        """draw a line"""
        x_A, y_A = self.A
        x_B, y_B = self.B
        pyglet.gl.glLineWidth(self.thickness)
        self.vertexlist = batch.add(2,pyglet.gl.GL_LINES,Layers.background,
                                   ('v2f', (x_A, y_A, x_B, y_B)),
                                   ('c4B', 2 * self.color))
        return self.vertexlist

    def update_coordinates(self, A, B):
        self.A = A
        self.B = B
        self.delete()
        self.add_batch(batch)

class Arrow(Line):
    """draw a line with a dot on the destination end (B)"""
    def __init__(self, * args, ** kwargs):
        super(Arrow, self).__init__(*args, **kwargs)
        self.vertexlist = []

    def delete(self):
        for obj in self.vertexlist:
            obj.delete()
        self.vertexlist = []

    def add_batch(self, batch):
        x_A, y_A = self.A
        x_B, y_B = self.B
        pyglet.gl.glLineWidth(self.thickness)

        C, D = compute_arrow_points(self.A, self.B, radius=14)
        x_C, y_C = C
        x_D, y_D = D

        # end the line a little bit before B
        angle_ab = compute_angle(self.A, self.B)
        line = batch.add(2,pyglet.gl.GL_LINES,Layers.foreground,
                         ('v2f', (x_B - math.cos(angle_ab) * 10,
                                  y_B - math.sin(angle_ab) * 10, x_A, y_A)),
                         ('c4B', 2 * self.color))
        arrow_tip = batch.add(3, pyglet.gl.GL_TRIANGLES,Layers.foreground,
                              ('v2f', (x_B, y_B, x_D, y_D, x_C, y_C)),
                              ('c4B', 3 * self.color))

        self.vertexlist.append(line)
        self.vertexlist.append(arrow_tip)
        return self.vertexlist

class ArrowGroup(object):
    """regroup multiple arrows together"""
    def __init__(self, coordinates, lifetime=1, color=HARD_BLACK):
        self.arrows = []
        for X, Y in coordinates:
            arrow = Arrow(X, Y, color=color)
            arrow.add_batch(batch)
            self.arrows.append(arrow)

        pyglet.clock.schedule_once(self.die, lifetime)

    def die(self, dt):
        for arrow in self.arrows:
            arrow.delete()


from pyglet.gl import *
def init():
    global batch
    batch = pyglet.graphics.Batch()

    #enable alpha blending
    glEnable(GL_BLEND)
    glShadeModel(GL_SMOOTH)
    glBlendFunc(GL_SRC_ALPHA,GL_ONE)
    glDisable(GL_DEPTH_TEST)
