from typing import Tuple, Dict, List, Optional, Any
from itertools import count
from pathlib import Path
from textwrap import wrap
from textwrap import wrap
import json
from typing import Any, Dict, Tuple


def default_texts() -> Tuple[
Dict[str, Any],
Dict[str, Any],
Dict[str, Any],
]:
    """
    Returns the default application texts.


    Used when the language JSON file cannot be loaded.

    Returns:
        Tuple containing:
            - UX messages
            - Status messages
            - Warning messages
            - Error messages
    """

    ux = {
        "welcome": "Welcome to A-Maze-ing!",
        "goodbye": "Thanks for playing A-Maze-ing. Goodbye!",
        "main_menu": "Main Menu",
        "select_option": "Select an option:",
        "select_map": "Select an option:",
        "select_map_instructions": "Select an option:",
        "press_enter": "Press ENTER to continue.",
    }

    status = {
        "loading": "Loading...",
        "generating_maze": "Generating maze...",
        "maze_ready": "Maze generated successfully.",
        "saving": "Saving...",
        "completed": "Operation completed successfully.",
    }

    warning = {
        "invalid_option": "Invalid option selected.",
        "invalid_value": "The value entered is not valid.",
        "out_of_range": "The value is outside the allowed range.",
        "unsaved_changes": "You have unsaved changes.",
        "default_configuration": "Using the default configuration.",
    }

    error = {
        "file_not_found": "The requested file could not be found.",
        "invalid_configuration": "The configuration is invalid.",
        "invalid_input": "The input could not be understood.",
        "loading_failed": "Failed to load the requested resource.",
        "unknown_error": "An unexpected error occurred.",
    }

    return ux, status, warning, error

def import_texts(
    language: str,
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """Imports application texts safely from a JSON file.

    Args:
        language (str): Locale code (e.g., 'en').

    Returns:
        Tuple[Dict, Dict, Dict, Dict]: UX, status, warnings, errors.
    """
    LANG_ROOT_PATH = Path("lang")
    file = LANG_ROOT_PATH / f"{language}_texts.json"

    try:
        print("Loading texts...", end="")
        with open(file, "r") as raw:
            texts = json.load(raw)
            print(" OK")
            return (
                texts["ux"],
                texts["status"],
                texts["warning"],
                texts["error"],
            )

    except FileNotFoundError:
        print(" FAIL")
        print("WARNING: Language file not found.")
        print("Using default texts.")
        return default_texts()
    except (json.JSONDecodeError, KeyError) as e:
        print(" FAIL")
        print(f"WARNING: Invalid language file: {e}")
        print("Using default texts.")
        return default_texts()


UX, STATUS, WARNING, ERROR = import_texts("en")
GRID_HEIGHT = 100
GRID_WIDTH = 200
UX_MAX: int = 500
UX_STD: int = 100
DELAY: float = 0.5
FAST: float = 0.1
DIRECT: float = 0.0
PACE = DELAY
path_id_generator = count(1)
drone_helices = count(1)




def wait_for_enter(message: Optional[str]) -> None:
    """Halts execution until the user presses the 'Enter' key.

    Args:
        message (str, optional): Custom override string to display.
    """
    if message is None:
        message = UX["press_enter"]
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