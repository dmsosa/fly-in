import sys

from gui import FlyinGuiPrinter, ERROR
from menu import MenuKey, read_menu_key
from menu import FlyinMenu, MenuState
from menu.utils import clear_from_cursor, clear_screen, move_cursor_after_grid, should_use_ansi
from model.graph import FlyinGraph
from parser import FlyinParser


def run_flyin_menu() -> None:
    is_ansi = should_use_ansi()
    
    menu = FlyinMenu()
    gui_printer = FlyinGuiPrinter()
    gui_printer.is_ansi = is_ansi
    while menu.get_menu_state() is not MenuState.EXIT:
        clear_screen(is_ansi)
        menu_state = menu.get_menu_state()
        if menu_state is MenuState.RUN:
            break
        active_menu = menu.level_menu if menu_state \
            is MenuState.LEVEL else menu.filename_menu
        try:
            gui_printer._print_menu_ascii(active_menu)
            key = read_menu_key()
            if key is MenuKey.UP:
                active_menu.move_up()
            elif key is MenuKey.DOWN:
                active_menu.move_down()
            elif key is MenuKey.SELECT:
                active_menu.selected_item().action()
            elif key is MenuKey.EXIT:
                if menu_state is MenuState.FILE_NAME:
                    menu.set_menu_state(MenuState.LEVEL)
                else:
                    menu.quit()
                    print("Say goodbye")
                    sys.exit(1)
            else:
                active_menu.get_item(key).action()
        except FileExistsError as e:
            print(f"Unknown key pressed for {e}")
    file_path = menu.get_path_to_config()
    if not file_path:
        print(f"No file path found")
        sys.exit(1)
    return file_path


def main() -> None:
    # First, let the user choose the configuration file to open
    argv_len = len(sys.argv)
    if argv_len == 1:
        config_file_path = run_flyin_menu()
    elif argv_len == 2:
        config_file_path = sys.argv[1]
    else:
        print(ERROR[""])
        sys.exit(1)

    graph = FlyinGraph()
    parser = FlyinParser()
    parser.parse(config_file_path, graph)
    # After initializing the graph find the solutions for it, and print
    # solver = GraphSolver
    # while 
    # simulator.run() 

    # while not all drons in hub_end:
    #     turn count ++
    #     for each drone do:
    #         find all shortests zone or find possible paths 
    #             # choose_random_path
    #             if this zone is not in maximum, move to 
    #         if not found possible path 
    #         drone.status = wait 
    #         continue
    #     outputfile.append(turn_to_str)
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
