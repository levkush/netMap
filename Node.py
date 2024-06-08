import math, subprocess, random
from datetime import datetime

class Node():
    def __init__(self, name, position, ip, node_size, themeManager, timestamp):
        self.name = name
        self.position = position
        self.ip = ip
        self.last_access_timestamp = timestamp
        self.theme = themeManager
        self.node_size = node_size

        # Hover
        self.hovered = False
    
    def on_click(self):
        host = self.ip.replace("[", "").replace("]", "").split(":")

        ip = host[0]
        port = 22

        if len(host) >= 2:
            port = host[1]

        print(f"Connecting to IP: {ip}")

        self.last_access_timestamp = datetime.now().timestamp()

        active_node = ActiveNode(self.name, self.position, self.ip, self.node_size, self.theme, self.last_access_timestamp)
        
        active_node.expanding_radius = self.expanding_radius
        active_node.expanding_state = self.expanding_state
        active_node.tick_count = self.tick_count
        active_node.wait_tick_count = self.wait_tick_count
        active_node.pulse_alpha = self.pulse_alpha

        self.__dict__.update(active_node.__dict__)

        self.__class__ = ActiveNode

        subprocess.run(["bash", "-c", f"i3-sensible-terminal /bin/bash -c 'ssh {ip} -p {port}; bash' &>/dev/null &"])

    def draw_popup(self, x, y, painter):
        host = self.ip.replace("[", "").replace("]", "").split(":")

        ip = host[0]

        line_1 = self.name
        line_2 = ip

        # Set rectangle and text properties
        rect_x = x + self.node_size * 1.5
        rect_y = y - self.node_size / 1.3

        # Set the font and font size
        painter.select_font_face(self.theme.font, self.theme.font_slant, self.theme.font_weight)
        painter.set_font_size(self.theme.font_size)

        # Calculate text extents to determine the size of the rectangle
        text1_extents = painter.text_extents(line_1)
        text2_extents = painter.text_extents(line_2)

        # Determine the maximum text width and total height
        max_text_width = max(text1_extents.width, text2_extents.width)
        line_spacing = self.theme.font_size * 0.4  # Reduced line spacing
        text_height = text1_extents.height + text2_extents.height + line_spacing

        # Add some padding around the text
        padding = self.theme.font_size * 0.5

        # Calculate rectangle width and height based on text dimensions and padding
        rect_width = max_text_width + 2 * padding
        rect_height = text_height + 2 * padding

        # Draw the rectangle
        painter.set_source_rgba(*self.theme.hex_to_rgb("#000000"), 0.3)
        painter.rectangle(rect_x, rect_y, rect_width, rect_height)
        painter.fill()

        # Draw the text
        painter.set_source_rgba(1, 1, 1, 1)  # White color for text

        # Calculate vertical positions for text to ensure equal padding at the top and bottom
        text1_y = rect_y + padding + text1_extents.height - 1
        text2_y = rect_y + padding + text1_extents.height + line_spacing + text2_extents.height - 1

        # Draw first line of text
        painter.move_to(rect_x + padding, text1_y)
        painter.show_text(line_1)

        # Draw second line of text
        painter.move_to(rect_x + padding, text2_y)
        painter.show_text(line_2)

