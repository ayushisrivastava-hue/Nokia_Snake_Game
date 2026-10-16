import cv2
import pygame
import numpy as np
import random
import math
import threading
import time
from snake_engine import DIFFICULTY_LEVELS, SnakeGame
from gesture_detector import GestureController

# Layout Dimensions
GAME_WIDTH, GAME_HEIGHT = 800, 600
CAM_PANEL_WIDTH = 480
TOTAL_WIDTH = GAME_WIDTH + CAM_PANEL_WIDTH
TOTAL_HEIGHT = GAME_HEIGHT

# Fixed galaxy starfield background (with phase for twinkling)
random.seed(42)
STARS = [
    (random.randint(0, TOTAL_WIDTH), random.randint(0, TOTAL_HEIGHT),
     random.randint(1, 3), random.uniform(0, 2 * math.pi))
    for _ in range(120)
]

# Floating White Space Character Sprites for Front Pages
CHARACTERS = [
    {"x": 120, "y": 120, "vx": 0.8, "vy": 0.5, "phase": 0.0},
    {"x": 1050, "y": 180, "vx": -0.6, "vy": 0.7, "phase": 1.5},
    {"x": 200, "y": 480, "vx": 0.7, "vy": -0.4, "phase": 3.0},
    {"x": 980, "y": 460, "vx": -0.5, "vy": -0.6, "phase": 4.5}
]


class CameraGestureWorker(threading.Thread):
    def __init__(self, width, height, initial_direction):
        super().__init__(daemon=True)
        self.width = width
        self.height = height
        self.direction = initial_direction
        self.frame = None
        self.action = None
        self.status = "Starting camera..."
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._direction_version = 0

    def set_direction(self, direction):
        with self._lock:
            self.direction = direction
            self._direction_version += 1

    def run(self):
        cap = None
        controller = None
        try:
            cap = cv2.VideoCapture(0)
            controller = GestureController(width=self.width, height=self.height)
            if not cap.isOpened():
                with self._lock:
                    self.status = "Camera unavailable - use arrows/buttons"
                return

            with self._lock:
                self.status = (
                    "Gesture control active"
                    if controller.detector is not None
                    else "Hand tracking unavailable - use arrows/buttons"
                )

            while not self._stop_event.is_set():
                started_at = time.monotonic()
                ret, frame = cap.read()
                if not ret:
                    with self._lock:
                        self.status = "Camera unavailable - use arrows/buttons"
                        self.frame = None
                    break

                frame = cv2.flip(frame, 1)
                with self._lock:
                    direction = self.direction
                    direction_version = self._direction_version
                direction, action, processed_frame = controller.get_direction_and_action(frame, direction)
                with self._lock:
                    if direction_version == self._direction_version:
                        self.direction = direction
                    self.frame = processed_frame
                    self.action = action

                self._stop_event.wait(max(0.0, 1 / 30 - (time.monotonic() - started_at)))
        finally:
            if cap is not None:
                cap.release()
            if controller is not None:
                controller.close()

    def get_state(self):
        with self._lock:
            action = self.action
            self.action = None
            return self.direction, action, self.frame, self.status

    def close(self):
        self._stop_event.set()
        if self.is_alive():
            self.join(timeout=2)


# ──────────────────────────────────────────────────────────────────
#  Drawing Helpers
# ──────────────────────────────────────────────────────────────────

def draw_galaxy_background(screen, frame_count):
    """Deep space background with twinkling stars."""
    screen.fill((10, 10, 26))
    for sx, sy, size, phase in STARS:
        b = 0.5 + 0.5 * math.sin(frame_count * 0.02 + phase)
        if size > 1:
            color = (int(200 * b), int(220 * b), int(255 * b))
        else:
            color = (int(100 * b), int(120 * b), int(180 * b))
        pygame.draw.circle(screen, color, (sx, sy), size)


def draw_scanlines(screen, alpha=15):
    """Retro CRT scanline overlay effect."""
    sl = pygame.Surface((TOTAL_WIDTH, TOTAL_HEIGHT), pygame.SRCALPHA)
    for y in range(0, TOTAL_HEIGHT, 3):
        pygame.draw.line(sl, (0, 0, 0, alpha), (0, y), (TOTAL_WIDTH, y))
    screen.blit(sl, (0, 0))


def draw_fade_overlay(screen, alpha):
    """Black fade overlay for state transitions."""
    if alpha > 0:
        f = pygame.Surface((TOTAL_WIDTH, TOTAL_HEIGHT), pygame.SRCALPHA)
        f.fill((10, 10, 26, min(int(alpha), 255)))
        screen.blit(f, (0, 0))


