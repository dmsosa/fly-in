import sys
import traceback

from pydantic import ValidationError

from error.error import FlyinParseError
from gui.gui import FlyinGui
from gui.utils import exit_program, wait_for_enter
from menu import FlyinMenu
from gui import FlyinPrinter
from gui.printers_utils import clear_screen, should_use_ansi, supports_ansi
from model.graph import FlyinGraph
from parser import FlyinParser


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
        # This parser is going to build what? a dict
        # the dict then is used to instantiate the graph using
        # Pydantic validations.

        # The graph starts with all drones in the start node
        # It also modifies zone objects to give value to its
        # self.connections Attribute. Which is an array of
        # connections that zones has.
        graph.init_graph()
    
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
    printer.print_presentation()

    menu = FlyinMenu(printer)
    parser = FlyinParser()
    while True:
        while True:
            if config_file_arg is None:
                menu.run_select_path_menu()
                config_file = menu.get_path_to_config()
            else:
                config_file = config_file_arg 
            config_file_arg = None

            graph = parse_and_init_graph(config_file, parser)

            if not graph:
                continue

            gui = FlyinGui(graph=graph)
            if gui.confirm_map_file(graph.filename, menu):
                break
            orchestrator = Orchestrator(graph)
            while orchestrator.drones_finished < orchestrator.drones_count:
                turn_str = orchestrator.next_turn()
                # the first step to be able to move all drones is to move a single drone, one at the time
                # one drone is going to cose the shortest path everytime, it wil no reach dead ends because I can already discard them with the heuristic function
                orchestrator.output_turn(turn_str)


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
