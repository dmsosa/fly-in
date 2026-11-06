from dataclasses import dataclass
from enum import Enum
import math


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
        pygame.K_r: Command.RESET,
    }


def poll_events(keymap: dict[int, Command]) -> list[Command]:
    commands: list[Command] = []
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            commands.append(Command.QUIT)
        elif event.type == pygame.KEYDOWN:
            command = keymap.get(event.key)
            if command is not None:
                commands.append(command)
    return commands