def draw_pulsing_text(screen, text, font, center_x, y, base_color, frame_count, speed=0.04):
    """Renders text with a pulsing brightness glow."""
    p = 0.7 + 0.3 * math.sin(frame_count * speed)
    color = (int(base_color[0] * p), int(base_color[1] * p), int(base_color[2] * p))
    shadow_color = (color[0] // 4, color[1] // 4, color[2] // 4)

    shadow = font.render(text, True, shadow_color)
    screen.blit(shadow, (center_x - shadow.get_width() // 2 + 3, y + 3))

    surf = font.render(text, True, color)
    screen.blit(surf, (center_x - surf.get_width() // 2, y))

    # Subtle glow rect behind text
    ga = int(25 + 15 * math.sin(frame_count * speed))
    gs = pygame.Surface((surf.get_width() + 20, surf.get_height() + 10), pygame.SRCALPHA)
    pygame.draw.rect(gs, (*base_color, ga), gs.get_rect(), border_radius=8)
    screen.blit(gs, (center_x - surf.get_width() // 2 - 10, y - 5))


def draw_navigation_button(screen, rect, label):
    hover = rect.collidepoint(pygame.mouse.get_pos())
    bg = (60, 20, 40) if hover else (15, 20, 40)
    border = (255, 0, 128) if hover else (80, 100, 140)
    pygame.draw.rect(screen, bg, rect, border_radius=10)
    pygame.draw.rect(screen, border, rect, width=2, border_radius=10)
    font = pygame.font.SysFont("trebuchet ms", 18, bold=True)
    text = font.render(label, True, (255, 255, 255) if hover else (180, 200, 230))
    screen.blit(text, (rect.centerx - text.get_width() // 2,
                       rect.centery - text.get_height() // 2))


def update_and_draw_floating_characters(screen, frame_count):
    """Animates floating white alien/snake characters across the galaxy pages."""
    for char in CHARACTERS:
        char["x"] += char["vx"] * 0.2
        char["y"] += char["vy"] * 0.2

        if char["x"] < 50 or char["x"] > TOTAL_WIDTH - 50:
            char["vx"] *= -1
        if char["y"] < 50 or char["y"] > TOTAL_HEIGHT - 50:
            char["vy"] *= -1

        bob = math.sin(frame_count * 0.02 + char["phase"]) * 4
        cx, cy = int(char["x"]), int(char["y"] + bob)

        pygame.draw.circle(screen, (255, 255, 255), (cx, cy), 14)
        pygame.draw.circle(screen, (0, 230, 255), (cx - 4, cy - 3), 3)
        pygame.draw.circle(screen, (0, 230, 255), (cx + 4, cy - 3), 3)
        pygame.draw.rect(screen, (255, 255, 255), (cx - 10, cy + 8, 20, 5), border_radius=2)


def draw_header_character(screen, cx, cy, frame_count):
    """Draws white mascot character at the top of the Rules page."""
    bob = math.sin(frame_count * 0.05) * 5
    cy = int(cy + bob)

    pygame.draw.circle(screen, (255, 255, 255), (cx, cy), 22)
    pygame.draw.circle(screen, (230, 230, 250), (cx - 30, cy + 10), 14)
    pygame.draw.circle(screen, (200, 200, 240), (cx - 55, cy + 18), 10)

    pygame.draw.circle(screen, (10, 10, 26), (cx - 6, cy - 4), 4)
    pygame.draw.circle(screen, (10, 10, 26), (cx + 8, cy - 4), 4)
    pygame.draw.circle(screen, (0, 230, 255), (cx - 5, cy - 5), 1)
    pygame.draw.circle(screen, (0, 230, 255), (cx + 9, cy - 5), 1)

    pygame.draw.line(screen, (255, 0, 128), (cx + 18, cy + 2), (cx + 28, cy + 2), 2)


def draw_virtual_buttons(screen, base_x, base_y, btn_size=50):
    """Clickable virtual arrow buttons. Returns {direction: Rect}."""
    gap = 4
    fsz = max(14, btn_size - 16)
    font = pygame.font.SysFont("trebuchet ms", fsz, bold=True)
    mpos = pygame.mouse.get_pos()

    btns = {}
    layout = [
        ("UP",    "\u25B2", base_x + btn_size + gap, base_y),
        ("LEFT",  "\u25C0", base_x, base_y + btn_size + gap),
        ("DOWN",  "\u25BC", base_x + btn_size + gap, base_y + btn_size + gap),
        ("RIGHT", "\u25B6", base_x + (btn_size + gap) * 2, base_y + btn_size + gap),
    ]

    for direction, symbol, bx, by in layout:
        rect = pygame.Rect(bx, by, btn_size, btn_size)
        btns[direction] = rect
        hover = rect.collidepoint(mpos)

        if hover:
            gs = pygame.Surface((btn_size + 6, btn_size + 6), pygame.SRCALPHA)
            pygame.draw.rect(gs, (0, 230, 255, 30), gs.get_rect(), border_radius=10)
            screen.blit(gs, (bx - 3, by - 3))

        bg = (40, 60, 100) if hover else (20, 28, 50)
        bc = (0, 230, 255) if hover else (50, 70, 110)
        pygame.draw.rect(screen, bg, rect, border_radius=8)
        pygame.draw.rect(screen, bc, rect, width=2, border_radius=8)

        tc = (0, 230, 255) if hover else (120, 150, 200)
        ts = font.render(symbol, True, tc)
        screen.blit(ts, (rect.centerx - ts.get_width() // 2,
                         rect.centery - ts.get_height() // 2))

    return btns


# ──────────────────────────────────────────────────────────────────
#  Screen Renderers
# ──────────────────────────────────────────────────────────────────

def draw_window_0_menu(screen, menu_items, selected_index, frame_count):
    """State 0: Main Menu."""
    draw_galaxy_background(screen, frame_count)
    update_and_draw_floating_characters(screen, frame_count)

    # Animated border
    bw = int(3 + 1.5 * math.sin(frame_count * 0.03))
    pygame.draw.rect(screen, (0, 230, 255),
                     (40, 40, TOTAL_WIDTH - 80, TOTAL_HEIGHT - 80), bw, border_radius=18)

    font_title = pygame.font.SysFont("trebuchet ms", 62, bold=True)
    font_sub = pygame.font.SysFont("trebuchet ms", 22, bold=True)
    font_menu = pygame.font.SysFont("trebuchet ms", 28, bold=True)
    font_hint = pygame.font.SysFont("trebuchet ms", 16)

    draw_pulsing_text(screen, "NOKIA SNAKE", font_title,
                      TOTAL_WIDTH // 2, 100, (0, 230, 255), frame_count, 0.03)

    sub = font_sub.render("GALAXY GESTURE EDITION", True, (255, 0, 128))
    screen.blit(sub, (TOTAL_WIDTH // 2 - sub.get_width() // 2, 175))

    # Decorative animated line
    lw = int(200 + 30 * math.sin(frame_count * 0.015))
    pygame.draw.line(screen, (0, 180, 220),
                     (TOTAL_WIDTH // 2 - lw, 210), (TOTAL_WIDTH // 2 + lw, 210), 2)

    # Menu items
    mpos = pygame.mouse.get_pos()
    rects = []
    for i, (label, icon) in enumerate(menu_items):
        r = pygame.Rect(TOTAL_WIDTH // 2 - 180, 260 + i * 80, 360, 60)
        rects.append(r)

        hovered = r.collidepoint(mpos)
        selected = (i == selected_index)
        active = selected or hovered

        if active:
            gs = pygame.Surface((r.width + 10, r.height + 10), pygame.SRCALPHA)
            ga = int(40 + 20 * math.sin(frame_count * 0.05))
            pygame.draw.rect(gs, (0, 230, 255, ga), gs.get_rect(), border_radius=14)
            screen.blit(gs, (r.x - 5, r.y - 5))

            pygame.draw.rect(screen, (25, 35, 70), r, border_radius=12)
            pygame.draw.rect(screen, (0, 230, 255), r, width=3, border_radius=12)
            tc = (255, 255, 255)

            # Arrow indicator
            iy = r.centery
            pygame.draw.polygon(screen, (0, 230, 255),
                                [(r.x - 20, iy), (r.x - 8, iy - 8), (r.x - 8, iy + 8)])
        else:
            pygame.draw.rect(screen, (15, 20, 40), r, border_radius=12)
            pygame.draw.rect(screen, (40, 60, 100), r, width=1, border_radius=12)
            tc = (150, 180, 220)

        txt = font_menu.render(f"{icon}  {label}", True, tc)
        screen.blit(txt, (r.centerx - txt.get_width() // 2,
                          r.centery - txt.get_height() // 2))

    hint = font_hint.render(
        "Use  \u2191 \u2193  +  ENTER  or  Click  to select   |   ESC to return",
        True, (100, 120, 160))
    screen.blit(hint, (TOTAL_WIDTH // 2 - hint.get_width() // 2, 540))

    draw_scanlines(screen, 12)
    return rects


def draw_window_1_start(screen, btn_rect, level_btns, selected_level,
                        back_btn_rect, frame_count):
    """Stage 1: Nokia Snake Game Title Window (No Camera)."""
    draw_galaxy_background(screen, frame_count)
    update_and_draw_floating_characters(screen, frame_count)

    bw = int(3 + math.sin(frame_count * 0.035))
    pygame.draw.rect(screen, (0, 230, 255),
                     (40, 40, TOTAL_WIDTH - 80, TOTAL_HEIGHT - 80), bw, border_radius=18)
    pygame.draw.rect(screen, (255, 0, 128),
                     (50, 50, TOTAL_WIDTH - 100, TOTAL_HEIGHT - 100), 1, border_radius=14)

    font_title = pygame.font.SysFont("trebuchet ms", 58, bold=True)
    font_sub = pygame.font.SysFont("trebuchet ms", 24, bold=True)
    font_btn = pygame.font.SysFont("trebuchet ms", 22, bold=True)

    # Pulsing title
    draw_pulsing_text(screen, "NOKIA SNAKE GAME", font_title,
                      TOTAL_WIDTH // 2, 160, (0, 230, 255), frame_count)

    # Subtitle with pulse
    sp = 0.7 + 0.3 * math.sin(frame_count * 0.03 + 1)
    sub_surf = font_sub.render("GALAXY GESTURE EDITION", True,
                               (int(255 * sp), 0, int(128 * sp)))
    screen.blit(sub_surf, (TOTAL_WIDTH // 2 - sub_surf.get_width() // 2, 235))

    # Animated decorative line
    lp = (math.sin(frame_count * 0.015) + 1) / 2
    ll = int(100 + 150 * lp)
    cx = TOTAL_WIDTH // 2
    pygame.draw.line(screen, (0, 180, 220), (cx - ll, 275), (cx + ll, 275), 2)

    level_font = pygame.font.SysFont("trebuchet ms", 18, bold=True)
    level_title = level_font.render("CHOOSE YOUR SPEED", True, (180, 200, 230))
    screen.blit(level_title, (TOTAL_WIDTH // 2 - level_title.get_width() // 2, 300))

    mpos = pygame.mouse.get_pos()
    for level, rect in level_btns.items():
        selected = level == selected_level
        hover = rect.collidepoint(mpos)
        bg = (0, 180, 220) if selected else ((35, 45, 75) if hover else (15, 25, 55))
        border = (0, 230, 255) if selected or hover else (65, 90, 130)
        pygame.draw.rect(screen, bg, rect, border_radius=12)
        pygame.draw.rect(screen, border, rect, width=2, border_radius=12)
        label = level_font.render(level.upper(), True,
                                  (10, 15, 30) if selected else (210, 225, 245))
        screen.blit(label, (rect.centerx - label.get_width() // 2,
                            rect.centery - label.get_height() // 2))

    # Begin button with hover glow
    hover = btn_rect.collidepoint(mpos)
    bg = (255, 0, 128) if hover else (15, 25, 55)
    bc = (0, 230, 255) if hover else (0, 180, 220)

    if hover:
        gs = pygame.Surface((btn_rect.width + 10, btn_rect.height + 10), pygame.SRCALPHA)
        pygame.draw.rect(gs, (255, 0, 128, 40), gs.get_rect(), border_radius=18)
        screen.blit(gs, (btn_rect.x - 5, btn_rect.y - 5))

    pygame.draw.rect(screen, bg, btn_rect, border_radius=16)
    pygame.draw.rect(screen, bc, btn_rect, width=3, border_radius=16)

    txt = font_btn.render("BEGIN GAME \u25B6", True,
                          (255, 255, 255) if hover else (0, 230, 255))
    screen.blit(txt, (btn_rect.centerx - txt.get_width() // 2,
                      btn_rect.centery - txt.get_height() // 2))

    hint = level_font.render(
        "Choose a speed, then click BEGIN GAME or press SPACE",
        True, (150, 170, 200))
    screen.blit(hint, (TOTAL_WIDTH // 2 - hint.get_width() // 2, 485))

    draw_navigation_button(screen, back_btn_rect, "BACK TO MENU")
    draw_scanlines(screen, 12)


def draw_window_2_rules(screen, btn_rect, frame_count, enter_frame, back_btn_rect=None):
    """Stage 2: Rules Display Window with slide-in cards."""
    draw_galaxy_background(screen, frame_count)
    update_and_draw_floating_characters(screen, frame_count)

    bw = int(3 + math.sin(frame_count * 0.03))
    pygame.draw.rect(screen, (0, 230, 255),
                     (40, 40, TOTAL_WIDTH - 80, TOTAL_HEIGHT - 80), bw, border_radius=18)

    draw_header_character(screen, TOTAL_WIDTH // 2, 85, frame_count)

    font_title = pygame.font.SysFont("trebuchet ms", 34, bold=True)
    font_rule = pygame.font.SysFont("trebuchet ms", 20, bold=True)
    font_btn = pygame.font.SysFont("trebuchet ms", 22, bold=True)

    title = font_title.render("GAME RULES & GESTURES", True, (255, 0, 128))
    screen.blit(title, (TOTAL_WIDTH // 2 - title.get_width() // 2, 130))

    rules = [
        "1. POINT INDEX FINGER to control snake direction (UP, DOWN, LEFT, RIGHT).",
        "2. SHOW PEACE SIGN (\u270C\uFE0F) when Game Over occurs to RESTART the game.",
        "3. USE KEYBOARD ARROWS or ON-SCREEN BUTTONS as alternate controls.",
        "4. CLOSE WINDOW OR PRESS 'X' to exit the game anytime."
    ]

    elapsed = frame_count - enter_frame

    for i, rule in enumerate(rules):
        delay = i * 8
        progress = min(max((elapsed - delay) / 20.0, 0.0), 1.0)
        progress = 1 - (1 - progress) ** 3  # ease-out

        ox = int((1 - progress) * -400)
        ca = int(255 * progress)

        cr = pygame.Rect(80 + ox, 180 + i * 62, TOTAL_WIDTH - 160, 50)

        cs = pygame.Surface((cr.width, cr.height), pygame.SRCALPHA)
        pygame.draw.rect(cs, (20, 25, 50, ca), cs.get_rect(), border_radius=10)
        border_glow = int(150 + 70 * math.sin(frame_count * 0.04 + i * 0.5))
        pygame.draw.rect(cs, (0, border_glow, 220, ca), cs.get_rect(),
                         width=1, border_radius=10)
        screen.blit(cs, cr.topleft)

        if progress > 0.3:
            ra = min(int(255 * ((progress - 0.3) / 0.7)), 255)
            rs = font_rule.render(rule, True, (220, 235, 255))
            rs.set_alpha(ra)
            screen.blit(rs, (cr.x + 20, cr.centery - rs.get_height() // 2))

    # Begin game button
    mpos = pygame.mouse.get_pos()
    hover = btn_rect.collidepoint(mpos)
    bg = (0, 230, 255) if hover else (15, 25, 55)
    bc = (255, 0, 128) if hover else (0, 180, 220)

    if hover:
        gs = pygame.Surface((btn_rect.width + 10, btn_rect.height + 10), pygame.SRCALPHA)
        pygame.draw.rect(gs, (0, 230, 255, 40), gs.get_rect(), border_radius=18)
        screen.blit(gs, (btn_rect.x - 5, btn_rect.y - 5))

    pygame.draw.rect(screen, bg, btn_rect, border_radius=16)
    pygame.draw.rect(screen, bc, btn_rect, width=3, border_radius=16)
    txt = font_btn.render("\u25B6 BEGIN GAME", True,
                          (10, 10, 26) if hover else (0, 230, 255))
    screen.blit(txt, (btn_rect.centerx - txt.get_width() // 2,
                      btn_rect.centery - txt.get_height() // 2))

    # Back to menu button
    if back_btn_rect is not None:
        draw_navigation_button(screen, back_btn_rect, "\u25C0 BACK TO MENU")

    hint = font_rule.render("Click button or Press SPACEBAR to start", True, (150, 170, 200))
    screen.blit(hint, (TOTAL_WIDTH // 2 - hint.get_width() // 2, 535))

    draw_scanlines(screen, 12)


def draw_window_4_about(screen, back_btn_rect, frame_count):
    """State 4: About Screen."""
    draw_galaxy_background(screen, frame_count)
    update_and_draw_floating_characters(screen, frame_count)

    pygame.draw.rect(screen, (0, 230, 255),
                     (40, 40, TOTAL_WIDTH - 80, TOTAL_HEIGHT - 80), 3, border_radius=18)

    font_title = pygame.font.SysFont("trebuchet ms", 38, bold=True)
    font_body = pygame.font.SysFont("trebuchet ms", 20, bold=True)
    font_btn = pygame.font.SysFont("trebuchet ms", 22, bold=True)
    font_ver = pygame.font.SysFont("trebuchet ms", 16)

    draw_pulsing_text(screen, "ABOUT", font_title,
                      TOTAL_WIDTH // 2, 80, (255, 0, 128), frame_count, 0.07)

    lines = [
        ("Nokia Snake Game \u2014 Galaxy Gesture Edition", (0, 230, 255)),
        ("", None),
        ("A modern reimagination of the classic Nokia Snake,", (200, 215, 240)),
        ("featuring hand gesture controls via webcam.", (200, 215, 240)),
        ("", None),
        ("CONTROLS:", (255, 0, 128)),
        ("  \u2022 Point your index finger to steer the snake", (180, 200, 230)),
        ("  \u2022 Show peace sign to restart after game over", (180, 200, 230)),
        ("  \u2022 Keyboard arrows & on-screen buttons also work", (180, 200, 230)),
        ("", None),
        ("BUILT WITH:", (255, 0, 128)),
        ("  Pygame  \u2022  OpenCV  \u2022  MediaPipe", (0, 200, 220)),
    ]

    for i, (line, color) in enumerate(lines):
        if line and color:
            s = font_body.render(line, True, color)
            screen.blit(s, (TOTAL_WIDTH // 2 - s.get_width() // 2, 140 + i * 30))

    # Back button
    mpos = pygame.mouse.get_pos()
    hover = back_btn_rect.collidepoint(mpos)
    bg = (60, 20, 40) if hover else (15, 20, 40)
    pygame.draw.rect(screen, bg, back_btn_rect, border_radius=12)
    bc = (255, 0, 128) if hover else (80, 60, 100)
    pygame.draw.rect(screen, bc, back_btn_rect, width=2, border_radius=12)
    bt = font_btn.render("\u25C0 BACK TO MENU", True,
                         (255, 255, 255) if hover else (180, 150, 200))
    screen.blit(bt, (back_btn_rect.centerx - bt.get_width() // 2,
                     back_btn_rect.centery - bt.get_height() // 2))

    ver = font_ver.render("v2.0 \u2014 Galaxy Gesture Edition", True, (80, 100, 140))
    screen.blit(ver, (TOTAL_WIDTH // 2 - ver.get_width() // 2, 555))

    draw_scanlines(screen, 12)


# ──────────────────────────────────────────────────────────────────
#  Main Loop
# ──────────────────────────────────────────────────────────────────

def main():
    pygame.init()
    camera_worker = None
    try:
        screen = pygame.display.set_mode((TOTAL_WIDTH, TOTAL_HEIGHT))
        pygame.display.set_caption("Nokia Snake Game - Galaxy Gesture Edition")
        clock = pygame.time.Clock()

        game = SnakeGame(GAME_WIDTH, GAME_HEIGHT, grid_size=20)
        game.sounds.play_startup()
        camera_status = "Camera starts when the game begins"
        current_direction = "RIGHT"
        selected_level = "Intermediate"

        # State: 0=Menu, 1=Title, 2=Rules, 3=Game, 4=About
        game_state = 0
        prev_state = -1

        # Menu
        menu_items = [
            ("PLAY GAME", "\u25B6"),
            ("HOW TO PLAY", "\U0001F4D6"),
            ("ABOUT", "\u2139"),
        ]
        menu_selected = 0
        menu_rects = []

        # Buttons
        start_btn_1 = pygame.Rect(TOTAL_WIDTH // 2 - 140, 410, 280, 55)
        title_back_btn = pygame.Rect(60, 60, 200, 44)
        level_btn_width = 170
        level_btn_gap = 18
        level_btn_total_width = (
            level_btn_width * len(DIFFICULTY_LEVELS)
            + level_btn_gap * (len(DIFFICULTY_LEVELS) - 1)
        )
        level_btn_left = (TOTAL_WIDTH - level_btn_total_width) // 2
        level_btns = {
            level: pygame.Rect(
                level_btn_left + index * (level_btn_width + level_btn_gap),
                330, level_btn_width, 48,
            )
            for index, level in enumerate(DIFFICULTY_LEVELS)
        }
        start_btn_2 = pygame.Rect(TOTAL_WIDTH // 2 - 130, 435, 260, 48)
        back_btn = pygame.Rect(TOTAL_WIDTH // 2 - 130, 490, 260, 40)
        about_back_btn = pygame.Rect(TOTAL_WIDTH // 2 - 130, 500, 260, 45)
        game_back_btn = pygame.Rect(
            GAME_WIDTH + CAM_PANEL_WIDTH - 166, 535, 150, 36
        )

        virtual_btns = {}

        def begin_game():
            nonlocal current_direction, game_state
            game.reset()
            current_direction = "RIGHT"
            game.sounds.play_startup()
            if camera_worker is not None:
                camera_worker.set_direction(current_direction)
            game_state = 3

        def return_to_levels():
            nonlocal camera_worker, current_direction, game_state
            if camera_worker is not None:
                camera_worker.close()
                camera_worker = None
            current_direction = "RIGHT"
            game_state = 1

        frame_count = 0
        rules_enter_frame = 0
        fade_alpha = 255
        fade_speed = 12

        running = True

        while running:
            frame_count += 1

            # Transition on state change
            if game_state != prev_state:
                fade_alpha = 180
                if game_state == 2:
                    rules_enter_frame = frame_count
                prev_state = game_state

            if fade_alpha > 0:
                fade_alpha = max(fade_alpha - fade_speed, 0)

            # Sync menu selection with mouse hover
            if game_state == 0 and menu_rects:
                mpos = pygame.mouse.get_pos()
                for i, r in enumerate(menu_rects):
                    if r.collidepoint(mpos):
                        menu_selected = i

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if game_state == 0:
                        for i, r in enumerate(menu_rects):
                            if r.collidepoint(event.pos):
                                game.sounds.play_click()
                                if i == 0:
                                    game_state = 1
                                elif i == 1:
                                    game_state = 2
                                elif i == 2:
                                    game_state = 4
                    elif game_state == 1:
                        for level, rect in level_btns.items():
                            if rect.collidepoint(event.pos):
                                game.sounds.play_click()
                                selected_level = level
                                game.set_difficulty(level)
                                break
                        else:
                            if start_btn_1.collidepoint(event.pos):
                                game.sounds.play_click()
                                game.set_difficulty(selected_level)
                                begin_game()
                            elif title_back_btn.collidepoint(event.pos):
                                game.sounds.play_click()
                                game_state = 0
                    elif game_state == 2:
                        if back_btn.collidepoint(event.pos):
                            game.sounds.play_click()
                            game_state = 0
                        elif start_btn_2.collidepoint(event.pos):
                            game.sounds.play_click()
                            game.set_difficulty(selected_level)
                            begin_game()
                    elif game_state == 3:
                        if game_back_btn.collidepoint(event.pos):
                            game.sounds.play_click()
                            return_to_levels()
                        else:
                            for d, r in virtual_btns.items():
                                if r.collidepoint(event.pos):
                                    game.sounds.play_click()
                                    current_direction = d
                                    if camera_worker is not None:
                                        camera_worker.set_direction(d)
                    elif game_state == 4 and about_back_btn.collidepoint(event.pos):
                        game.sounds.play_click()
                        game_state = 0

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_x:
                        running = False
                    elif event.key == pygame.K_ESCAPE:
                        if game_state == 3:
                            return_to_levels()
                        elif game_state in (1, 2, 4):
                            game_state = 0

                    # Menu navigation
                    elif game_state == 0:
                        if event.key == pygame.K_UP:
                            menu_selected = (menu_selected - 1) % len(menu_items)
                        elif event.key == pygame.K_DOWN:
                            menu_selected = (menu_selected + 1) % len(menu_items)
                        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            game.sounds.play_click()
                            if menu_selected == 0:
                                game_state = 1
                            elif menu_selected == 1:
                                game_state = 2
                            elif menu_selected == 2:
                                game_state = 4

                    elif game_state == 1 and event.key in (
                            pygame.K_LEFT, pygame.K_RIGHT):
                        levels = list(DIFFICULTY_LEVELS)
                        level_index = levels.index(selected_level)
                        step = 1 if event.key == pygame.K_RIGHT else -1
                        selected_level = levels[(level_index + step) % len(levels)]
                        game.set_difficulty(selected_level)
                        game.sounds.play_click()

                    elif event.key == pygame.K_SPACE:
                        if game_state == 1:
                            game.sounds.play_click()
                            game.set_difficulty(selected_level)
                            begin_game()
                        elif game_state == 2:
                            game.sounds.play_click()
                            game.set_difficulty(selected_level)
                            begin_game()

                    # Game controls
                    elif game_state == 3:
                        if event.key == pygame.K_UP:
                            current_direction = "UP"
                        elif event.key == pygame.K_DOWN:
                            current_direction = "DOWN"
                        elif event.key == pygame.K_LEFT:
                            current_direction = "LEFT"
                        elif event.key == pygame.K_RIGHT:
                            current_direction = "RIGHT"
                        elif event.key == pygame.K_r and game.game_over:
                            game.reset()
                            current_direction = "RIGHT"
                            if camera_worker is not None:
                                camera_worker.set_direction(current_direction)
                        if event.key in (
                                pygame.K_UP, pygame.K_DOWN,
                                pygame.K_LEFT, pygame.K_RIGHT,
                                pygame.K_r):
                            game.sounds.play_click()
                        if camera_worker is not None and event.key in (
                                pygame.K_UP, pygame.K_DOWN,
                                pygame.K_LEFT, pygame.K_RIGHT,
                                pygame.K_r):
                            camera_worker.set_direction(current_direction)

            # ── Render current state ──────────────────────────────

            if game_state == 0:
                menu_rects = draw_window_0_menu(
                    screen, menu_items, menu_selected, frame_count)

            elif game_state == 1:
                draw_window_1_start(
                    screen, start_btn_1, level_btns, selected_level,
                    title_back_btn, frame_count)

            elif game_state == 2:
                draw_window_2_rules(
                    screen, start_btn_2, frame_count, rules_enter_frame,
                    back_btn_rect=back_btn)

            elif game_state == 4:
                draw_window_4_about(screen, about_back_btn, frame_count)

            elif game_state == 3:
                # Camera worker
                if camera_worker is None:
                    camera_worker = CameraGestureWorker(
                        width=CAM_PANEL_WIDTH, height=360,
                        initial_direction=current_direction,
                    )
                    camera_worker.start()

                gesture_dir, action, processed_frame, camera_status = \
                    camera_worker.get_state()
                current_direction = gesture_dir
                if action == "RESTART" and game.game_over:
                    game.reset()
                    current_direction = "RIGHT"
                    camera_worker.set_direction(current_direction)

                game.update(current_direction)

                game_surface = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
                game.draw(game_surface)
                screen.fill((15, 15, 28))
                screen.blit(game_surface, (0, 0))

                # ── Side panel ────────────────────────────────────
                panel_rect = pygame.Rect(GAME_WIDTH, 0, CAM_PANEL_WIDTH, TOTAL_HEIGHT)
                pygame.draw.rect(screen, (20, 22, 35), panel_rect)
                pygame.draw.line(screen, (60, 70, 100),
                                 (GAME_WIDTH, 0), (GAME_WIDTH, TOTAL_HEIGHT), 2)

                font = pygame.font.SysFont("trebuchet ms", 18, bold=True)
                sfont = pygame.font.SysFont("trebuchet ms", 16, bold=True)

                no_camera = "unavailable" in camera_status.lower()

                if processed_frame is not None:
                    # ── Camera is working ─────────────────────────
                    frame_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                    frame_rgb = np.rot90(frame_rgb)
                    frame_rgb = np.flipud(frame_rgb)
                    cam_surface = pygame.surfarray.make_surface(frame_rgb)
                    screen.blit(cam_surface, (GAME_WIDTH, 10))

                    screen.blit(sfont.render(camera_status, True, (150, 170, 200)),
                                (GAME_WIDTH + 20, 375))
                    screen.blit(font.render(f"Snake: {game.direction}", True,
                                            (0, 230, 255)),
                                (GAME_WIDTH + 20, 395))
                    screen.blit(font.render(
                        f"Score: {game.score}  |  {game.difficulty}", True,
                                            (255, 255, 255)),
                                (GAME_WIDTH + 20, 418))
                    screen.blit(font.render("\u2022 Point Finger: Direction", True,
                                            (200, 220, 255)),
                                (GAME_WIDTH + 20, 442))
                    screen.blit(font.render("\u2022 Peace Sign: Restart", True,
                                            (180, 220, 180)),
                                (GAME_WIDTH + 20, 462))
                    screen.blit(font.render("\u2022 Arrows/Buttons: Alternate", True,
                                            (200, 200, 220)),
                                (GAME_WIDTH + 20, 482))

                    # Compact virtual buttons
                    btn_sz = 32
                    blw = btn_sz * 3 + 4 * 2
                    bx = GAME_WIDTH + (CAM_PANEL_WIDTH - blw) // 2
                    virtual_btns = draw_virtual_buttons(screen, bx, 508, btn_size=btn_sz)

                    if game.game_over:
                        ov = font.render("GAME OVER! Show \u270C\uFE0F or Press 'R'",
                                         True, (255, 0, 128))
                        screen.blit(ov, (GAME_WIDTH + 20, 578))

                elif no_camera:
                    # ── No camera – prominent buttons ─────────────
                    banner_font = pygame.font.SysFont("trebuchet ms", 26, bold=True)
                    sub_font = pygame.font.SysFont("trebuchet ms", 18)

                    bf = banner_font.render(
                        "\U0001F4F7  NO CAMERA DETECTED", True, (255, 80, 100))
                    screen.blit(bf, (GAME_WIDTH + CAM_PANEL_WIDTH // 2
                                     - bf.get_width() // 2, 30))

                    sf2 = sub_font.render(
                        "Use keyboard arrows or buttons below", True, (150, 170, 200))
                    screen.blit(sf2, (GAME_WIDTH + CAM_PANEL_WIDTH // 2
                                      - sf2.get_width() // 2, 65))

                    # Large virtual buttons
                    btn_sz = 55
                    blw = btn_sz * 3 + 4 * 2
                    bx = GAME_WIDTH + (CAM_PANEL_WIDTH - blw) // 2
                    virtual_btns = draw_virtual_buttons(screen, bx, 110,
                                                        btn_size=btn_sz)

                    yo = 250
                    screen.blit(sfont.render(camera_status, True, (150, 170, 200)),
                                (GAME_WIDTH + 20, yo))
                    screen.blit(font.render(f"Snake: {game.direction}", True,
                                            (0, 230, 255)),
                                (GAME_WIDTH + 20, yo + 30))
                    screen.blit(font.render(
                        f"Score: {game.score}  |  {game.difficulty}", True,
                                            (255, 255, 255)),
                                (GAME_WIDTH + 20, yo + 55))
                    screen.blit(font.render("\u2022 Arrow Keys: Change Direction", True,
                                            (200, 220, 255)),
                                (GAME_WIDTH + 20, yo + 90))
                    screen.blit(font.render("\u2022 Press 'R': Restart Game", True,
                                            (180, 220, 180)),
                                (GAME_WIDTH + 20, yo + 115))
                    screen.blit(font.render("\u2022 Click Buttons Above", True,
                                            (200, 200, 220)),
                                (GAME_WIDTH + 20, yo + 140))

                    if game.game_over:
                        ov = font.render("GAME OVER! Press 'R' to Restart",
                                         True, (255, 0, 128))
                        screen.blit(ov, (GAME_WIDTH + 20, yo + 175))

                else:
                    # ── Camera loading ────────────────────────────
                    loading_font = pygame.font.SysFont("trebuchet ms", 22, bold=True)
                    dots = "." * ((frame_count // 15) % 4)
                    lt = loading_font.render(f"Starting camera{dots}", True,
                                             (0, 230, 255))
                    screen.blit(lt, (GAME_WIDTH + CAM_PANEL_WIDTH // 2
                                     - lt.get_width() // 2, 180))

                    screen.blit(font.render(f"Snake: {game.direction}", True,
                                            (0, 230, 255)),
                                (GAME_WIDTH + 20, 400))
                    screen.blit(font.render(
                        f"Score: {game.score}  |  {game.difficulty}", True,
                                            (255, 255, 255)),
                                (GAME_WIDTH + 20, 425))

                    # Medium buttons while loading
                    btn_sz = 45
                    blw = btn_sz * 3 + 4 * 2
                    bx = GAME_WIDTH + (CAM_PANEL_WIDTH - blw) // 2
                    virtual_btns = draw_virtual_buttons(screen, bx, 470,
                                                        btn_size=btn_sz)

                draw_navigation_button(screen, game_back_btn, "BACK TO LEVELS")

            # Fade transition overlay
            draw_fade_overlay(screen, fade_alpha)

            pygame.display.flip()
            clock.tick(60)
    finally:
        if camera_worker is not None:
            camera_worker.close()
        pygame.quit()


if __name__ == "__main__":
    main()