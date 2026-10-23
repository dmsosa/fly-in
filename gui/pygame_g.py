import pygame


class PygameG:
    def __init__(self):
        self.graph = graph
        self.history = history
        self.fps = FPS
    
    def draw_history(self) -> None:
        pygame.init()

        end_time = float(len(self.history))
        current_time = 0.0
        current_turn = 0
        max_turn = len(self.history)
        running = True
        paused = False
        while running:
            dt = pygame.tick(self.fps) / 1000.0
            if current_time < end_time:
                current_time = min(end_time, current_time + dt / self.turns_per_second)

            while current_turn < max_turn and current_time >= current_turn:
                self._update_anim_turn(current_turn)

            for anim in self.drone_anim:
                px, py = self._get_drone_pixels(anim)
            
            # I have a continuos amount of time  in seconds
            # and a discrete amount in turns
            # I want to map the amount of time in seconds to a turn
            # that is easy, but it depends on how turns per second 
            # do I want to have. For example, un second et egale
            # 1 turn, then if current_time = 2.44 then current_turn is
            # just the floor, the turn number 2.
            # current_turn = math.floor(current_time / turns_per_second)
            if paused:
                pygame.display.flip()
                continue

            

            pygame.display.flip()
        pygame.display.quit()

    def _get_drone_pixels(
            self,
            anim: DroneAnim,
            current_time: float
        ) -> pygame.Vector2:
        #progress, how near I am from the next turn?
        p = (current_time - anim.turn) / (anim.turn + 1 - anim.turn)
        
        return pygame.Vector2((px, py))