class BaseNode(Node):
    def __init__(self, name, position, ip, node_size, themeManager, last_access_timestamp):
        Node.__init__(self, name, position, ip, node_size, themeManager, last_access_timestamp)
        # Animation
        self.raw_expanding_radius = self.node_size * 0.8
        self.expanding_radius = self.raw_expanding_radius
        self.expanding_state = "expand"
        self.max_radius = self.node_size * 4
        self.expanding_duration = 8
        self.waiting_duration = 60
        self.tick_count = 0
        self.wait_tick_count = 0
        self.raw_pulse_alpha = 0.35
        self.pulse_alpha = self.raw_pulse_alpha
    
    def tick(self):
        if self.expanding_state == "expand":
            # Increment the expanding radius by a small amount

            self.tick_count += 0.5
            self.expanding_radius += self.tick_count / 20
            
            # Ensure that the expanding circle doesn't grow beyond a certain limit
            if self.pulse_alpha == 0:
                self.expanding_radius = 0
                self.tick_count = 0
                self.expanding_state = "wait"  # Switch to the waiting state
            
            # Calculate the opacity of the expanding circle based on the current duration
            self.pulse_alpha = max(0, self.raw_pulse_alpha - (self.tick_count / self.max_radius))
            
        elif self.expanding_state == "wait":
            # Increment the tick count
            self.wait_tick_count += 1
            
            # Check if the waiting duration has elapsed
            if self.wait_tick_count >= self.waiting_duration:
                self.wait_tick_count = 0  # Reset the tick count
                self.expanding_radius = self.raw_expanding_radius  # Reset the radius
                self.expanding_state = "expand"  # Switch back to the expanding state
    
    def render(self, drawing_area, painter):
        allocation = drawing_area.get_allocation()

        width = allocation.width
        height = allocation.height

        x, y = self.position
        color = self.theme.base_color

        # Set alpha value for transparency (0 = fully transparent, 1 = fully opaque)
        alpha = 0.5  # You can adjust this value as needed

        if self.hovered:
            self.draw_popup(x, y, painter)
            
        # Darken the color
        dark_color = self.theme.adjust_brightness(color, 0.2)

        # Draw main node with transparency
        painter.set_source_rgba(*self.theme.hex_to_rgb(color), alpha)
        painter.arc(x, y, self.node_size, 0, 2 * math.pi)
        painter.fill()

        # Draw inner circle with darker color and transparency
        painter.set_source_rgba(*self.theme.hex_to_rgb(dark_color), alpha)
        painter.arc(x, y, self.node_size * 0.6, 0, 2 * math.pi)
        painter.fill()

        # Small inner outline
        lighter_color = self.theme.adjust_brightness(color, 0.8)
        painter.set_source_rgba(*self.theme.hex_to_rgb(lighter_color), 1)
        painter.arc(x, y, self.node_size * 0.5, 0, 2 * math.pi)
        painter.set_line_width(2)  # Optional: Set the width of the outline
        painter.stroke()

        # Draw the expanding circle
        painter.set_source_rgba(*self.theme.hex_to_rgb(color), self.pulse_alpha)
        painter.arc(x, y, self.expanding_radius, 0, 2 * math.pi)
        painter.set_line_width(5)  # Optional: Set the width of the outline
        painter.stroke()

