# STRINGS
import re


USERNAME_REGEXP = re.compile(r"[a-z0-9]{3,15}")


THEME_CHAR = {
    0b0000: " ",
    0b0011: "╚",
    0b1100: "╗",
    0b0110: "╔",
    0b1001: "╝",
    0b0101: "║",
    0b1010: "═",
}

THEME_COLOR = {
    "bg":      "#000000",
    "primary":    "#2121ff",
    "secondary": "#ffff00",
    "tertiary":   "#00ffff",
    "danger":   "#ff0000",
    "bg-secondary":     "#242424",
    "warning": "#fdbe00",
}

MENU_WIDTH = 30


# Reset
RESET = "\033[0m"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"

# Regular colors (bright)
BLACK = "\033[30m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"

# Bold / bright variants
BOLD_BLACK = "\033[90m"
BOLD_RED = "\033[91m"
BOLD_GREEN = "\033[92m"
BOLD_YELLOW = "\033[93m"
BOLD_BLUE = "\033[94m"
BOLD_MAGENTA = "\033[95m"
BOLD_CYAN = "\033[96m"
BOLD_WHITE = "\033[97m"

# Background colors
BG_BLACK = "\033[40m"
BG_RED = "\033[41m"
BG_GREEN = "\033[42m"
BG_YELLOW = "\033[43m"
BG_BLUE = "\033[44m"
BG_MAGENTA = "\033[45m"
BG_CYAN = "\033[46m"
BG_WHITE = "\033[47m"

# Text styles
BOLD = "\033[1m"
ITALIC = "\033[3m"
UNDERLINE = "\033[4m"
BLINK = "\033[5m"
