from dataclasses import dataclass
from enum import Enum
import math
from typing import Callable


try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False


class Command(str, Enum):
    QUIT = "quit"
    PAUSE = "pause"
    RESET = "reset"
    NEXT = "next"
    PREVIOUS = "previous"
    SKIP = "skip"


@dataclass
class GameLoop:
    end: float
    turns_per_second: float = 1.0
    now: float = 0.0
    paused: bool = False
    running: bool = True

    def handle(self, commands: list[Command]) -> None:
        for command in commands:
            if command == Command.QUIT:
                self.running = False
            elif command == Command.PAUSE:
                self.paused = not self.paused
            elif command == Command.RESET:
                self.now, self.paused = 0.0, True
            elif command == Command.NEXT:
                self.now = min(self.end, math.floor(self.now) + 1)
                self.paused = True
            elif command == Command.PREVIOUS:
                self.now = max(0.0, math.ceil(self.now) - 1)
                self.paused = True
            elif command == Command.SKIP:
                self.now = self.end
                self.paused = True

    def advance(self, dt: float) -> None:
        if not self.paused:
            self.now = min(self.end, self.now + dt * self.turns_per_second)


def key_commands() -> dict[int, Command]:
    return {
        pygame.K_ESCAPE: Command.QUIT,
        pygame.K_q: Command.QUIT,
        pygame.K_SPACE: Command.PAUSE,
        pygame.K_p: Command.PAUSE,
        pygame.K_LEFT: Command.PREVIOUS,
        pygame.K_w: Command.PREVIOUS,
        pygame.K_RIGHT: Command.NEXT,
        pygame.K_s: Command.NEXT,
        pygame.K_END: Command.SKIP,
        pygame.K_f: Command.SKIP,
        pygame.K_r: Command.RESET,
    }


def poll_events(
    keymap: dict[int, Command],
    click_command: Callable[[tuple[int, int]], Command | None] | None = None,
) -> list[Command]:
    """Translate keyboard (and optional mouse) input into commands.

    ``click_command`` receives the mouse position and returns the command
    for the HUD button under it (or ``None``). Keeping the hit test in the
    GUI keeps this module free of layout knowledge.
    """
    commands: list[Command] = []
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            commands.append(Command.QUIT)
        elif event.type == pygame.KEYDOWN:
            command = keymap.get(event.key)
            if command is not None:
                commands.append(command)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if click_command is not None:
                command = click_command(event.pos)
                if command is not None:
                    commands.append(command)
    return commands
