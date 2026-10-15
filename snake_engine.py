import pygame
import random
from sound_effects import NokiaSoundManager


DIFFICULTY_LEVELS = {
    "Easy": 250,
    "Intermediate": 180,
    "Fast": 130,
}


class SnakeGame:
    def __init__(self, width=800, height=600, grid_size=20,
                 difficulty="Intermediate"):
        self.width = width
        self.height = height
        self.grid_size = grid_size
        self.sounds = NokiaSoundManager()
        self.set_difficulty(difficulty)
        self.last_move_time = pygame.time.get_ticks()

        # Galaxy background particle stars (with phase for twinkling)
        self.stars = [
            (random.randint(0, width), random.randint(0, height),
             random.choice([1, 2, 3]))
            for _ in range(70)
        ]

        # Animation frame counter
        self.frame_count = 0

        # Score popups: (x, y, life, text)
        self.score_popups = []

        self.reset()

    def set_difficulty(self, difficulty):
        if difficulty not in DIFFICULTY_LEVELS:
            raise ValueError(f"Unknown difficulty level: {difficulty}")
        self.difficulty = difficulty
        self.move_delay = DIFFICULTY_LEVELS[difficulty]

    def reset(self):
        self.snake = [(self.width // 2, self.height // 2)]
        self.direction = "RIGHT"
        self.pending_direction = self.direction
        self.score = 0
        self.game_over = False
        self.last_move_time = pygame.time.get_ticks()
        self.score_popups = []
        self._spawn_food()

    def _spawn_food(self):
        cols = self.width // self.grid_size
        rows = self.height // self.grid_size
        while True:
            fx = random.randint(0, cols - 1) * self.grid_size
            fy = random.randint(0, rows - 1) * self.grid_size
            if (fx, fy) not in self.snake:
                self.food = (fx, fy)
                break

    def update(self, new_direction):
        self.frame_count += 1

        # Float score popups upward and decay
        self.score_popups = [
            (x, y - 1, life - 1, t)
            for x, y, life, t in self.score_popups if life > 0
        ]

        if self.game_over:
            return

        # Buffer turns between movement ticks so brief inputs are not lost.
        opposites = {"UP": "DOWN", "DOWN": "UP", "LEFT": "RIGHT", "RIGHT": "LEFT"}
        if (new_direction in opposites
                and opposites[new_direction] != self.direction
                and opposites[new_direction] != self.pending_direction):
            self.pending_direction = new_direction

        # Throttle movement speed
        current_time = pygame.time.get_ticks()
        if current_time - self.last_move_time < self.move_delay:
            return

        self.last_move_time = current_time
        self.direction = self.pending_direction

        # Move head
        hx, hy = self.snake[0]
        if self.direction == "UP": hy -= self.grid_size
        elif self.direction == "DOWN": hy += self.grid_size
        elif self.direction == "LEFT": hx -= self.grid_size
        elif self.direction == "RIGHT": hx += self.grid_size

        new_head = (hx, hy)
        will_grow = new_head == self.food
        occupied_segments = self.snake if will_grow else self.snake[:-1]

        # Collision detection
        if (hx < 0 or hx >= self.width or hy < 0 or hy >= self.height or new_head in occupied_segments):
            self.game_over = True
            self.sounds.play_game_over()
            return

        self.snake.insert(0, new_head)

        # Eat food
        if will_grow:
            self.score += 10
            self.sounds.play_eat()
            # Score popup
            self.score_popups.append((self.food[0], self.food[1], 40, "+10"))
            self._spawn_food()
        else:
            self.snake.pop()

    def draw(self, surface):
        # Deep space galaxy background (Dark Charcoal/Space Blue)
        surface.fill((15, 15, 28))

        # Keep the background static to avoid distracting flicker.
        for x, y, size in self.stars:
            pygame.draw.circle(surface, (145, 155, 180), (x, y), size)

        # Draw Grid lines (Subtle cosmic grid)
        for x in range(0, self.width, self.grid_size):
            pygame.draw.line(surface, (25, 30, 50), (x, 0), (x, self.height))
        for y in range(0, self.height, self.grid_size):
            pygame.draw.line(surface, (25, 30, 50), (0, y), (self.width, y))

        # Draw food without a pulsing glow.
        fx, fy = self.food
        pygame.draw.rect(surface, (255, 0, 128),
                         (fx, fy, self.grid_size, self.grid_size), border_radius=6)
        pygame.draw.rect(surface, (255, 100, 180),
                         (fx + 3, fy + 3, self.grid_size - 6, self.grid_size - 6), border_radius=4)

        # Draw the snake on grid positions, moving only on each game tick.
        for i, (sx, sy) in enumerate(self.snake):
            if i == 0:
                color = (0, 230, 255)
            else:
                t = min(i / max(len(self.snake), 1), 1.0)
                color = (int(100 - 50 * t), int(180 - 60 * t), int(220 - 40 * t))
            pygame.draw.rect(surface, color,
                             (sx + 1, sy + 1, self.grid_size - 2, self.grid_size - 2),
                             border_radius=4)

        # Draw eyes on snake head
        if self.snake:
            hx, hy = self.snake[0]
            cx = hx + self.grid_size // 2
            cy = hy + self.grid_size // 2
            eye_map = {
                "RIGHT": [(4, -3), (4, 3), (5, -3), (5, 3)],
                "LEFT":  [(-4, -3), (-4, 3), (-5, -3), (-5, 3)],
                "UP":    [(-3, -4), (3, -4), (-3, -5), (3, -5)],
                "DOWN":  [(-3, 4), (3, 4), (-3, 5), (3, 5)],
            }
            offsets = eye_map.get(self.direction, eye_map["RIGHT"])
            pygame.draw.circle(surface, (255, 255, 255),
                               (cx + offsets[0][0], cy + offsets[0][1]), 3)
            pygame.draw.circle(surface, (255, 255, 255),
                               (cx + offsets[1][0], cy + offsets[1][1]), 3)
            pygame.draw.circle(surface, (10, 10, 26),
                               (cx + offsets[2][0], cy + offsets[2][1]), 1)
            pygame.draw.circle(surface, (10, 10, 26),
                               (cx + offsets[3][0], cy + offsets[3][1]), 1)

        # Draw score popups (float upward and fade)
        if self.score_popups:
            pf = pygame.font.SysFont("trebuchet ms", 18, bold=True)
            for px, py, life, text in self.score_popups:
                f = life / 40.0
                c = (int(255 * f), int(220 * f), int(100 * f))
                s = pf.render(text, True, c)
                surface.blit(s, (int(px), int(py)))

        # Game over overlay with pulsing text
        if self.game_over:
            ov = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 100))
            surface.blit(ov, (0, 0))

            gf = pygame.font.SysFont("trebuchet ms", 52, bold=True)
            sf = pygame.font.SysFont("trebuchet ms", 22, bold=True)

            go = gf.render("GAME OVER", True, (255, 0, 128))
            gs = gf.render("GAME OVER", True, (80, 0, 40))
            cx, cy = self.width // 2, self.height // 2
            surface.blit(gs, (cx - go.get_width() // 2 + 3,
                              cy - go.get_height() // 2 + 3))
            surface.blit(go, (cx - go.get_width() // 2,
                              cy - go.get_height() // 2))

            sc = sf.render(f"Final Score: {self.score}", True, (0, 230, 255))
            surface.blit(sc, (cx - sc.get_width() // 2, cy + 35))