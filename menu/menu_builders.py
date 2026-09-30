"""Functions that build the startup menus."""
import sys
from typing import Callable

from parser.parser import FlyinConfiguration, Level
from menu.menu import Menu, MenuItem

# (label, optional hotkey letter, action)


MenuOption = tuple[str, str | None, Callable[[], None]]


def build_menu(name: str, options: list[MenuOption]) -> Menu:
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





def build_level_menu(
    configuration: FlyinConfiguration,
    on_selected: Callable[[], None],
) -> Menu:
    """Menu 1: easy / medium / hard / challenger / custom file.

    Args:
        configuration: Receives the chosen level or custom path.
        on_selected: Called after a choice (advance the menu state).
    """
    def choose_level(level: Level) -> Callable[[], None]:
        def action() -> None:
            configuration.set_level(level)
            on_selected()
        return action

    def choose_custom() -> None:
        input_custom_file(configuration)
        on_selected()

    options: list[MenuOption] = [
        (level.value.capitalize(), level.value[0], choose_level(level))
        for level in Level
    ]
    options.append(("Custom file", "f", choose_custom))
    return build_menu("Flyin menu - select level", options)


def build_filename_menu(
    configuration: FlyinConfiguration,
    on_selected: Callable[[], None],
) -> Menu:
    """Menu 2: one item per *.txt map of the selected level directory."""
    directory = configuration.level_directory()
    names = sorted(p.name for p in directory.glob("*.txt")) \
        if directory.is_dir() else []

    def choose_file(file_name: str) -> Callable[[], None]:
        def action() -> None:
            configuration.set_file_name(file_name)
            on_selected()
        return action

    def choose_custom() -> None:
        input_custom_file(configuration)
        on_selected()

    options: list[MenuOption] = [
        (name, None, choose_file(name)) for name in names
    ]
    options.append(("Custom file", "f", choose_custom))
    level = configuration.get_level()
    title = level.value if level else "?"
    return build_menu(f"Flyin menu - select map ({title})", options)
