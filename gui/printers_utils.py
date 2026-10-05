from functools import lru_cache
import os
import sys


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
