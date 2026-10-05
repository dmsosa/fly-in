# src/player/menu.py
from pathlib import Path
from typing import List, Union
from gui.constants import THEME_CHAR, THEME_COLOR, MENU_WIDTH
from gui.printers import FlyinGuiPrinter
from gui.utils import UX, hex_to_ansi_fg
from menu.keys import MenuKey, read_menu_key
from gui.printers_utils import move_cursor


MAPS_ROOT = Path(".")


class MenuItem:
    def __init__(
            self,
            key: str,
            label: str,
            keys: set[str],
    ):
        self.key = key
        self.label = label
        self.keys = keys


class Menu:
    def __init__(
            self,
            name: str,
            items: list[str],
            ):
        self.name = name
        self.items = []
        for idx, item in enumerate(items):
            self.items.append(MenuItem(str(idx), item, { item[0], item[0].upper, str(idx) }))
        self.selected_index: int = 0
        self.items_len: int = len(items)

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

    def run(self) -> Union[int, None]:
        try:
            key = read_menu_key()
            if key is MenuKey.UP:
                self.move_up()
                return None
            elif key is MenuKey.DOWN:
                self.move_down()
                return None
            elif key is MenuKey.SELECT:
                return self.selected_index
            elif key is MenuKey.EXIT:
                return -1
            else:
                selected_item = self.get_item(key)
                index = 0
                for i in self.items:
                    if selected_item.key == i.key:
                        return index
                    index += 1
                return None
        except KeyError as e:
            print(f"Unknown key pressed for menu '{self.name}'\n{e}")
            

