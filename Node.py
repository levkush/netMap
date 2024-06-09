import math, subprocess, random
from datetime import datetime
import threading

class Node():
    def __init__(self, name, position, ip, node_size, themeManager, timestamp):
        self.name = name
        self.position = position
        self.ip = ip
        self.last_access_timestamp = timestamp
        self.theme = themeManager
        self.node_size = node_size

        # Pulse animation
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

        # Hover
        self.hovered = False
    
    def animation_tick(self):
        pass
    
    def pulse_tick(self):
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
    
    def tick(self):
        self.pulse_tick()
        self.animation_tick()

    def unclick(self):
        active_node = ActiveNode(self.name, self.position, self.ip, self.node_size, self.theme, self.last_access_timestamp)
        
        active_node.expanding_radius = self.expanding_radius
        active_node.expanding_state = self.expanding_state
        active_node.tick_count = self.tick_count
        active_node.wait_tick_count = self.wait_tick_count
        active_node.pulse_alpha = self.pulse_alpha

        self.__dict__.update(active_node.__dict__)

        self.__class__ = ActiveNode
    
    def run_cmd(self, cmd, on_exit):
        """
        Runs the given args in a subprocess.Popen, and then calls the function
        on_exit when the subprocess completes.
        on_exit is a callable object, and popen_args is a list/tuple of args that 
        would give to subprocess.Popen.
        """
        def run_in_thread(on_exit, cmd):
            proc = subprocess.Popen(cmd)
            proc.wait()
            on_exit()
            return

        thread = threading.Thread(target=run_in_thread, args=(on_exit, cmd))
        thread.start()
        # returns immediately after the thread starts
        return thread
    
    def on_click(self):
        host = self.ip.replace("[", "").replace("]", "").split(":")

        ip = host[0]
        port = 22

        if len(host) >= 2:
            port = host[1]

        print(f"Connecting to IP: {ip}")

        self.last_access_timestamp = datetime.now().timestamp()

        clicked_node = ClickedNode(self.name, self.position, self.ip, self.node_size, self.theme, self.last_access_timestamp)
        
        clicked_node.expanding_radius = self.expanding_radius
        clicked_node.expanding_state = self.expanding_state
        clicked_node.tick_count = self.tick_count
        clicked_node.wait_tick_count = self.wait_tick_count
        clicked_node.pulse_alpha = self.pulse_alpha

        self.__dict__.update(clicked_node.__dict__)

        self.__class__ = ClickedNode

        def _(): pass

        self.run_cmd(["bash", "-c", f"pkill ssh"], _)

        self.run_cmd(["bash", "-c", f"i3-sensible-terminal /bin/bash -c 'ssh {ip} -p {port}' &>/dev/null"], self.unclick)

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

        # Spinning arc animation
        self.angle = 0
        self.angle_increment = 0.025  # Adjust this value to control the speed of the spin

        # Inner spinning arc animation
        self.inner_angle = math.pi * 1.5 # Start at a different angle to desynchronize
        self.inner_angle_increment = 0.025  # Slightly different speed
    
    def tick(self):
        self.animation_tick()
    
    def animation_tick(self):
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

