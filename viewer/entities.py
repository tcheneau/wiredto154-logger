"""Contains the various entities that will be displayed during the simulation"""
import pyglet

batch = None

# common colors
BLACK = (255, 255, 255)
BLUE  = (0,0,255)

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
    def delete(self):
        self.box.delete()
        self.box = None
        self.label.delete()
        self.label = None


class SensorNode(pyglet.sprite.Sprite):
    def __init__(self, node, *args, **kwargs):
        super(SensorNode, self).__init__(img=pyglet.resource.image('node.png'),
                                         *args[1:],
                                         **kwargs)
        self.node = node
        self.anchor_x = self.width/2
        self.anchor_y = self.height/2
        self.overlay = None

    def on_mouse_motion(self, x, y, dx, dy):
        if self.x < x < self.x + self.width and  \
           self.y < y < self.y + self.height:
            self.enable_overlay(str(self.node))
        else:
            self.disable_overlay()

    def enable_overlay(self, string):
        if not self.overlay:
            self.overlay = Overlay(self.x + self.width//2,
                                   self.y + self.height//2,
                                   string)

    def disable_overlay(self):
        if self.overlay:
            self.overlay.delete()
            self.overlay = None

class NodeStatus(pyglet.sprite.Sprite):
    def __init__(self, *args, **kwargs):
        super(NodeStatus, self).__init__(img=pyglet.resource.image('status.png'),
                                         group = Layers.middleground,
                                         *args[1:],
                                         **kwargs)

class Node(object):
    def __init__(self, identifier, x, y):
        self.identifier = identifier
        self.x = x
        self.y = y

    def __str__(self):
        return "x: {0}\ny: {1}\n".format(self.x, self.y)

class SensorMap(object):
    """Display the sensor in simulation area"""
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
        sensor_node = SensorNode(node, group=Layers.middleground, batch=batch)
        sensor_node.scale=self.node_scale
        sensor_status = NodeStatus(batch=batch)
        sensor_status.scale=self.node_scale
        label = pyglet.text.Label(text=node.identifier,
                                  anchor_x='center',
                                  anchor_y='center',
                                  color=(0,0,0,255),
                                  group=Layers.middleground,
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

    def on_mouse_motion(self, x, y, dx, dy):
        for node in self.nodes_img:
            node.on_mouse_motion(x, y, dx, dy)

class Line(object):
    def __init__(self, A=(0.,0.), B=(0.,0.), thickness=6, color=BLACK, batch=None):
        self.A = A
        self.B = B
        self.thickness = thickness
        self.color = color

    def draw(self):
        x_A, y_A = self.A
        x_B, y_B = self.B

        pyglet.gl.glLineWidth(self.thickness)
        pyglet.graphics.draw(2,pyglet.gl.GL_LINES,
                             ('v2f', (x_A, y_A, x_B, y_B)),
                             ('c3B', 2 * self.color))

    def delete(self):
        self.vertexlist.delete()

    def add_batch(self, batch):
        x_A, y_A = self.A
        x_B, y_B = self.B
        pyglet.gl.glLineWidth(self.thickness)
        self.vertexlist = batch.add(2,pyglet.gl.GL_LINES,None,
                                   ('v2f', (x_A, y_A, x_B, y_B)),
                                   ('c3B', 2 * self.color))
        return self.vertexlist

def init():
    global batch
    batch = pyglet.graphics.Batch()