class ActiveNode(Node):
    def __init__(self, name, position, ip, node_size, themeManager, last_access_timestamp):
        Node.__init__(self, name, position, ip, node_size, themeManager, last_access_timestamp)

        self.blur = []

        # Animation
        self.raw_expanding_radius = self.node_size * 0.8
        self.expanding_radius = self.raw_expanding_radius
        self.expanding_state = "expand"
        self.max_radius = self.node_size * 4
        self.expanding_duration = 8
        self.waiting_duration = 60
        self.tick_count = 0
        self.wait_tick_count = 0
        self.raw_pulse_alpha = 0.35
        self.pulse_alpha = self.raw_pulse_alpha
    
    def tick(self):
        if self.expanding_state == "expand":
            # Increment the expanding radius by a small amount

            self.tick_count += 0.5
            self.expanding_radius += self.tick_count / 20
            
            # Ensure that the expanding circle doesn't grow beyond a certain limit
            if self.pulse_alpha == 0:
                self.expanding_radius = 0
                self.tick_count = 0
                self.expanding_state = "wait"  # Switch to the waiting state
            
            # Calculate the opacity of the expanding circle based on the current duration
            self.pulse_alpha = max(0, self.raw_pulse_alpha - (self.tick_count / self.max_radius))
            
        elif self.expanding_state == "wait":
            # Increment the tick count
            self.wait_tick_count += 1
            
            # Check if the waiting duration has elapsed
            if self.wait_tick_count >= self.waiting_duration:
                self.wait_tick_count = 0  # Reset the tick count
                self.expanding_radius = self.raw_expanding_radius  # Reset the radius
                self.expanding_state = "expand"  # Switch back to the expanding state
    
    def render(self, drawing_area, painter):
        allocation = drawing_area.get_allocation()

        width = allocation.width
        height = allocation.height

        x, y = self.position
        color = self.theme.base_color

        # Set alpha value for transparency (0 = fully transparent, 1 = fully opaque)
        alpha = 0.9  # You can adjust this value as needed

        if self.hovered:
            self.draw_popup(x, y, painter)
            
        # Darken the color
        dark_color = self.theme.adjust_brightness(color, 0.2)

        # Draw main node with transparency
        painter.set_source_rgba(*self.theme.hex_to_rgb(color), alpha)
        painter.arc(x, y, self.node_size, 0, 2 * math.pi)
        painter.fill()

        # Draw inner circle with darker color and transparency
        painter.set_source_rgba(*self.theme.hex_to_rgb(dark_color), alpha)
        painter.arc(x, y, self.node_size * 0.6, 0, 2 * math.pi)
        painter.fill()

        # Small inner outline
        lighter_color = self.theme.adjust_brightness(color, 0.8)
        painter.set_source_rgba(*self.theme.hex_to_rgb(lighter_color), 1)
        painter.arc(x, y, self.node_size * 0.5, 0, 2 * math.pi)
        painter.set_line_width(2)  # Optional: Set the width of the outline
        painter.stroke()

        # Draw the expanding circle
        painter.set_source_rgba(*self.theme.hex_to_rgb(color), self.pulse_alpha)
        painter.arc(x, y, self.expanding_radius, 0, 2 * math.pi)
        painter.set_line_width(5)  # Optional: Set the width of the outline
        painter.stroke()

        if self.blur != []:
            for i in range(0, 9):
                blur_alpha = 0.05 * (1 - (i / 10))
                offset_x, offset_y = self.blur[i]

                painter.set_source_rgba(*self.theme.hex_to_rgb(color), blur_alpha)
                painter.arc(x + offset_x, y + offset_y, self.node_size * (1.2 + i * 0.05), 0, 2 * math.pi)
                painter.fill()
        else:
            for i in range(1, 10):
                blur_alpha = 0.05 * (1 - (i / 10))
                offset_x = random.uniform(-self.node_size * 0.1, self.node_size * 0.1)
                offset_y = random.uniform(-self.node_size * 0.1, self.node_size * 0.1)

                painter.set_source_rgba(*self.theme.hex_to_rgb(color), blur_alpha)
                painter.arc(x + offset_x, y + offset_y, self.node_size * (1.2 + i * 0.05), 0, 2 * math.pi)
                painter.fill()

                self.blur.append((offset_x, offset_y))