class ClickedNode(Node):
    def __init__(self, name, position, ip, node_size, themeManager, last_access_timestamp):
        Node.__init__(self, name, position, ip, node_size, themeManager, last_access_timestamp)

        self.blur = []

        self.animations = []

        for _ in range(random.randint(6, 8)):
            self.animations.append(
                {
                    "type": random.choice(["bar", "circle", "circle", "dots"]),
                    "speed": random.uniform(0.02, 0.03),
                    "rotation": random.uniform(0, 1),
                    "reversed": random.choice([True, False]),
                    "spacing": random.uniform(1.7, 2),
                    "length": random.uniform(math.pi, math.pi * 1.2),
                    "angle": random.randint(-200, 200)
                }
            )

    
    def animation_tick(self):
        for animation in self.animations:
            if animation.get("reversed"):
                animation["angle"] -= animation.get("speed")
            else:
                animation["angle"] += animation.get("speed")

            animation["angle"] %= (2 * math.pi)  # Ensure the angle stays within 0 to 2π


    def on_click(self):
        return
    
    def render(self, drawing_area, painter):
        allocation = drawing_area.get_allocation()

        width = allocation.width
        height = allocation.height

        x, y = self.position
        color = "#FFFFFF"

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

        painter.set_source_rgba(*self.theme.hex_to_rgb(color), 0.2)

        for animation in self.animations:
            if animation.get("type") == "dots":
                # Draw three dots following the inner animated quarter-circle
                num_dots = 3
                dot_radius = self.node_size * 0.1  # Adjust the dot size as needed
                arc_radius = self.node_size * animation.get("spacing")
                dot_spacing_angle = (0.5 * math.pi) / (num_dots + 1)

                for i in range(1, num_dots + 1):
                    angle = animation.get("angle") + i * dot_spacing_angle - 1.5
                    dot_x = x + arc_radius * math.cos(angle)
                    dot_y = y + arc_radius * math.sin(angle)
                    painter.arc(dot_x, dot_y, dot_radius, 0, 2 * math.pi)
                    painter.fill()

            elif animation.get("type") == "bar":
                # Draw the outer bar circling around the node
                bar_height = 3 # Height of the bar
                bar_width = self.node_size * 1 # Width of the bar (make it narrow)
                bar_radius = self.node_size * 2  # Radius at which the bar will rotate

                # Calculate the center position of the bar
                bar_center_x = x + bar_radius * math.cos(animation.get("angle"))
                bar_center_y = y + bar_radius * math.sin(animation.get("angle"))

                # Calculate the four corners of the rectangle (bar)
                bar_half_height = bar_height / 2

                bar_top_x = bar_center_x - bar_half_height * math.sin(animation.get("angle"))
                bar_top_y = bar_center_y + bar_half_height * math.cos(animation.get("angle"))
                bar_bottom_x = bar_center_x + bar_half_height * math.sin(animation.get("angle"))
                bar_bottom_y = bar_center_y - bar_half_height * math.cos(animation.get("angle"))

                painter.set_line_width(bar_width)

                # Left side of the bar
                painter.move_to(bar_top_x, bar_top_y)
                painter.line_to(bar_bottom_x, bar_bottom_y)
                painter.stroke()

            elif animation.get("type") == "circle":
                # Draw the first spinning arc (two-thirds circle)
                start_angle = animation.get("angle")
                end_angle = animation.get("angle") + (math.pi / 3)  # 240 degrees
                painter.arc(x, y, self.node_size * animation.get("spacing"), start_angle, end_angle)
                painter.set_line_width(2)  # Optional: Set the width of the spinning arc
                painter.stroke()
                

        # # Draw the second spinning arc (desynchronized two-thirds circle) over the dots
        # inner_start_angle = self.inner_angle
        # inner_end_angle = self.inner_angle + (1.5 * math.pi / 3.2)  # 240 degrees
        # painter.arc(x, y, arc_radius, inner_start_angle, inner_end_angle)
        # painter.set_line_width(2)  # Optional: Set the width of the spinning arc
        # painter.stroke()
        
        if self.blur != []:
            for i in range(0, 9):
                blur_alpha = 0.05 * (1 - (i / 10))
                offset_x, offset_y = self.blur[i]

                painter.set_source_rgba(*self.theme.hex_to_rgb(color), blur_alpha)
                painter.arc(x + offset_x, y + offset_y, self.node_size * (1.1 + i * 0.05), 0, 2 * math.pi)
                painter.fill()
        else:
            for i in range(1, 10):
                blur_alpha = 0.05 * (1 - (i / 10))
                offset_x = random.uniform(-self.node_size * 0.1, self.node_size * 0.1)
                offset_y = random.uniform(-self.node_size * 0.1, self.node_size * 0.1)

                painter.set_source_rgba(*self.theme.hex_to_rgb(color), blur_alpha)
                painter.arc(x + offset_x, y + offset_y, self.node_size * (1.1 + i * 0.05), 0, 2 * math.pi)
                painter.fill()

                self.blur.append((offset_x, offset_y))
