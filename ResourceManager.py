import yaml
import os
import cairo

def quoted_presenter(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"')

class ThemeManager():
    def __init__(self):
        config = self.load_config()

        self.terminal = config.get("Terminal")

        self.home_color = config.get("Home Node Color")
        self.base_color = config.get("Node Color")
        self.bg_color = config.get("Background Color")
        self.draw_outer_circle = True

        self.font = config.get("Font")
        self.font_weight = config.get("Font Weight")
        self.font_size = 14

        self.font_slant = cairo.FONT_SLANT_NORMAL

        if self.font_weight.lower().strip() == "bold":
            self.font_weight = cairo.FONT_WEIGHT_BOLD
        else:
            self.font_weight = cairo.FONT_SLANT_ITALIC
    
    def generate_default_config(self):
        home = os.path.expanduser('~')
        config = {
            "Terminal": None,
            "Background Color": "#070e14",
            "Node Color": "#00a9ef",
            "Home Node Color": "#81f171",
            "Font": "Consolas",
            "Font Weight": "Bold"
        }

        with open(f'{home}/.config/netMap/config.yml', "w") as cfg:
            yaml.dump(config, cfg, sort_keys=False)
        
        return config
    
    def load_config(self):
        home = os.path.expanduser('~')
        config = f'{home}/.config/netMap/config.yml'

        if not os.path.exists(config):
            return self.generate_default_config()

        with open(config, 'r') as config_file:
            config = yaml.safe_load(config_file)

        return config

        
    
    def adjust_brightness(self, hex_color, coefficient):
        """
        Adjust the brightness of a hex color by a given coefficient.
        
        Parameters:
        hex_color (str): The hex color string (e.g., '#RRGGBB').
        coefficient (float): The brightness adjustment coefficient (e.g., 1.5 for brighter, 0.5 for darker).
        
        Returns:
        str: The adjusted hex color string.
        """
        
        # Remove the hash symbol if present
        hex_color = hex_color.lstrip('#')
        
        # Convert hex to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        # Adjust brightness
        r = min(255, max(0, int(r * coefficient)))
        g = min(255, max(0, int(g * coefficient)))
        b = min(255, max(0, int(b * coefficient)))
        
        # Convert RGB back to hex
        adjusted_hex = f'#{r:02x}{g:02x}{b:02x}'
        
        return adjusted_hex
    
    def hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))
