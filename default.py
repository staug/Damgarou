import os

# List of fix data and variable
# GAME
GAME_TITLE = "Damgarou"
GAME_VER = "0.04"

# define some colors (R, G, B)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARKGREY = (40, 40, 40)
LIGHTGREY = (100, 100, 100)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)

# Themes for Buttons, labels...
THEME_LIGHT_GRAY = {
    "rounded_angle" : 0.1,  # 0 = no angle, 1 = full angle
    "with_decoration" : True,  # This adds small triangles
    "borders": [(2, (233, 233, 233)), (2, (203, 203, 203))],  # list of margin + colors (external to int)
    "bg_color": (229, 229, 229),
    "font_color": (155, 157, 173)
}
THEME_DARK_GRAY = {
    "rounded_angle" : 0.1,  # 0 = no angle, 1 = full angle
    "with_decoration" : True,  # This adds small triangles
    "borders": [(2, (97, 99,116)), (2, (155,157,173))],  # list of margin + colors (external to int)
    "bg_color": (131,135,150),
    "font_color": (233, 233, 233)
}
THEME_LIGHT_BROWN = {
    "rounded_angle" : 0.1,  # 0 = no angle, 1 = full angle
    "with_decoration" : True,  # This adds small triangles
    "borders": [(2, (217,205,175)), (2, (177,160,119))],  # list of margin + colors (external to int)
    "bg_color": (211,191,143),
    "font_color": (155, 157, 173)
}
THEME_DARK_BROWN = {
    "rounded_angle" : 0.1,  # 0 = no angle, 1 = full angle
    "with_decoration" : True,  # This adds small triangles
    "borders": [(2, (136,102,68)), (2, (183, 145, 106))],  # list of margin + colors (external to int)
    "bg_color": (151, 113, 74),
    "font_color": (233, 233, 233)
}

# Folders
GAME_FOLDER = os.path.dirname(__file__)
ASSET_FOLDER = os.path.join(GAME_FOLDER, "assets")

FONT_FOLDER = os.path.join(ASSET_FOLDER, "font")
FONT_NAME = "ProFontWindows.ttf"

IMG_FOLDER = os.path.join(ASSET_FOLDER, "img")
ITEM_FOLDER = os.path.join(IMG_FOLDER, "Items")
LIVE_FOLDER = os.path.join(IMG_FOLDER, "LiveEntities")
OBJECT_FOLDER = os.path.join(IMG_FOLDER, "Objects")
PLAYER_FOLDER = os.path.join(IMG_FOLDER, "Player")
ICON_FOLDER = os.path.join(IMG_FOLDER, "Icons")

# Graphical Settings
TILESIZE_SCREEN = (32, 32)

# game settings
PLAYABLE_WIDTH = 512   # 16 * 64 or 32 * 32 or 64 * 16
PLAYABLE_HEIGHT = 512  # 16 * 48 or 32 * 24 or 64 * 12
FPS = 60
BGCOLOR = BLACK

GRIDWIDTH = PLAYABLE_WIDTH / TILESIZE_SCREEN[0]
GRIDHEIGHT = PLAYABLE_HEIGHT / TILESIZE_SCREEN[1]

GAME_HEIGHT = 800
GAME_WIDTH = 600

MINIMAP_WIDTH = 60
MINIMAP_HEIGHT = 40