import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
import random
import math
import socket
import subprocess
import cairo
import json
import os
import Node
import yaml
import string
from datetime import datetime
import requests
import json
from ResourceManager import ThemeManager
import sys

def quoted_presenter(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"')

yaml.add_representer(str, quoted_presenter)

class NodeVisualizer(Gtk.Window):
    def __init__(self, node_size=5):
        Gtk.Window.__init__(self, title="netMap v1.7")

        self.theme = ThemeManager()

        if len(sys.argv) > 1 and self.theme.terminal is None:
            self.theme.terminal = sys.argv[1]

        self.connect("size_allocate", self.on_size_allocate)
        self.connect("destroy", self.unload)

        # Set window properties
        self.set_default_size(400, 400)

        # Create a drawing area
        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.connect("draw", self.on_draw)
        self.drawing_area.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.drawing_area.connect("button-press-event", self.on_click)
        self.add(self.drawing_area)

        self.drawn = False

        self.blur = []
        size = Gtk.Window.get_size(self)

        self.width = size.width
        self.height = size.height

        print(self.width)
        print(self.height)

        self.node_size = 20  # Change this value to adjust node size

        # Create a dictionary for nodes with positions, colors, and IPs
        self.nodes = []

        # self.nodes.append(
        #     Node.ClickedNode(
        #         name="Test Node", 
        #         position=self.gen_position(),
        #         ip="1337.1337.1337.1337",
        #         last_access_timestamp=None,
        #         node_size=self.node_size,
        #         themeManager=self.theme
        #     )
        # )


        # Make the background transparent
        self.set_app_paintable(True)

        screen = self.get_screen()
        rgba = screen.get_rgba_visual()

        if rgba is not None and screen.is_composited():
            self.set_visual(rgba)

        self.connect("draw", self.draw_window)

        self.drawing_area.add_events(Gdk.EventMask.POINTER_MOTION_MASK)
        self.drawing_area.connect("motion-notify-event", self.on_hover)

        # Pulsing animation
        GLib.timeout_add(30, self.on_tick)
    
    def unload(self, event):
        self.save_nodes()
        Gtk.main_quit()
    
    def load_nodes(self):
        home = os.path.expanduser('~')
        config = f'{home}/.config/netMap/nodes.yml'

        if not os.path.exists(config):
            return

        with open(config, 'r') as config_file:
            nodes_dicted = yaml.safe_load(config_file)
            time_now = datetime.now().timestamp()
            
            for node_ip, node_dict in nodes_dicted.items():
                if node_dict.get("Home"):
                    self.nodes.append(
                        Node.HomeNode(
                            name=node_dict.get("Name"), 
                            position=[node_dict.get("XPos"), node_dict.get("YPos")],
                            ip=node_ip,
                            last_access_timestamp=node_dict.get("LastAccessed"),
                            node_size=self.node_size,
                            themeManager=self.theme
                        )
                    )  
                    continue

                if node_dict.get("LastAccessed") is None:
                    pass

                elif time_now - node_dict.get("LastAccessed") < 604800:
                    self.nodes.append(
                        Node.ActiveNode(
                            name=node_dict.get("Name"), 
                            position=[node_dict.get("XPos"), node_dict.get("YPos")],
                            ip=node_ip,
                            last_access_timestamp=node_dict.get("LastAccessed"),
                            node_size=self.node_size,
                            themeManager=self.theme
                        )
                    )  
                    continue

                self.nodes.append(
                    Node.BaseNode(
                        name=node_dict.get("Name"), 
                        position=[node_dict.get("XPos"), node_dict.get("YPos")],
                        ip=node_ip,
                        last_access_timestamp=node_dict.get("LastAccessed"),
                        node_size=self.node_size,
                        themeManager=self.theme
                    )
                ) 

    def save_nodes(self):
        home = os.path.expanduser('~')
        config_folder = f'{home}/.config/netMap/'
        config = f'{config_folder}/nodes.yml'

        if not os.path.exists(config_folder):
            os.makedirs(config_folder, exist_ok=True)
        
        print("saving")

        nodes_dicted = {}

        for node in self.nodes:
            ip = ""
            x, y = node.position
            
            for char in node.ip:
                if char not in string.ascii_letters + string.digits + ":.":
                    continue
                
                ip += char
            
            print(node.last_access_timestamp)

            nodes_dicted[ip] = {
                "Name": node.name,
                "XPos": x,
                "YPos": y,
                "LastAccessed": node.last_access_timestamp,
                "Home": isinstance(node, Node.HomeNode)
            }

        with open(config, 'w') as config_file:
            yaml.dump(nodes_dicted, config_file, sort_keys=False)
    
    def is_up(self, host):
        param = '-c'
        response = os.system(f"ping {param} 1 {host}")

        return response == 0
    
    def on_tick(self):
        clicked_node = None

        for node in self.nodes:
            if isinstance(node, Node.ClickedNode):
                if clicked_node != None:
                    first_node_timestamp = clicked_node.last_access_timestamp
                    if first_node_timestamp is None:
                        clicked_node.unclick()
                        clicked_node = node
                        continue

                    second_node_timestamp = node.last_access_timestamp

                    if first_node_timestamp > second_node_timestamp:
                        continue

                    clicked_node.unclick()
                    clicked_node = node
                else:
                    clicked_node = node

            node.tick()
        
        self.queue_draw()

        return True
    
    def get_cursor_position(self):
        display = Gdk.Display.get_default()
        screen, x, y, _ = display.get_pointer()
        return x, y

    def on_hover(self, widget, event):
        x, y = event.x, event.y
        self.hovered_node = None  # Reset the hovered node

        for node in self.nodes:
            node.hovered = False
            node_x, node_y = node.position
            distance = math.sqrt((node_x - x) ** 2 + (node_y - y) ** 2)
            if distance <= self.node_size:
                node.hovered = True
                break

        self.queue_draw()  # Redraw the widget to reflect hover state

    def draw_window(self, widget, cr):
        allocation = self.get_allocation()

        self.width = allocation.width
        self.height = allocation.height

        if not self.drawn:
            self.load_nodes()
            self.parse_ssh()
            self.add_home_node()
            self.drawn = True

        cr.set_source_rgba(*self.theme.hex_to_rgb(self.theme.bg_color), 0.3)  # Transparent background
        cr.paint()
    
    def parse_ssh(self):
        home = os.path.expanduser('~')
        print("command run")
        if os.path.isfile(f"{home}/.ssh/known_hosts"):
            print("path exists")
            with open(f"{home}/.ssh/known_hosts") as hosts:
                for host in hosts:
                    raw_ip = host.split(" ")[0]
                    ip = ""
                    skip = False

                    for char in raw_ip:
                        if char not in string.ascii_letters + string.digits + ":.":
                            continue
                        
                        ip += char

                    for node in self.nodes:
                        if node.ip == ip:
                            skip = True
                    
                    if skip:
                        continue

                    self.nodes.append(
                        Node.BaseNode(
                            name="Unknown", 
                            position=self.gen_position(),
                            ip=ip,
                            last_access_timestamp=None,
                            node_size=self.node_size,
                            themeManager=self.theme
                        )
                    )
    
    def get_ip(sellf):
        endpoint = 'https://ipinfo.io/json'
        response = requests.get(endpoint, verify = True)

        if response.status_code != 200:
            return 'Status:', response.status_code, 'Problem with the request. Exiting.'
            exit()

        data = response.json()

        return data['ip']

    def add_home_node(self):
        for node in self.nodes:
            if isinstance(node, Node.HomeNode):
                return
        self.nodes.append(
            Node.HomeNode(
                name=socket.gethostname(), 
                position=self.gen_position(home=True),
                ip=self.get_ip(),
                last_access_timestamp=None,
                node_size=self.node_size,
                themeManager=self.theme
            )
        )
    
    def redraw(self):
        for node in self.nodes:
            if isinstance(node, Node.HomeNode):
                node.position = self.gen_position(home=True)
            else:
                node.position = self.gen_position()

    def on_draw(self, widget, cr):
        allocation = self.drawing_area.get_allocation()
        width = allocation.width
        height = allocation.height

        # Dictionary to store positions of nodes with same first two digits of IP
        ip_prefix_positions = {}

        for node in self.nodes:
            try:
                ip = socket.gethostbyname(node.ip)
            except Exception:
                ip = node.ip

            # Get the first two digits of the IP address
            ip_prefix = ip[0] + ip[1]

            x, y = node.position

            node.render(self.drawing_area, cr)

            cr.set_line_width(2)
            cr.set_source_rgba(*self.theme.hex_to_rgb("#ffffff"), 0.3)

            if ip_prefix in ip_prefix_positions:
                # Connect nodes with the same first two digits of IP address
                for pos_x, pos_y in ip_prefix_positions[ip_prefix]:
                    cr.move_to(x, y)
                    cr.line_to(pos_x, pos_y)
                    cr.stroke()
                ip_prefix_positions[ip_prefix].append((x, y))
            else:
                ip_prefix_positions[ip_prefix] = [(x, y)]

            # if node.get("active"):
            #     # Additional circles to simulate smaller and more chaotic blur effect
            #     if self.blur != []:
            #         for i in range(0, 9):
            #             blur_alpha = 0.05 * (1 - (i / 10))
            #             offset_x, offset_y = self.blur[i]

            #             cr.set_source_rgba(*self.theme.hex_to_rgb(color), blur_alpha)
            #             cr.arc(x + offset_x, y + offset_y, self.node_size * (1.2 + i * 0.05), 0, 2 * math.pi)
            #             cr.fill()
            #     else:
            #         for i in range(1, 10):
            #             blur_alpha = 0.05 * (1 - (i / 10))
            #             offset_x = random.uniform(-self.node_size * 0.1, self.node_size * 0.1)
            #             offset_y = random.uniform(-self.node_size * 0.1, self.node_size * 0.1)

            #             cr.set_source_rgba(*self.theme.hex_to_rgb(color), blur_alpha)
            #             cr.arc(x + offset_x, y + offset_y, self.node_size * (1.2 + i * 0.05), 0, 2 * math.pi)
            #             cr.fill()

            #             self.blur.append((offset_x, offset_y))

    def on_click(self, widget, event):
        x, y = event.x, event.y
        for node in self.nodes:
            node_x, node_y = node.position
            distance = math.sqrt((node_x - x) ** 2 + (node_y - y) ** 2)
            if distance <= self.node_size:
                node.on_click()
    
    def set_home(self, index):
        self.nodes[index]["home"] = True

    def set_active(self, index):
        self.nodes[index]["active"] = True

    def on_size_allocate(self, widget, allocation):
        if allocation.width == self.width and allocation.height == self.height:
            return

        self.height = allocation.height
        self.width = allocation.width

        self.redraw()

    def is_overlapping(self, x, y, treshhold=2):
        for node in self.nodes:
            pos_x, pos_y = node.position
            distance = math.sqrt((pos_x - x) ** 2 + (pos_y - y) ** 2)
            if distance < self.node_size * 2:
                return True

        return False

    def gen_position(self, home=False):
        random_position = [random.uniform(self.width * 0.1, self.width * 0.9), random.uniform(self.height * 0.2, self.height * 0.8)]

        if home:
            random_position = [random.uniform(self.width * 0.1, self.width * 0.3), random.uniform(self.height * 0.4, self.height * 0.6)]
        
        if self.nodes == {}:
            return random_position

        if home:
            while self.is_overlapping(random_position[0], random_position[1]):
                random_position = [random.uniform(self.width * 0.1, self.width * 0.3), random.uniform(self.height * 0.4, self.height * 0.6)]
                
        else:
            while self.is_overlapping(random_position[0], random_position[1], treshhold=6):
                random_position = [random.uniform(self.width * 0.2, self.width * 0.8), random.uniform(self.height * 0.2, self.height * 0.8)]
            
        return random_position

node_visualizer = NodeVisualizer()

if __name__ == "__main__":
    node_visualizer.show_all()

    try:
        Gtk.main()
    except KeyboardInterrupt:
        node_visualizer.unload(None)
