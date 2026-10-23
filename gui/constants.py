# STRINGS
GRID_HEIGHT = 100
GRID_WIDTH = 200
UX_MAX: int = 500
UX_STD: int = 100
DELAY: float = 0.5
FAST_DELAY: float = 0.1
DIRECT: float = 0.0


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
    "primary":    "#00d916",
    "secondary": "#2AB5B5",
    "tertiary":   "#B5A724",
    "danger":   "#ff0000",
    "bg-secondary":"#242424",
    "connection-primary": "#6edc00",
    "connection-secondary": "#dc8f00",
    "warning": "#fdbe00",
    "info": "#66d19d",
    "blue": "#0071a9",
    "cyan": "#009ba9",
    "orange": "#f47b18",
    "black": "#151515",
    "yellow": "#e7b614",
    "red": "#c40000",
    "green": "#21c400",
    "purple": "#a9009e",
    "maroon": "#AC4626",
    "brown": "#662000",
    "crimson": "#ac0000",
    "darkred": "#5b0000",
    "gold": "#dc8f00",

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

COLOR_MAP = {
    "green": "\033[32m",
    "red": "\033[31m",
    "blue": "\033[34m",
    "yellow": "\033[33m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "gray": "\033[90m",
    "orange": "\033[38;5;208m",
    "purple": "\033[38;5;129m",
    "gold": "\033[38;5;220m",
    "brown": "\033[38;5;130m",
    "maroon": "\033[38;5;88m",
    "darkred": "\033[38;5;160m",
    "crimson": "\033[38;2;220;20;60m",
    "violet": "\033[38;5;177m",
    "lime": "\033[38;5;118m",
    "black": "\033[30m",
}

# Text styles
BOLD = "\033[1m"
ITALIC = "\033[3m"
DIM = "\033[2m"
UNDERLINE = "\033[4m"
BLINK = "\033[5m"
