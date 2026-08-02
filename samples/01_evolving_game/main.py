"""参加者のアイデアで進化させるネオン・ブロック崩し。"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

import pygame

from game_rules import bounce_from_paddle, next_ball_speed, score_for_brick

WIDTH, HEIGHT = 960, 640
PLAY_TOP = 92
BACKGROUND = (6, 9, 24)
CYAN = (55, 235, 255)
MAGENTA = (255, 70, 190)
YELLOW = (255, 220, 75)
WHITE = (235, 246, 255)
BRICK_COLORS = [(255, 70, 130), (255, 125, 75), (255, 210, 70), (70, 230, 180), (70, 170, 255), (170, 100, 255)]


@dataclass
class Ball:
    x: float
    y: float
    vx: float
    vy: float
    radius: int = 9

    @property
    def speed(self) -> float:
        return math.hypot(self.vx, self.vy)

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(
            int(self.x - self.radius),
            int(self.y - self.radius),
            self.radius * 2,
            self.radius * 2,
        )


@dataclass
class Brick:
    rect: pygame.Rect
    row: int
    color: tuple[int, int, int]


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    color: tuple[int, int, int]


class Game:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("EVOLVING GAME // AI Workshop")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 24, bold=True)
        self.small_font = pygame.font.SysFont("arial", 16)
        self.big_font = pygame.font.SysFont("arial", 58, bold=True)
        self.running = True
        self.state = "title"
        self.stars = [
            (random.randrange(WIDTH), random.randrange(HEIGHT), random.choice((1, 1, 1, 2)))
            for _ in range(110)
        ]
        self.reset()

    def reset(self) -> None:
        self.paddle = pygame.Rect(WIDTH // 2 - 72, HEIGHT - 55, 144, 16)
        self.ball = Ball(WIDTH / 2, HEIGHT - 80, 225, -330)
        self.bricks = self._make_bricks()
        self.particles: list[Particle] = []
        self.score = 0
        self.lives = 3
        self.combo = 0
        self.broken_bricks = 0

    @staticmethod
    def _make_bricks() -> list[Brick]:
        bricks: list[Brick] = []
        columns, rows = 11, 6
        gap = 8
        brick_width = (WIDTH - 100 - gap * (columns - 1)) // columns
        for row in range(rows):
            for column in range(columns):
                x = 50 + column * (brick_width + gap)
                y = 128 + row * 35
                bricks.append(Brick(pygame.Rect(x, y, brick_width, 23), row, BRICK_COLORS[row]))
        return bricks

    def run(self) -> None:
        while self.running:
            dt = min(self.clock.tick(120) / 1000.0, 0.03)
            self._handle_events()
            if self.state == "playing":
                self._update(dt)
            self._draw()
        pygame.quit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_r:
                    self.reset()
                    self.state = "playing"
                elif event.key == pygame.K_SPACE:
                    if self.state in {"title", "paused"}:
                        self.state = "playing"
                    elif self.state == "playing":
                        self.state = "paused"
                    else:
                        self.reset()
                        self.state = "playing"

    def _update(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        direction = int(keys[pygame.K_RIGHT] or keys[pygame.K_d]) - int(
            keys[pygame.K_LEFT] or keys[pygame.K_a]
        )
        if direction:
            self.paddle.x += round(direction * 600 * dt)
        elif pygame.mouse.get_focused():
            self.paddle.centerx = pygame.mouse.get_pos()[0]
        self.paddle.clamp_ip(pygame.Rect(18, PLAY_TOP, WIDTH - 36, HEIGHT - PLAY_TOP))

        previous = self.ball.rect
        self.ball.x += self.ball.vx * dt
        self.ball.y += self.ball.vy * dt

        if self.ball.x - self.ball.radius <= 16 and self.ball.vx < 0:
            self.ball.x = 16 + self.ball.radius
            self.ball.vx *= -1
        elif self.ball.x + self.ball.radius >= WIDTH - 16 and self.ball.vx > 0:
            self.ball.x = WIDTH - 16 - self.ball.radius
            self.ball.vx *= -1
        if self.ball.y - self.ball.radius <= PLAY_TOP and self.ball.vy < 0:
            self.ball.y = PLAY_TOP + self.ball.radius
            self.ball.vy *= -1

        if self.ball.rect.colliderect(self.paddle) and self.ball.vy > 0:
            self.ball.y = self.paddle.top - self.ball.radius
            self.ball.vx, self.ball.vy = bounce_from_paddle(
                self.ball.x, self.paddle.centerx, self.paddle.width, self.ball.speed
            )
            self.combo = 0
            self._burst(self.ball.x, self.ball.y, CYAN, 10)

        hit = self.ball.rect.collidelist([brick.rect for brick in self.bricks])
        if hit >= 0:
            brick = self.bricks.pop(hit)
            if previous.bottom <= brick.rect.top or previous.top >= brick.rect.bottom:
                self.ball.vy *= -1
            else:
                self.ball.vx *= -1
            event = score_for_brick(brick.row, self.combo)
            self.score += event.points
            self.combo = event.combo
            self.broken_bricks += 1
            old_speed = self.ball.speed
            new_speed = next_ball_speed(old_speed, self.broken_bricks)
            if new_speed != old_speed:
                scale = new_speed / old_speed
                self.ball.vx *= scale
                self.ball.vy *= scale
            self._burst(brick.rect.centerx, brick.rect.centery, brick.color, 18)

        if self.ball.y - self.ball.radius > HEIGHT:
            self.lives -= 1
            self.combo = 0
            if self.lives <= 0:
                self.state = "gameover"
            else:
                self.ball = Ball(self.paddle.centerx, HEIGHT - 85, random.choice((-220, 220)), -335)

        if not self.bricks:
            self.state = "won"

        alive: list[Particle] = []
        for particle in self.particles:
            particle.life -= dt
            particle.x += particle.vx * dt
            particle.y += particle.vy * dt
            particle.vy += 80 * dt
            if particle.life > 0:
                alive.append(particle)
        self.particles = alive

    def _burst(self, x: float, y: float, color: tuple[int, int, int], count: int) -> None:
        for _ in range(count):
            angle = random.random() * math.tau
            speed = random.uniform(70, 230)
            self.particles.append(
                Particle(x, y, math.cos(angle) * speed, math.sin(angle) * speed, random.uniform(0.25, 0.7), color)
            )

    def _draw(self) -> None:
        self.screen.fill(BACKGROUND)
        for x, y, radius in self.stars:
            pygame.draw.circle(self.screen, (25, 42, 75), (x, y), radius)
        pygame.draw.line(self.screen, (25, 65, 90), (16, PLAY_TOP), (WIDTH - 16, PLAY_TOP), 2)

        for brick in self.bricks:
            glow = brick.rect.inflate(8, 8)
            pygame.draw.rect(self.screen, (*brick.color, 45), glow, border_radius=8)
            pygame.draw.rect(self.screen, brick.color, brick.rect, border_radius=6)
            pygame.draw.line(self.screen, WHITE, brick.rect.topleft, brick.rect.topright, 2)

        pygame.draw.rect(self.screen, (25, 95, 105), self.paddle.inflate(12, 12), border_radius=14)
        pygame.draw.rect(self.screen, CYAN, self.paddle, border_radius=8)
        pygame.draw.circle(self.screen, (45, 110, 120), (int(self.ball.x), int(self.ball.y)), self.ball.radius + 7)
        pygame.draw.circle(self.screen, WHITE, (int(self.ball.x), int(self.ball.y)), self.ball.radius)

        for particle in self.particles:
            size = max(1, int(5 * min(particle.life * 2, 1)))
            pygame.draw.circle(self.screen, particle.color, (int(particle.x), int(particle.y)), size)

        self._draw_hud()
        if self.state == "title":
            self._overlay("EVOLVING GAME", "SPACE TO START  •  BUILD IT WITH AI")
        elif self.state == "paused":
            self._overlay("PAUSED", "SPACE TO RESUME")
        elif self.state == "gameover":
            self._overlay("MISSION FAILED", "SPACE TO RETRY  •  R TO RESET")
        elif self.state == "won":
            self._overlay("ALL CLEAR!", "ASK AI TO CREATE THE NEXT STAGE")
        pygame.display.flip()

    def _draw_hud(self) -> None:
        score = self.font.render(f"SCORE  {self.score:06d}", True, WHITE)
        lives = self.font.render(f"LIVES  {'●' * self.lives}", True, MAGENTA)
        combo = self.small_font.render(f"COMBO x{self.combo}" if self.combo > 1 else "COMBO READY", True, YELLOW)
        self.screen.blit(score, (24, 25))
        self.screen.blit(lives, (WIDTH - lives.get_width() - 24, 25))
        self.screen.blit(combo, (WIDTH // 2 - combo.get_width() // 2, 32))

    def _overlay(self, title: str, subtitle: str) -> None:
        layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        layer.fill((2, 5, 18, 185))
        self.screen.blit(layer, (0, 0))
        title_surface = self.big_font.render(title, True, CYAN)
        subtitle_surface = self.font.render(subtitle, True, WHITE)
        self.screen.blit(title_surface, title_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 25)))
        self.screen.blit(subtitle_surface, subtitle_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 45)))


def main() -> None:
    Game().run()


if __name__ == "__main__":
    main()
