# src/player/menu.py
from pathlib import Path
from typing import List, Union
from gui import FlyinPrinter, \
    move_cursor_up, \
    clear_screen
from .keys import MenuKey, read_menu_key


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
    def __init__(self, printer: FlyinPrinter) -> None:
        """Start with nothing selected."""
        self.items: List[str]
        self._config_dir: Path | None = None
        self._file_name: Path | None = None
        self._path_to_config: Path | None = None
        self.active_menu: Menu | None
        self.printer: FlyinPrinter = printer

    def run_select_path_menu(self) -> None:
        current_dir = MAPS_ROOT
        while True:
            clear_screen()

            print(f"\nSelect the map file to be open\n")
            current_rel = current_dir.relative_to(MAPS_ROOT)
            print(f" 📁 Path: {current_rel}\n")

        
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
                print("❌ Permission denied")
                continue

            if len(self.items) == 0:
                print("❌ No folders or .txt files found")
                continue
    
            self.items.append("❌  Exit")
            paths.append(None)

            self.active_menu = Menu(
                "Select an option:",
                self.items
                )

            idx = None
            while idx is None:
                menu_height = len(self.active_menu.items)
                move_cursor_up(menu_height)
                self.printer.print_menu(self.active_menu)
                idx = self.active_menu.run()

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

    def run_confirm_file_map(self) -> None:
        self.items = [
            "Continue with simulation",
            "Choose another file",
            "Exit the program"
        ]
        self.active_menu = Menu(
            "Select an option:",
            self.items
            )

        idx = None
        while idx is None:
            menu_height = len(self.items)
            move_cursor_up(menu_height)
            self.printer.print_menu(self.active_menu)
            idx = self.active_menu.run()

        return idx

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
