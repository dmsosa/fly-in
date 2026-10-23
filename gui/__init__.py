from .printers import FlyinPrinter
from .terminal_gui import TerminalGui
from .utils import clear_screen, \
    clear_from_cursor, \
    move_cursor, \
    move_cursor_up, \
    exit_program, \
    should_use_ansi, \
    wait_for_enter
from .constants import UX_MAX, \
    UX_STD, \
    DELAY, \
    FAST_DELAY, \
    DIRECT
from .pygame_gui import PYGAME_AVAILABLE

# Importing the view without pygame installed must fail here (instead of
# crashing later when the window is created), so ``main`` can fall back
# to the terminal view only.
if PYGAME_AVAILABLE:
    from .pygame_gui import FlyinPygameGui  # noqa: F401


__all__ = [
    "FlyinPrinter",
    "TerminalGui",
    "clear_screen",
    "clear_from_cursor",
    "move_cursor",
    "move_cursor_up",
    "exit_program",
    "should_use_ansi",
    "wait_for_enter",
    "UX_MAX",
    "UX_STD",
    "DELAY",
    "FAST_DELAY",
    "DIRECT"
]

if PYGAME_AVAILABLE:
    __all__.append("FlyinPygameGui")