#"""Run configuration chosen by the user through the menus."""
class FlyinMenu():
    """
    Holds metadata about the current Flyin Program
    and contains the menus the user can interact with.
    It builds interactive menus to build its own object
    the interactive menu is just a while loop that returns
    an index.

    After pressing enter on the LevelMenu, it changes the MenuState to FILE_NAME
    after pressing enter on FILE_NAME, it changes to MenuState.RUN
    """
    def __init__(self, printer: FlyinGuiPrinter) -> None:
        """Start with nothing selected."""
        self.items: List[str]
        self._config_dir: Path | None = None
        self._file_name: Path | None = None
        self._path_to_config: Path | None = None
        self.active_menu: Menu | None
        self.printer = printer

    # ---- menus ------------------------------------------------------
    def print_menu(
            self,
            menu: Menu,
            mark: bool = True,
            scale: int = 3,
            frame: bool = False
            ) -> None:
        if self.printer.is_ansi:
            self._print_menu_ansi(menu, mark, scale, frame)
        else:
            self._print_menu_ascii(menu, mark, scale, frame)


    def _print_menu_ascii(
            self,
            menu: Menu,
            mark: bool = True,
            scale: int = 3,
            frame: bool = False
            ) -> None:
        chars = [
                THEME_CHAR[0b0110],
                THEME_CHAR[0b1100],
                THEME_CHAR[0b0011],
                THEME_CHAR[0b1001],
                THEME_CHAR[0b1010],
                THEME_CHAR[0b0101],
            ]
        corner_ul = chars[0]
        corner_ur = chars[1]
        corner_bl = chars[2]
        corner_br = chars[3]
        hor_bar = chars[4]
        ver_bar = chars[5]
        top_row = f"{corner_ul}" + hor_bar * MENU_WIDTH * scale + f"{corner_ur}"
        bot_row = f"{corner_bl}" + hor_bar * MENU_WIDTH * scale + f"{corner_br}"
        empty_row = ver_bar + " " * MENU_WIDTH * scale + ver_bar
        if frame:
            lines = [
                top_row,
                ver_bar + "{:^{w}}".format(menu.name, w=MENU_WIDTH * scale) + ver_bar,
                empty_row
            ]
        else:
            lines = []
        for i in range(0, menu.items_len):
            item = menu.items[i]
            is_selected = " >>" if \
                i == menu.selected_index and mark \
                else ""
            text = f"{is_selected} [{item.key}]: {item.label}"
            if frame:
                line = ver_bar + "{:<{w}}".format(text, w=MENU_WIDTH * scale) + ver_bar
            else:
                line = "{:<{w}}".format(text, w=MENU_WIDTH * scale)
            lines.append(line)
        if frame:
            lines.append(empty_row)
            lines.append(bot_row)
        print("\n".join(lines))


    def _print_menu_ansi(
            self,
            menu: Menu,
            mark: bool = True,
            scale: int = 3,
            frame: bool = False
            ) -> None:
        chars = [
                THEME_CHAR[0b0110],
                THEME_CHAR[0b1100],
                THEME_CHAR[0b0011],
                THEME_CHAR[0b1001],
                THEME_CHAR[0b1010],
                THEME_CHAR[0b0101],
            ]
        corner_ul = chars[0]
        corner_ur = chars[1]
        corner_bl = chars[2]
        corner_br = chars[3]
        hor_bar = chars[4]
        ver_bar = chars[5]
        accent = hex_to_ansi_fg(THEME_COLOR["primary"])
        highlight = hex_to_ansi_fg(THEME_COLOR["secondary"])
        reset = "\033[0m"
        top_row = (
            f"{accent}{corner_ul}" + hor_bar * MENU_WIDTH * scale +
            f"{corner_ur}{reset}"
            )
        bot_row = (
            f"{accent}{corner_bl}" + hor_bar * MENU_WIDTH * scale +
            f"{corner_br}{reset}")
        accent_bar = accent + ver_bar + reset
        empty_row = accent_bar + " " * MENU_WIDTH * scale + accent_bar
        if frame:
            lines = [
                top_row,
                accent_bar + "{:^{w}}".format(
                    menu.name, w=MENU_WIDTH * scale) + accent_bar,
                empty_row
            ]
        else:
            lines = []
        for i in range(0, menu.items_len):
            item = menu.items[i]
            is_selected = " >>" if \
                i == menu.selected_index and mark\
                else ""
            color = highlight if is_selected else ""
            reset_color = reset if is_selected else ""
            text = f"{is_selected} [{item.key}]: {item.label}"
            if frame:
                line = accent_bar + color + text.ljust((MENU_WIDTH * scale)) + reset_color + accent_bar
            else:
                line = color + text.ljust((MENU_WIDTH * scale)) + reset_color
            lines.append(line)
        
        if frame:
            lines.append(empty_row)
            lines.append(bot_row)
        print("\n".join(lines))


    def run_select_path_menu(self) -> None:
        current_dir = MAPS_ROOT
        while True:
            self.printer.clear_screen()
            self.printer.print_top_row()
            print()
            print(f" {UX['select_map']}")
            print()
            current_rel = current_dir.relative_to(MAPS_ROOT)
            print(f" 📁 Path: {current_rel}")
            print()
    
            self.items = []
            paths: list[str] = []

            if current_dir != MAPS_ROOT:
                self.items.append("⬅️  Back to parent")
                paths.append("..")
            try:
                entries = sorted(current_dir.iterdir())
                for entry in entries:
                    if entry.name.startswith((".", "_", "venv", "requirements")):
                        continue
                    if entry.is_dir():
                        self.items.append(f"📁 {entry.name}/")
                        paths.append(entry.name)
                    elif entry.suffix == ".txt":
                        self.items.append(f"📄 {entry.name}")
                        paths.append(entry.name)
            except PermissionError:
                print(UX["permission_denied"])
                continue

            if len(self.items) == 0:
                print(UX["no_files_found"])
                continue
    
            self.items.append("❌ Exit")
            paths.append(None)

            self.active_menu = Menu(
                UX["select_map_instructions"],
                self.items
                )

            idx = None
            while idx is None:
                move_cursor(7, 0)
                self.print_menu(self.active_menu)
                idx = self.active_menu.run()

            if idx == -1:
                return None

            selected = paths[idx]
            if selected is None:
                return None

            if selected == "..":
                current_dir = current_dir.parent
                continue

            path = current_dir / selected
            if path.is_dir():
                current_dir = path
                continue
            
            if path.is_file() and path.suffix == ".txt":
                self.set_path_to_config(str(path))
                break 

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
