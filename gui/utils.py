import os
from typing import List, Optional
from textwrap import wrap
from functools import lru_cache
import sys


def wait_for_enter(message: Optional[str]) -> None:
    """Halts execution until the user presses the 'Enter' key.

    Args:
        message (str, optional): Custom override string to display.
    """
    if message is None:
        message = "Press ENTER to continue..."
    input(message)


def slice_str(
    str_list: List[str], max_char_line: int, max_lines: int
) -> List[str]:
    """Truncates a list of strings to fit column and height limits.

    Args:
        str_list (List[str]): The incoming unsanitized rows.
        max_char_line (int): Maximum characters per line.
        max_lines (int): Maximum allowed height.

    Returns:
        List[str]: Strings formatted into constrained boundaries.
    """
    str_list = str_list[:max_lines]
    new = [line for s in str_list for line in wrap(s, max_char_line)]
    return new


def hex_to_ansi_fg(hex_color: str) -> str:
    """Convert '#rrggbb' to a 24-bit truecolor ANSI foreground escape."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"\033[38;2;{r};{g};{b}m"


def hex_to_ansi_bg(hex_color: str) -> str:
    """Convert '#rrggbb' to a 24-bit truecolor ANSI background escape."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"\033[48;2;{r};{g};{b}m"

def clear_screen(self) -> None:
    """Clears the console or terminal screen cleanly."""
    os.system("cls" if os.name == "nt" else "clear")


def is_terminal() -> bool:
    """Check if stdout is connected to a terminal (TTY)."""
    return sys.stdout.isatty()

@lru_cache
def supports_ansi() -> bool:
    """
    Best-effort check for whether stdout will interpret ANSI escape codes.
    """
    if os.environ.get("NO_COLOR") is not None:
        return False

    if not sys.stdout.isatty():
        return False

    term = os.environ.get("TERM", "")
    if term in ("dumb", ""):
        return False

    return True


def should_use_ansi() -> bool:
    if not is_terminal():
        return False
    elif not supports_ansi():
        return False
    return True


def clear_screen(is_ansi: bool = True) -> None:
    """Call this ONCE, before the animation loop starts."""
    if is_ansi:
        sys.stdout.write("\033[2J\033[H")
    else:
        os.system("cls" if sys.platform == "Windows" else "clear")
    sys.stdout.flush()


def clear_from_cursor() -> None:
    sys.stdout.write("\x1b[J")


def print_char(char: str) -> None:
    sys.stdout.write(char)


def cursor_home() -> None:
    sys.stdout.write("\033[H")


def hide_cursor() -> None:
    sys.stdout.write("\033[?25l")


def show_cursor() -> None:
    sys.stdout.write("\033[?25h")


def move_cursor(row: int, col: int) -> None:
    sys.stdout.write(f"\033[{row};{col}H")


def move_cursor_right(columns: int) -> None:
    sys.stdout.write(f"\033[{columns}C")


def move_cursor_up(rows: int) -> None:
    sys.stdout.write(f"\033[{rows}A")

def move_cursor(row: int, col: int) -> None:
    sys.stdout.write(f"\033[{row};{col}H")

def exit_program() -> str:
    """Exits the application gracefully displaying parting graphics."""
    clear_screen()
    print("\n\n")
    print("Thanks for using Fly-in!\n")
    sys.exit(0)