class HomeNode(Node):
    def __init__(self, name, position, ip, node_size, themeManager, last_access_timestamp):
        Node.__init__(self, name, position, ip, node_size, themeManager, last_access_timestamp)

        self.blur = []

        # Animation
        self.raw_expanding_radius = self.node_size * 0.8
        self.expanding_radius = self.raw_expanding_radius
        self.expanding_state = "expand"
        self.max_radius = self.node_size * 4
        self.expanding_duration = 8
        self.waiting_duration = 60
        self.tick_count = 0
        self.wait_tick_count = 0
        self.raw_pulse_alpha = 0.35
        self.pulse_alpha = self.raw_pulse_alpha

        # Spinning arc animation
        self.angle = 0
        self.angle_increment = 0.05  # Adjust this value to control the speed of the spin

        # Inner spinning arc animation
        self.inner_angle = math.pi * 1.5 # Start at a different angle to desynchronize
        self.inner_angle_increment = 0.05  # Slightly different speed


    
    def tick(self):
        if self.expanding_state == "expand":
            # Increment the expanding radius by a small amount
            self.tick_count += 0.5
            self.expanding_radius += self.tick_count / 20
            
            # Ensure that the expanding circle doesn't grow beyond a certain limit
            if self.pulse_alpha == 0:
                self.expanding_radius = 0
                self.tick_count = 0
                self.expanding_state = "wait"  # Switch to the waiting state
            
            # Calculate the opacity of the expanding circle based on the current duration
            self.pulse_alpha = max(0, self.raw_pulse_alpha - (self.tick_count / self.max_radius))
            
        elif self.expanding_state == "wait":
            # Increment the tick count
            self.wait_tick_count += 1
            
            # Check if the waiting duration has elapsed
            if self.wait_tick_count >= self.waiting_duration:
                self.wait_tick_count = 0  # Reset the tick count
                self.expanding_radius = self.raw_expanding_radius  # Reset the radius
                self.expanding_state = "expand"  # Switch back to the expanding state
        
        # Update the angle for the spinning arcs
        self.angle += self.angle_increment
        self.angle %= (2 * math.pi)  # Ensure the angle stays within 0 to 2π

        self.inner_angle += self.inner_angle_increment
        self.inner_angle %= (2 * math.pi)  # Ensure the angle stays within 0 to 2π


    def on_click(self):
        return
    
    def render(self, drawing_area, painter):
        allocation = drawing_area.get_allocation()

        width = allocation.width
        height = allocation.height

        x, y = self.position
        color = self.theme.home_color

        # Set alpha value for transparency (0 = fully transparent, 1 = fully opaque)
        alpha = 0.9  # You can adjust this value as needed

        if self.hovered:
            self.draw_popup(x, y, painter)
            
        # Darken the color
        dark_color = self.theme.adjust_brightness(color, 0.2)

        # Draw main node with transparency
        painter.set_source_rgba(*self.theme.hex_to_rgb(color), alpha)
        painter.arc(x, y, self.node_size, 0, 2 * math.pi)
        painter.fill()

        # Draw inner circle with darker color and transparency
        painter.set_source_rgba(*self.theme.hex_to_rgb(dark_color), alpha)
        painter.arc(x, y, self.node_size * 0.7, 0, 2 * math.pi)
        painter.fill()

        # Small inner outline
        lighter_color = self.theme.adjust_brightness(color, 0.8)
        painter.set_source_rgba(*self.theme.hex_to_rgb(lighter_color), 1)
        painter.arc(x, y, self.node_size * 0.6, 0, 2 * math.pi)
        painter.set_line_width(2)  # Optional: Set the width of the outline
        painter.stroke()

        # Draw the expanding circle
        painter.set_source_rgba(*self.theme.hex_to_rgb(color), self.pulse_alpha)
        painter.arc(x, y, self.expanding_radius, 0, 2 * math.pi)
        painter.set_line_width(5)  # Optional: Set the width of the outline
        painter.stroke()

        # Draw the first spinning arc (two-thirds circle)
        painter.set_source_rgba(*self.theme.hex_to_rgb(color), 1)
        start_angle = self.angle
        end_angle = self.angle + (4.5 * math.pi / 3)  # 240 degrees
        painter.arc(x, y, self.node_size * 1.6, start_angle, end_angle)
        painter.set_line_width(2)  # Optional: Set the width of the spinning arc
        painter.stroke()

        # Draw the second spinning arc (desynchronized two-thirds circle)
        painter.set_source_rgba(*self.theme.hex_to_rgb(color), 1)
        inner_start_angle = self.inner_angle
        inner_end_angle = self.inner_angle + (4 * math.pi / 3.2)  # 240 degrees
        painter.arc(x, y, self.node_size * 1.1, inner_start_angle, inner_end_angle)
        painter.set_line_width(2)  # Optional: Set the width of the spinning arc
        painter.stroke()

        if self.blur != []:
            for i in range(0, 9):
                blur_alpha = 0.05 * (1 - (i / 10))
                offset_x, offset_y = self.blur[i]

                painter.set_source_rgba(*self.theme.hex_to_rgb(color), blur_alpha)
                painter.arc(x + offset_x, y + offset_y, self.node_size * (1.2 + i * 0.05), 0, 2 * math.pi)
                painter.fill()
        else:
            for i in range(1, 10):
                blur_alpha = 0.05 * (1 - (i / 10))
                offset_x = random.uniform(-self.node_size * 0.1, self.node_size * 0.1)
                offset_y = random.uniform(-self.node_size * 0.1, self.node_size * 0.1)

                painter.set_source_rgba(*self.theme.hex_to_rgb(color), blur_alpha)
                painter.arc(x + offset_x, y + offset_y, self.node_size * (1.2 + i * 0.05), 0, 2 * math.pi)
                painter.fill()

                self.blur.append((offset_x, offset_y))