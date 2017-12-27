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


# Folders
GAME_FOLDER = os.path.dirname(__file__)
ASSET_FOLDER = os.path.join(GAME_FOLDER, "assets")

FONT_FOLDER = os.path.join(ASSET_FOLDER, "font")
FONT_NAME = "Ubuntu-B.ttf"

IMG_FOLDER = os.path.join(ASSET_FOLDER, "img")
ITEM_FOLDER = os.path.join(IMG_FOLDER, "Items")
LIVE_FOLDER = os.path.join(IMG_FOLDER, "LiveEntities")
OBJECT_FOLDER = os.path.join(IMG_FOLDER, "Objects")
PLAYER_FOLDER = os.path.join(IMG_FOLDER, "Player")
ICON_FOLDER = os.path.join(IMG_FOLDER, "Icons")
UI_FOLDER = os.path.join(IMG_FOLDER, "UIPack")

# Graphical Settings
TILESIZE_SCREEN = (32, 32)

# game settings
PLAYABLE_WIDTH = 512  # 16 * 64 or 32 * 32 or 64 * 16
PLAYABLE_HEIGHT = 512  # 16 * 48 or 32 * 24 or 64 * 12
FPS = 60
BGCOLOR = BLACK

GRIDWIDTH = PLAYABLE_WIDTH / TILESIZE_SCREEN[0]
GRIDHEIGHT = PLAYABLE_HEIGHT / TILESIZE_SCREEN[1]

GAME_HEIGHT = 800
GAME_WIDTH = 600

MINIMAP_WIDTH = 60
MINIMAP_HEIGHT = 40
