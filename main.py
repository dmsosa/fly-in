from curses import ERR
import sys

from pydantic import ValidationError

from error.error import FlyinParseError
from gui import FlyinGuiPrinter, ERROR
from menu import FlyinMenu
from gui.printers_utils import clear_screen, should_use_ansi
from model.graph import FlyinGraph
from parser import FlyinParser


def main() -> None:
    # First, let the user choose the configuration file to open
    # As I want to do this various times, is enough to wrap it inside a while loop
    config_file_path = None

    argv_len = len(sys.argv)
    if argv_len == 1:
        menu.run_select_path_menu()
        config_file_path = menu.get_path_to_config()
    elif argv_len == 2:
        config_file_path = sys.argv[1]
    else:
        print(ERROR["critical"]["usage"])
        sys.exit(1)
    
    is_ansi = should_use_ansi()
    gui_printer = FlyinGuiPrinter()
    gui_printer.is_ansi = is_ansi
    gui_printer.prettify = True
    menu = FlyinMenu(gui_printer)

    gui_printer.print_presentation()
    try:
        parser = FlyinParser()
        graph_data = parser.parse(config_file_path)
    except PermissionError:
        print(ERROR["parser"]["file_permission"])
    except FileNotFoundError:
        print(ERROR["parser"]["file_not_found"])
    except IOError:
        print(ERROR["parser"]["io_error"])
    except FlyinParseError as e:
        print(ERROR["parser"]["parsing_error"])
        print(f"   └── {e}\n")
        sys.exit(1)
    except Exception as e:
        print(ERROR["unkown_error"])
        print(f"   └── {e}\n")
        sys.exit(1)

    try:
        graph = FlyinGraph(**graph_data)
        # This parser is going to build what? a config object or a class directly?
        # It reads line by line, if it is a nb_drones line, assign the nb_drones. if it has start_hub, end_hub or hub
        graph.init_graph()

    except ValidationError as e:
        clear_screen()
        print(ERROR["parser"]["parsing_error"])
        for error in e.errors():
            field_loc = " -> ".join(str(loc) for loc in error["loc"])
            display_loc = (
                field_loc if field_loc else "Configuration File"
            )
            print(f"   └── [{display_loc}] {error['msg']}\n")
    
    except Exception as e:
        print(ERROR["unkown_error"])
        print(f"   └── {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except EOFError:
        print(ERROR["eof"])
    except KeyboardInterrupt:
        print(ERROR["keyboard_interrupt"])
