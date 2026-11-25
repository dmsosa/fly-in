from time import sleep
from .constants import BOLD, DELAY, DIM, COLOR_MAP, MENU_WIDTH, RESET
from .utils import clear_screen, wait_for_enter
from model import FlyinGraph
from orchestrator import Move, ReservationTable


class TerminalGui:
    """
    This class receives a list of movements (Move class)
    and displays them on the screen using ANSI escape sequences
    for colorful output to the terminal
    """
    def __init__(
            self,
            graph: FlyinGraph,
            manual: bool = False,
            direct: bool = False,
            color: bool = True,
            delay: float = DELAY
            ):
        self.graph = graph
        self.manual = manual
        self.direct = direct
        self.color_terminal = color
        self.delay = delay

    def _colorize_rainbow(self, text: str, bold: bool = False) -> str:
        """
        Apply multi-color gradient characters.

        Returns:
            str: colorized sentence to display.
        """
        rainbow_c: list[str] = [
            "\033[31m",
            "\033[33m",
            "\033[32m",
            "\033[36m",
            "\033[34m",
            "\033[35m",
        ]
        prefix = BOLD if bold else ""
        chars = [
            f"{rainbow_c[i % len(rainbow_c)]}{char}"
            for i, char in enumerate(text)
        ]
        return f"{prefix}{''.join(chars)}{RESET}"

    def colorize(
            self,
            text: str,
            color_name: str | None = None,
            bold: bool = False,
    ) -> str:
        """
        Apply styling codes to string.

        Returns:
            str: colorized string to display.
        """
        code: str = BOLD if bold else ""
        c_name = color_name.strip().lower() if color_name else None
        if c_name == "grey":
            c_name = "gray"
        if c_name == "rainbow":
            return self._colorize_rainbow(text, bold)
        if c_name and c_name in COLOR_MAP:
            code += COLOR_MAP[c_name]
        if not code:
            return text
        return f"{DIM}{code}{text}{RESET}"

    def format_move(self, move: Move) -> str:
        """
        Format an individual move token with ANSI colors.

        Returns:
            str: colorized sentence to display.
        """
        if "-" in move.target_name:
            target_a, target_b = move.target_name.split("-", 1)
            zone_a = self.graph.get_zone_by_name(target_a)
            zone_b = self.graph.get_zone_by_name(target_b)
            color_a = zone_a.color if zone_a else None
            color_b = zone_b.color if zone_b else None

            result: str = ""
            if self.color_terminal:
                result = (
                    f"{move.drone_id}-"
                    f"{self.colorize(target_a, color_a, bold=True)}"
                    f"-{self.colorize(target_b, color_b, bold=True)}"
                )
            else:
                result = (
                    f"{move.drone_id}-"
                    f"{target_a}"
                    f"-{target_b}"
                )
            return result

        zone = self.graph.get_zone_by_name(move.target_name)
        color = zone.color if zone else None
        if self.color_terminal:
            return self.colorize(move.to_str(), color, bold=True)
        else:
            return move.to_str()

    def print_history(
            self,
            history: list[list[Move]],
            reservations: ReservationTable,
            verbose: bool = False
    ) -> None:
        if self.direct:
            clear_screen()

        for turn in history:
            turn_id = turn[0].turn_id
            line = []
            if verbose:
                line.append(f"T{turn_id + 1}: ")
            turn_title = f" Turn {turn_id + 1:02d} ".center(MENU_WIDTH, "=")
            print(f"\n{turn_title}")
            sorted_moves = sorted(turn, key=lambda s: s.drone_id)
            for move in sorted_moves:
                line.append(self.format_move(move))
            print(" ".join(line))
            if self.manual:
                wait_for_enter("\n")
            if not self.direct and not self.manual:
                sleep(self.delay)
        print("\n\n\n")
