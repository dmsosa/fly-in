import sys

from gui.printers import FlyinGuiPrinter
from menu.keys import MenuKey, read_menu_key
from menu import build_filename_menu, build_level_menu
from menu.menu import FlyinMenu
from model.graph import FlyinGraph
from parser import MenuState, Level
from menu.utils import ERROR, print_menu_ansi
from parser.parser import FlyinParse
from parser.parser import FlyinParser


def main() -> None:
    # First, let the user choose the configuration file to open
    argv_len = len(sys.argv)
    # if argv_len != 2:
    #     config_file_path = level + config_file
    # else:
    #     config_file_path = argv[1]
    menu = FlyinMenu()
    level_menu = build_level_menu(
        menu,
        lambda : menu.set_menu_state(MenuState.FILE_NAME)
        )
    file_menu = build_filename_menu(
        menu,
        lambda : menu.set_menu_state(MenuState.RUN)
    )
    while menu.get_menu_state() is not MenuState.EXIT:
        menu_state = menu.get_menu_state()
        if menu_state is MenuState.RUN:
            break
        active_menu = menu.level_menu if menu_state \
            is MenuState.LEVEL else menu.file_menu
        try:
            print_menu_ansi(active_menu)
            key = read_menu_key()
            if key is MenuKey.UP:
                active_menu.move_up()
            elif key is MenuKey.DOWN:
                active_menu.move_down()
            elif key is MenuKey.SELECT:
                active_menu.selected_item().action()
            elif key is MenuKey.EXIT:
                menu.set_menu_state(MenuState.EXIT)
                print("Say goodbye")
                sys.exit(1)
            else:
                active_menu.get_item(key).action()
        except KeyError as e:
            print(f"Unknown key pressed for {e}")
    file_path = menu.get_path_to_config()
    if not file_path:
        print(f"No file path found")
        sys.exit(1)
    graph = FlyinGraph()
    try:
        FlyinParser.parse(file_path, graph)
        printer = FlyinGuiPrinter()
        printer.print_presentation()
    except PermissionError:
        print(ERROR["file_permission"])
    except FileNotFoundError:
        print(ERROR["file_not_found"])
    except Exception as e:
        print(ERROR["unkown"])

if __name__ == "__main__":
    try:
        main()
    except EOFError:
        print("End of file reached. Exiting gracefully.")
    except KeyboardInterrupt:
        print("Program interrupted by user (Ctrl+C). Exiting gracefully.")
