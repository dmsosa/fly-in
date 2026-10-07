import sys
import time
from typing import TYPE_CHECKING, Optional

from .utils import clear_screen
from .constants import THEME_CHAR, THEME_COLOR
from .constants import MENU_WIDTH

if TYPE_CHECKING:
    from menu import Menu


def hex_to_ansi_fg(hex_color: str) -> str:
    """Convert '#rrggbb' to a 24-bit truecolor ANSI foreground escape."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"\033[38;2;{r};{g};{b}m"


def hex_to_ansi_bg(hex_color: str) -> str:
    """Convert '#rrggbb' to a 24-bit truecolor ANSI background escape."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"\033[48;2;{r};{g};{b}m"


class FlyinPrinter:
    def __init__(self):
        self.is_ansi: bool = False
        self.prettify: bool = False
        self.delay: float = 0.03

    def title(self) -> str:
        """Generates the ASCII title graphic for game screens.

        Returns:
            str: Centered multiline ASCII string.
        """
        ascii_art = r"""                                          
       ___  ___
     /'___\/\_ \                      __
    /\ \__/\//\ \    __  __          /\_\    ___
    \ \ ,__\ \ \ \  /\ \/\ \  _______\/\ \ /' _ `\
     \ \ \_/  \_\ \_\ \ \_\ \/\______\\ \ \/\ \/\ \
      \ \_\   /\____\\/`____ \/______/ \ \_\ \_\ \_\
       \/_/   \/____/ `/___/> \         \/_/\/_/\/_/
                         /\___/
                         \/__/                      """
        return ascii_art.center(100)

    # ── Helper: ANSI typing illusion ────────────────────────────────
    def _print_line(self, text: str) -> None:
        """Print *text* one character at a time (ANSI cursor tricks)."""
        print("\033[?25l", end="")  # hide cursor
        for ch in text:
            print(ch, end="", flush=True)
            time.sleep(self.delay)
        print("\033[?25h")  # show cursor again
        sys.stdout.write("\r")

    def _erase_line(self, s: str) -> None:
        sys.stdout.write("\r")
        for _ in s:
            sys.stdout.write(" ")
            sys.stdout.flush()
            time.sleep(self.delay)
        sys.stdout.write("\r")

    def print_wrap(self, msg: str) -> None:
        if self.prettify:
            self._print_line(msg)
        else:
            print(msg)

    def print_presentation(self) -> None:
        """Displays the interactive title graphic for program launch."""
        clear_screen()
        if self.is_ansi:
            accent = hex_to_ansi_fg(THEME_COLOR["primary"])
            reset = "\033[0m"
        else:
            accent = ""
            reset = ""
        print(f"{accent}{self.title()}{reset}", end="\n" * 3)
        self.wait_for_enter(None)


    def wait_for_enter(self, message: Optional[str]) -> None:
        """Halts execution until the user presses the 'Enter' key.

        Args:
            message (str, optional): Custom override string to display.
        """
        if message is None:
            message = "Press enter..."
        self.print_wrap(message)
        sys.stdin.readline()


    def print_goodbye(self) -> None:
        """Exits the application gracefully displaying parting graphics."""
        self.clear_screen()
        print("\n\n")
        if self.is_ansi:
            accent = hex_to_ansi_fg(THEME_COLOR["primary"])
            reset = "\033[0m"
        else:
            accent = ""
            reset = ""
        self.print_wrap(f"{accent}{self.title()}{reset}", end="\n" * 3)
        self.print_wrap("Thanks for using the fly-in project, :)", "\n")
        sys.exit(0)

    def print_lines(
            self,
            title: str,
            items: list[str],
            scale: int = 3
            ) -> None:
        if self.is_ansi:
            self._print_menu_ansi(title, items, scale)
        else:
            self._print_menu_ascii(title, items, scale)


    def _print_lines_ascii(
            self,
            title: str,
            items: list[str],
            scale: int = 3
            ) -> None:
        chars = [
                THEME_CHAR[0b0110],
                THEME_CHAR[0b1100],
                THEME_CHAR[0b0011],
                THEME_CHAR[0b1001],
                THEME_CHAR[0b1010],
                THEME_CHAR[0b0001],
            ]
        corner_ul = chars[0]
        corner_ur = chars[1]
        corner_bl = chars[2]
        corner_br = chars[3]
        hor_bar = chars[4] * scale
        ver_bar = chars[5]
        top_row = f"{corner_ul}" + hor_bar * MENU_WIDTH + f"{corner_ur}"
        bot_row = f"{corner_bl}" + hor_bar * MENU_WIDTH + f"{corner_br}"
        empty_row = ver_bar + " " * scale * MENU_WIDTH + ver_bar
        lines = [
                top_row,
                ver_bar + "{:^{w}}".format(title, w=MENU_WIDTH * scale) + ver_bar,
                empty_row
        ]
        for i in range(0, len(items)):
            item = items[i]
            lines.append(
                ver_bar + "{:<{w}}".format(item, w=MENU_WIDTH * scale) + ver_bar
            )
        lines.append(empty_row)
        lines.append(bot_row)
        print("\n".join(lines))


    def _print_lines_ansi(
        self,
            title: str,
            items: list[str],
            scale: int = 3
            ) -> None:
        chars = [
                THEME_CHAR[0b0110],
                THEME_CHAR[0b1100],
                THEME_CHAR[0b0011],
                THEME_CHAR[0b1001],
                THEME_CHAR[0b1010],
                THEME_CHAR[0b0001],
            ]
        corner_ul = chars[0]
        corner_ur = chars[1]
        corner_bl = chars[2]
        corner_br = chars[3]
        hor_bar = chars[4] * scale
        ver_bar = chars[5]
        accent = hex_to_ansi_fg(THEME_COLOR["primary"])
        highlight = hex_to_ansi_fg(THEME_COLOR["secondary"])
        reset = "\033[0m"
        top_row = (
            f"{accent}{corner_ul}"
            + hor_bar * MENU_WIDTH * scale
            + f"{corner_ur}{reset}"
        )

        bot_row = (
            f"{accent}{corner_bl}"
            + hor_bar * MENU_WIDTH * scale
            + f"{corner_br}{reset}"
        )
        accent_bar = accent + ver_bar + reset
        empty_row = accent_bar + " " * scale * MENU_WIDTH + accent_bar
        lines = [
            top_row,
            accent_bar + "{:^{w}}".format(
                title, w=MENU_WIDTH * scale) + accent_bar,
            empty_row
        ]
        for i in range(0, len(items)):
            item = items[i]
            line = accent_bar + highlight + "{:<{w}}".format(
                item, w=MENU_WIDTH * scale) + reset + accent_bar
            lines.append(line)
        lines.append(empty_row)
        lines.append(bot_row)
        print("\n".join(lines))


    def print_top_row(
            self,
            scale: int = 3
            ) -> None:
        chars = [
                THEME_CHAR[0b0110],
                THEME_CHAR[0b1100],
                THEME_CHAR[0b1010],
            ]
        corner_ul = chars[0]
        corner_ur = chars[1]
        hor_bar = chars[2]
        accent = hex_to_ansi_fg(THEME_COLOR["primary"])
        reset = "\033[0m"
        if self.is_ansi:
            top_row = (
                f"{accent}{corner_ul}" + hor_bar * MENU_WIDTH * scale +
                f"{corner_ur}{reset}"
                )
        else:
            top_row = (
                f"{corner_ul}" + hor_bar * MENU_WIDTH * scale +
                f"{corner_ur}"
                )
        print(top_row)

    def print_empty_row(
            self,
            scale: int = 3
            ) -> None:
        ver_bar = THEME_CHAR[0b0101]
        accent = hex_to_ansi_fg(THEME_COLOR["primary"])
        reset = "\033[0m"
        accent_bar = accent + ver_bar + reset
        if self.is_ansi:
            empty_row = accent_bar + " " * MENU_WIDTH * scale + accent_bar
        else:
            empty_row = ver_bar + " " * MENU_WIDTH * scale + ver_bar
        print(empty_row)

    def print_line_framed(
            self,
            text: str,
            scale: int = 3
            ) -> None:
        ver_bar = THEME_CHAR[0b0101]
        accent = hex_to_ansi_fg(THEME_COLOR["primary"])
        reset = "\033[0m"
        accent_bar = accent + ver_bar + reset
        if self.is_ansi:
            row = accent_bar + f"{text:<{MENU_WIDTH * scale }}" + accent_bar
        else:
            row = ver_bar + f"{text:<{MENU_WIDTH * scale }}" + ver_bar
        print(row)

    def print_bot_row(
            self,
            scale: int = 3
            ) -> None:
        chars = [
            THEME_CHAR[0b0011],
            THEME_CHAR[0b1001],
            THEME_CHAR[0b1010]
        ]
        corner_bl = chars[0]
        corner_br = chars[1]
        hor_bar = chars[2]
        accent = hex_to_ansi_fg(THEME_COLOR["primary"])
        reset = "\033[0m"
        if self.is_ansi:
            bot_row = (
                f"{accent}{corner_bl}" + hor_bar * MENU_WIDTH * scale +
                f"{corner_br}{reset}"
                )
        else:
            bot_row = (
                f"{corner_bl}" + hor_bar * MENU_WIDTH * scale +
                f"{corner_br}"
                )
        print(bot_row)

    # ---- menus ------------------------------------------------------
    def print_menu(
            self,
            menu: "Menu",
            mark: bool = True,
            scale: int = 3,
            frame: bool = False
            ) -> None:
        if self.is_ansi:
            self._print_menu_ansi(menu, mark, scale, frame)
        else:
            self._print_menu_ascii(menu, mark, scale, frame)


    def _print_menu_ascii(
            self,
            menu: "Menu",
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
            menu: "Menu",
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
