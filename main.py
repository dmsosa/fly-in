import argparse
import sys
import traceback
from pydantic import ValidationError
from error.error import FlyinError, FlyinParseError, FlyinUnreachableError
from gui import DELAY, \
        DIRECT, \
        FAST_DELAY, \
        TerminalGui, \
        exit_program, \
        should_use_ansi, \
        wait_for_enter, \
        FlyinPrinter
from menu import FlyinMenu
from model.graph import FlyinGraph
from orchestrator.orchestrator import Orchestrator
from parser import FlyinParser
from pathfinding.dijkstra import DijkstraPathfinding


__author__ = "Durian Sosa"
__email__ = "durisosa@student.42madrid.com"


def parse_and_init_graph(
    config_file: str, parser: FlyinParser
) -> tuple[str, FlyinGraph] | None:
    try:
        parser = FlyinParser()
        graph_data = parser.parse(config_file)
    except PermissionError as e:
        print(f"❌ Permission denied to file: \n{e}")
        print("   Closing the program.")
        return None
    except FileNotFoundError as e:
        print(f"❌ No folders or .txt files found: \n{e}")
        print("    Closing the program.")
        return None
    except IOError as e:
        print(f"IO Error: \n{e}")
        return None
    except FlyinParseError as e:
        print("Exception while parsing.")
        print(f"   └── {e}\n")
        return None
    except Exception as e:
        print("An unexpected error occurred.")
        print(f"   └── {e}\n")
        return None

    try:
        graph = FlyinGraph(**graph_data)
    except ValidationError as e:
        print("Exception while creating graph class.")
        for error in e.errors():
            field_loc = " -> ".join(str(loc) for loc in error["loc"])
            display_loc = (
                field_loc if field_loc else "Configuration File"
            )
            print(f"   └── [{display_loc}] {error['msg']}\n")
        return None

    except Exception as e:
        print("An unexpected error occurred.")
        print(f"   └── {e}\n")
        traceback.print_exc(file=sys.stderr)
        return None

    return graph_data["filename"], graph


def main() -> None:
    # First, let the user choose the configuration file to open
    # As I want to do this various times, wrapping it in a while loop
    # is enough.
    arg_parser = argparse.ArgumentParser(
         description="Fly-in drone fleet routing simulator."
    )
    arg_parser.add_argument(
        "map",
        nargs='?',
        default=None,
        help="Path to the map text file"
    )
    arg_parser.add_argument(
        "-m",
        "--map",
        dest="map_flag",
        default=None,
        help="Path to the map text file"
    )
    arg_parser.add_argument(
        "-c",
        "--color",
        default=True,
        action="store_true",
        help="Enable colored visual terminal display and metrics",
    )


    args = arg_parser.parse_args()

    map_file_arg = None
    if args.map:
        map_file_arg = args.map
    elif args.map_flag:
        map_file_arg = args.map_flag

    verbose = args.verbose
    color_terminal = args.color

    is_ansi = should_use_ansi()
    printer = FlyinPrinter()
    printer.is_ansi = is_ansi

    menu = FlyinMenu(printer)
    parser = FlyinParser()

    while True:
        while True:
            if map_file_arg is None:
                printer.print_presentation()
                menu.run_select_path_menu()
                config_file = menu.get_path_to_config()
            else:
                config_file = map_file_arg
            map_file_arg = None

            # The menu can come back with nothing selected.
            if config_file is None:
                continue

            parse_result = parse_and_init_graph(str(config_file), parser)

            if not parse_result:
                wait_for_enter("Press ENTER to exit.")
                sys.exit(1)

            filename, graph = parse_result
            if menu.run_confirm_file_map(filename):
                break

        manual = False
        direct = False
        delay = DELAY
        config = menu.run_configure_ui_menu()
        if config == 0:
            manual = True
        elif config == 1:
            direct = True
            delay = DIRECT
        elif config == 2:
            delay = DELAY
        elif config == 3:
            delay = FAST_DELAY
        else:
            direct = True
            delay = DIRECT

        pathfinding = DijkstraPathfinding(graph)
        orchestrator = Orchestrator(graph=graph, pathfinding=pathfinding)

        # Solvable map with disconnected islands: they can never take part
        # in a delivery, so they are only worth a heads-up.
        if pathfinding.is_end_reachable():
            islands = pathfinding.unreachable_zones()
            if islands:
                print(
                    "⚠ Warning: zone(s) with no route to the goal"
                    f" (ignored): {', '.join(islands)}",
                    file=sys.stderr,
                )

        try:
            history = orchestrator.run_orchestra()
            orchestrator.export_turns()
            terminal_gui = TerminalGui(
                graph,
                manual,
                direct,
                color_terminal,
                delay
                )
            terminal_gui.print_history(history, orchestrator.reservation_table)
        except FlyinUnreachableError as e:
            # Not a bug in the schedule: the map itself has no solution.
            # Report it and let the user pick another one.
            print(f"❌ {e}")
            wait_for_enter("\n Choose another map...")
            continue
        except FlyinError as e:
            print(e)
            wait_for_enter("\n Exit the program gracefully.")
            sys.exit(1)

        title = "The program work finished, do you want to continue?"
        if menu.run_continue_menu(title) == 0:
            continue
        exit_program()


if __name__ == "__main__":
    try:
        main()
    except EOFError:
        print("End of file reached. Exiting gracefully.")
    except KeyboardInterrupt:
        print(
            "Program interrupted by user (Ctrl+C). Exiting gracefully."
            )
