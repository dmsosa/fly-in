import sys
import traceback

from pydantic import ValidationError

from error.error import FlyinParseError
from gui.gui import FlyinGui
from gui.terminal_gui import TerminalGui
from gui.utils import exit_program, wait_for_enter
from menu import FlyinMenu
from gui import FlyinPrinter
from gui.terminal_utils import clear_screen, should_use_ansi, supports_ansi
from model.graph import FlyinGraph
from orchestrator.orchestrator import Orchestrator
from parser import FlyinParser
from pathfinding.dijkstra import DijkstraPathfinding


def parse_and_init_graph(config_file: str, parser: FlyinParser) -> None:
    try:
        parser = FlyinParser()
        graph_data = parser.parse(config_file)
    except PermissionError as e:
        print(f"❌ Permission denied to file: \n{e}")
    except FileNotFoundError as e:
        print(f"❌ No folders or .txt files found: \n{e}")
    except IOError as e:
        print(f"IO Error: \n{e}")
    except FlyinParseError as e:
        print("Exception while parsing.")
        print(f"   └── {e}\n")
        sys.exit(1)
    except Exception as e:
        print("An unexpected error occurred.")
        print(f"   └── {e}\n")
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

    graph = None
    try:
        graph = FlyinGraph(**graph_data)
    except ValidationError as e:
        clear_screen()
        print("Exception while creating graph class.")
        for error in e.errors():
            field_loc = " -> ".join(str(loc) for loc in error["loc"])
            display_loc = (
                field_loc if field_loc else "Configuration File"
            )
            print(f"   └── [{display_loc}] {error['msg']}\n")
        wait_for_enter(None)

    except Exception as e:
        print("An unexpected error occurred.")
        print(f"   └── {e}\n")
        traceback.print_exc(file=sys.stderr)
        wait_for_enter(None)
        exit_program()

    return graph


def main() -> None:
    # First, let the user choose the configuration file to open
    # As I want to do this various times, is enough to wrap it inside a while loop
    config_file_arg = None

    argv_len = len(sys.argv)
    if argv_len == 2:
        config_file_arg = sys.argv[1]
    elif argv_len > 2:
        print(
            "CRITICAL ERROR: \
            Usage of the program is flyin.py [config_file]"
            )
        sys.exit(1)

    is_ansi = should_use_ansi()
    printer = FlyinPrinter()
    printer.is_ansi = is_ansi


    menu = FlyinMenu(printer)
    parser = FlyinParser()
    while True:
        while True:
            if config_file_arg is None:
                printer.print_presentation()
                menu.run_select_path_menu()
                config_file = menu.get_path_to_config()
            else:
                config_file = config_file_arg 
            config_file_arg = None

            graph = parse_and_init_graph(config_file, parser)

            if not graph:
                continue

            gui = FlyinGui(graph=graph)

            if not gui.confirm_map_file(graph.filename, menu):
                break

            pathfinding = DijkstraPathfinding(graph)
            orchestrator = Orchestrator(graph=graph, pathfinding=pathfinding)
            history = orchestrator.run_orchestra()
            orchestrator.export_turns()

            terminal_gui = TerminalGui(graph, orchestrator.reservation_table, history)
            terminal_gui.print_history()
            input()
            


        # What I need to start another simulation ... ?
        # Know if the user wants to do it, handled by try_again Menu
        # 

        try_again = input("try aain")
        if try_again == "si":
            continue
        elif try_again == "no":
            break
        else:
            continue
        





if __name__ == "__main__":
    try:
        main()
    except EOFError:
        print("End of file reached. Exiting gracefully.")
    except KeyboardInterrupt:
        print("Program interrupted by user (Ctrl+C). Exiting gracefully.")
