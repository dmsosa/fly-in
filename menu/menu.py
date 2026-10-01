# src/player/menu.py
from enum import Enum
from pathlib import Path
import sys
from typing import Any, Callable


MenuOption = tuple[str, str | None, Callable[[], None]]

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

    After pressing enter on the LevelMenu, it changes the MenuState to FILE_NAME
    after pressing enter on FILE_NAME, it changes to MenuState.RUN
    """
    def __init__(self) -> None:
        """Start with nothing selected."""
        self._level: Level = Level.EASY
        self._file_name: str | None = None
        self._path_to_config: Path | None = None
        self._menu_state: MenuState = MenuState.LEVEL
        self.level_menu: Menu = self.build_level_menu()
        self.filename_menu: Menu = self.build_filename_menu()

    # ---- state ------------------------------------------------------
    def get_menu_state(self) -> Level | None:
        """Return the selected menu_state, or None."""
        return self._menu_state

    def set_menu_state(self, menu_state: MenuState | str) -> None:
        """Select a MenuState or its string value ("level")."""
        self._menu_state = menu_state if isinstance(menu_state, MenuState) else MenuState(menu_state)

    # ---- menus ------------------------------------------------------
    def _build_menu(self, name: str, options: list[MenuOption]) -> Menu:
        """Build a Menu from plain option tuples.

        Every item gets its 1-based number as a key, plus its hotkey letter
        (both cases) when given.

        Raises:
            ValueError: on empty options or duplicated keys.
        """
        items: list[MenuItem] = []
        used: set[str] = set()
        for idx, (label, hotkey, action) in enumerate(options, start=1):
            keys = {str(idx)}
            shown = str(idx)
            if hotkey:
                keys |= {hotkey.upper(), hotkey.lower()}
                shown = hotkey.upper()
            if keys & used:
                raise ValueError(f"Duplicated menu key for '{label}'")
            used |= keys
            items.append(MenuItem(shown, label, keys, action))
        return Menu(name, items)


    def build_level_menu(self) -> None:
        """Menu 1: easy / medium / hard / challenger / custom file.

        Args:
            configuration: Receives the chosen level or custom path.
            on_selected: Called after a choice (advance the menu state).
        """
        def choose_level(level: Level) -> Callable[[], None]:
            def action() -> None:
                self.set_level(level)
                self.filename_menu = self.build_filename_menu()
                self.set_menu_state("filename")
            return action

        def choose_custom() -> None:
            self.input_custom_file()

        options: list[MenuOption] = [
            (level.value.capitalize(), level.value[0], choose_level(level))
            for level in Level
        ]
        options.append(("Custom file", "f", choose_custom))
        return self._build_menu("Flyin menu - select level", options)


    def build_filename_menu(self) -> Menu:
        """Menu 2: one item per *.txt map of the selected level directory."""
        directory = self.level_directory()
        names = sorted(p.name for p in directory.glob("*.txt")) \
            if directory.is_dir() else []

        def choose_file(file_name: str) -> Callable[[], None]:
            def action() -> None:
                self.set_file_name(file_name)
                self.set_menu_state("run")
            return action

        options: list[MenuOption] = [
            (name, None, choose_file(name)) for name in names
        ]
        level = self.get_level()
        title = level.value if level else "?"
        return self._build_menu(f"Flyin menu - select map ({title})", options)


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

    def quit(self) -> None:
        self.set_menu_state(MenuState.EXIT)