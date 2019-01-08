from pygame.freetype import Font as PygameFont
from pygame.freetype import init as freetype_init
from pygame import MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, KEYDOWN, KEYUP, QUIT, VIDEORESIZE, \
                    KMOD_LSHIFT, KMOD_RSHIFT, KMOD_CAPS, KMOD_CTRL, KMOD_ALT

freetype_init()

POLARON_ROOT = __file__.replace("\\", "/")[:-9]

DRAG = 1000
PROPERTY_CHANGE = 1001

CONFIGURATION = {
    "DRAG_MIN_DISTANCE": 50,
    "STYLE_PROPERTIES": [
        "background_color",
        "color",
        "border",
        "border_color",
        "selection_color",
        ],
    "STYLE_DEFAULTS": {
        "background_color": (0, 0, 0, 0),
        "color": (0, 0, 0),
        "border": 0,
        "border_color": (0, 0, 0),
        "selection_color": (150, 150, 255)
        },
    "DEFAULT_FONTS": {
        "regular": PygameFont(POLARON_ROOT + "resources/fonts/Roboto-Regular.ttf", size=12),
        "bold": PygameFont(POLARON_ROOT + "resources/fonts/Roboto-Bold.ttf", size=12),
        "italic": PygameFont(POLARON_ROOT + "resources/fonts/Roboto-Italic.ttf", size=12),
        "bold-italic": PygameFont(POLARON_ROOT + "resources/fonts/Roboto-BoldItalic.ttf", size=12),
        "heading": PygameFont(POLARON_ROOT + "resources/fonts/Autobus-Bold.ttf", size=14)
        },
    "EVENT_TYPES": {
        "mouse_down": MOUSEBUTTONDOWN,
        "mouse_up": MOUSEBUTTONUP,
        "mouse_motion": MOUSEMOTION,
        "key_down": KEYDOWN,
        "key_up": KEYUP,
        "quit": QUIT,
        "video_resize": VIDEORESIZE,
        "drag": DRAG,
        "property_change": PROPERTY_CHANGE
        },
    "PERMEABLE_EVENT_TYPES": [
        QUIT,
        VIDEORESIZE,
        PROPERTY_CHANGE
        ],
    "KEY_MODIFIERS": {
        "left_shift": KMOD_LSHIFT,
        "right_shift": KMOD_RSHIFT,
        "caps_lock": KMOD_CAPS,
        "capitalize": KMOD_LSHIFT | KMOD_RSHIFT | KMOD_CAPS,
        "control": KMOD_CTRL,
        "alt": KMOD_ALT
        }
    }
