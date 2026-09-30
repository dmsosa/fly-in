# src/player/menu.py
from enum import Enum
import sys
from typing import Any, Callable

from zipp import Path

from menu.menu_builders import MenuOption, build_menu, input_custom_file

class MenuState(Enum):
    MENU = "menu"
    LEVEL = "level"
    FILE_NAME = "filename"
    RUN = "run"
    EXIT = "exit"

class Level(Enum):
    """Difficulty levels, each one backed by a maps directory."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    CHALLENGER = "challenger"



MAPS_ROOT = Path("maps")


class MenuItem:
    def __init__(
            self,
            key: str,
            label: str,
            keys: set[str],
            action: Callable[..., Any]
    ):
        self.key = key
        self.label = label
        self.action = action
        self.keys = keys


class Menu:
    def __init__(self, name: str, items: list[MenuItem]):
        self.name = name
        self.items = items
        self.selected_index: int = 0
        self.items_len = len(items)

    def get_item(self, key: str) -> MenuItem:
        for idx, item in enumerate(self.items):
            if key in item.keys:
                self.selected_index = idx
                return item
        raise KeyError(
            f"MenuItem with key '{key}' not found in menu '{self.name}'"
        )

    def move_up(self) -> None:
        self.selected_index = (self.selected_index - 1) % self.items_len

    def move_down(self) -> None:
        self.selected_index = (self.selected_index + 1) % self.items_len

    def selected_item(self) -> MenuItem:
        return self.items[self.selected_index]


#"""Run configuration chosen by the user through the menus."""
class FlyinMenu():
    """
    Holds metadata about the current Flyin Program
    and contains the menus the user can interact with.
    """
    def __init__(self) -> None:
        """Start with nothing selected."""
        self._level: Level = Level.EASY
        self._file_name: str | None = None
        self._path_to_config: Path | None = None
        self._menu_state: MenuState = MenuState.LEVEL
        self._level_menu: Menu | None = None
        self._filename_menu: Menu | None = None

    # ---- state ------------------------------------------------------
    def get_menu_state(self) -> Level | None:
        """Return the selected menu_state, or None."""
        return self._menu_state

    def set_menu_state(self, menu_state: MenuState | str) -> None:
        """Select a MenuState or its string value ("level")."""
        self._menu_state = menu_state if isinstance(menu_state, MenuState) else Level(menu_state)

    # ---- menus ------------------------------------------------------
    def build_level_menu(self, on_selected: Callable[..., Any]) -> None:
        """Menu 1: easy / medium / hard / challenger / custom file.

        Args:
            configuration: Receives the chosen level or custom path.
            on_selected: Called after a choice (advance the menu state).
        """
        items = [
            MenuItem()
        ]
        self._level_menu = Menu("Flyin menu - select level")
        def choose_level(level: Level) -> Callable[[], None]:
            def action() -> None:
                self.set_level(level)
                on_selected()
            return action

        def choose_custom() -> None:
            self.input_custom_file()
            on_selected()

            options: list[MenuOption] = [
                (level.value.capitalize(), level.value[0], choose_level(level))
                for level in Level
            ]
            options.append(("Custom file", "f", choose_custom))
            return build_menu("Flyin menu - select level", options)

    def input_custom_file(self) -> None:
        """Ask for a config file path on stdin and store it.

        Raises:
            FileNotFoundError: if the path does not exist (caller exits).
        """
        print("Insert custom file name:")
        print(">> ", end="", flush=True)
        path = sys.stdin.readline().strip()
        self.set_path_to_config(path)

    # ---- level ------------------------------------------------------
    def get_level(self) -> Level | None:
        """Return the selected level, or None."""
        return self._level

    def set_level(self, level: Level | str) -> None:
        """Select a level from a Level or its string value ("easy")."""
        self._level = level if isinstance(level, Level) else Level(level)
        self._file_name = None
        self._path_to_config = None

    def level_directory(self) -> Path:
        """Return the maps directory of the selected level."""
        if self._level is None:
            raise ValueError("No level selected")
        return MAPS_ROOT / self._level.value

    # ---- file name --------------------------------------------------
    def get_file_name(self) -> str | None:
        """Return the selected map file name, or None."""
        return self._file_name

    def set_file_name(self, file_name: str) -> None:
        """Select a map inside the current level directory.

        Raises:
            FileNotFoundError: if the file does not exist.
        """
        path = self.level_directory() / file_name
        if not path.is_file():
            raise FileNotFoundError(f"Map file not found: {path}")
        self._file_name = file_name
        self._path_to_config = path

    # ---- path -------------------------------------------------------
    def get_path_to_config(self) -> Path | None:
        """Return the final path of the configuration file, or None."""
        return self._path_to_config

    def set_path_to_config(self, path: str | Path) -> None:
        """Select a custom configuration file (bypasses level/file name).

        Raises:
            FileNotFoundError: if the file does not exist.
        """
        candidate = Path(path)
        if not candidate.is_file():
            raise FileNotFoundError(f"Config file not found: {candidate}")
        self._path_to_config = candidate
        self._file_name = candidate.name
