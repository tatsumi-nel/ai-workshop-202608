"""手のジェスチャーで宇宙船を操作するアリーナゲーム。"""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass

import pygame

from gesture_logic import Gesture, GestureReading

SCREEN_WIDTH, SCREEN_HEIGHT = 1120, 700
ARENA_WIDTH = 780
NAVY = (5, 8, 24)
CYAN = (60, 235, 255)
MAGENTA = (255, 60, 185)
WHITE = (235, 245, 255)
YELLOW = (255, 220, 70)


@dataclass
class Meteor:
    x: float
    y: float
    speed: float
    radius: int

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x - self.radius), int(self.y - self.radius), self.radius * 2, self.radius * 2)


@dataclass
class Laser:
    x: float
    y: float

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x - 3), int(self.y - 18), 6, 24)


class GestureArena:
    def __init__(self, use_camera: bool, camera_index: int) -> None:
        pygame.init()
        pygame.display.set_caption("GESTURE ARENA // Local AI")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 23, bold=True)
        self.small = pygame.font.SysFont("arial", 16)
        self.big = pygame.font.SysFont("arial", 46, bold=True)
        self.controller = None
        self.camera_message = "KEYBOARD MODE"
        if use_camera:
            try:
                from camera_input import CameraGestureController

                self.controller = CameraGestureController(camera_index)
                self.camera_message = "CAMERA ONLINE"
            except Exception as error:  # Camera/OS errors must not prevent the workshop.
                self.camera_message = f"CAMERA OFFLINE: {error}"
        self.running = True
        self.preview = None
        self.stars = [(random.randrange(ARENA_WIDTH), random.randrange(SCREEN_HEIGHT), random.randrange(1, 3)) for _ in range(95)]
        self.reset()

    def reset(self) -> None:
        self.player_x = ARENA_WIDTH / 2
        self.player_y = SCREEN_HEIGHT - 78
        self.health = 100
        self.score = 0
        self.shield = False
        self.lasers: list[Laser] = []
        self.meteors: list[Meteor] = []
        self.spawn_timer = 0.3
        self.fire_cooldown = 0.0
        self.reading = GestureReading(Gesture.NONE)
        self.game_over = False

    def run(self) -> None:
        try:
            while self.running:
                dt = min(self.clock.tick(60) / 1000.0, 0.04)
                self._events()
                self._update(dt)
                self._draw()
        finally:
            if self.controller is not None:
                self.controller.close()
            pygame.quit()

    def _events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_r:
                    self.reset()

    def _update(self, dt: float) -> None:
        if self.game_over:
            return
        self.fire_cooldown = max(0.0, self.fire_cooldown - dt)
        keys = pygame.key.get_pressed()
        keyboard_direction = int(keys[pygame.K_RIGHT] or keys[pygame.K_d]) - int(
            keys[pygame.K_LEFT] or keys[pygame.K_a]
        )

        if self.controller is not None:
            self.reading, self.preview = self.controller.read()
            if self.reading.gesture is Gesture.POINTER:
                self.player_x += (self.reading.x * ARENA_WIDTH - self.player_x) * min(1.0, dt * 10)
            if self.reading.gesture is Gesture.FIST:
                self._fire()
            self.shield = self.reading.gesture is Gesture.OPEN
        else:
            self.reading = GestureReading(Gesture.NONE)

        if keyboard_direction:
            self.player_x += keyboard_direction * 520 * dt
        if keys[pygame.K_SPACE]:
            self._fire()
        if keys[pygame.K_s]:
            self.shield = True
        elif self.controller is None or self.reading.gesture is not Gesture.OPEN:
            self.shield = False
        self.player_x = max(38, min(self.player_x, ARENA_WIDTH - 38))

        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.meteors.append(
                Meteor(
                    x=random.uniform(28, ARENA_WIDTH - 28),
                    y=-30,
                    speed=random.uniform(145, 245) + min(self.score, 1500) * 0.025,
                    radius=random.randrange(15, 29),
                )
            )
            self.spawn_timer = random.uniform(0.35, 0.72)

        for laser in self.lasers:
            laser.y -= 680 * dt
        self.lasers = [laser for laser in self.lasers if laser.y > -30]
        for meteor in self.meteors:
            meteor.y += meteor.speed * dt

        for laser in self.lasers[:]:
            hit = next((meteor for meteor in self.meteors if laser.rect.colliderect(meteor.rect)), None)
            if hit is not None:
                self.lasers.remove(laser)
                self.meteors.remove(hit)
                self.score += 100

        player_rect = pygame.Rect(int(self.player_x - 25), int(self.player_y - 22), 50, 44)
        for meteor in self.meteors[:]:
            if meteor.rect.colliderect(player_rect):
                self.meteors.remove(meteor)
                if self.shield:
                    self.score += 25
                else:
                    self.health -= 25
                    if self.health <= 0:
                        self.game_over = True
            elif meteor.y - meteor.radius > SCREEN_HEIGHT:
                self.meteors.remove(meteor)

    def _fire(self) -> None:
        if self.fire_cooldown <= 0:
            self.lasers.append(Laser(self.player_x, self.player_y - 28))
            self.fire_cooldown = 0.22

    def _draw(self) -> None:
        self.screen.fill(NAVY)
        for x, y, radius in self.stars:
            pygame.draw.circle(self.screen, (25, 44, 78), (x, y), radius)
        pygame.draw.line(self.screen, (35, 95, 120), (ARENA_WIDTH, 0), (ARENA_WIDTH, SCREEN_HEIGHT), 2)

        for meteor in self.meteors:
            pygame.draw.circle(self.screen, (120, 55, 100), (int(meteor.x), int(meteor.y)), meteor.radius + 5)
            pygame.draw.circle(self.screen, MAGENTA, (int(meteor.x), int(meteor.y)), meteor.radius, 3)
        for laser in self.lasers:
            pygame.draw.rect(self.screen, CYAN, laser.rect, border_radius=3)
            pygame.draw.rect(self.screen, WHITE, laser.rect.inflate(-3, 0), border_radius=2)

        ship = [(self.player_x, self.player_y - 30), (self.player_x - 28, self.player_y + 24), (self.player_x, self.player_y + 12), (self.player_x + 28, self.player_y + 24)]
        pygame.draw.polygon(self.screen, CYAN, ship)
        pygame.draw.polygon(self.screen, WHITE, ship, 2)
        pygame.draw.polygon(self.screen, YELLOW, [(self.player_x - 10, self.player_y + 19), (self.player_x, self.player_y + 38), (self.player_x + 10, self.player_y + 19)])
        if self.shield:
            pygame.draw.circle(self.screen, (80, 180, 255), (int(self.player_x), int(self.player_y)), 54, 4)

        self._draw_panel()
        if self.game_over:
            shade = pygame.Surface((ARENA_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            shade.fill((4, 6, 20, 190))
            self.screen.blit(shade, (0, 0))
            title = self.big.render("SIGNAL LOST", True, MAGENTA)
            retry = self.font.render("Press R to reconnect", True, WHITE)
            self.screen.blit(title, title.get_rect(center=(ARENA_WIDTH // 2, SCREEN_HEIGHT // 2 - 20)))
            self.screen.blit(retry, retry.get_rect(center=(ARENA_WIDTH // 2, SCREEN_HEIGHT // 2 + 42)))
        pygame.display.flip()

    def _draw_panel(self) -> None:
        panel_x = ARENA_WIDTH + 20
        self.screen.blit(self.font.render("GESTURE ARENA", True, CYAN), (panel_x, 22))
        camera_status = self.small.render(self.camera_message[:39], True, WHITE)
        self.screen.blit(camera_status, (panel_x, 59))
        if self.preview is not None:
            surface = pygame.surfarray.make_surface(self.preview.swapaxes(0, 1))
            surface = pygame.transform.smoothscale(surface, (300, 225))
            self.screen.blit(surface, (panel_x, 91))
        else:
            pygame.draw.rect(self.screen, (12, 20, 44), (panel_x, 91, 300, 225), border_radius=8)
            text = self.small.render("Camera preview unavailable", True, (120, 145, 170))
            self.screen.blit(text, text.get_rect(center=(panel_x + 150, 203)))

        gesture_color = {Gesture.FIST: MAGENTA, Gesture.OPEN: CYAN, Gesture.POINTER: YELLOW}.get(self.reading.gesture, WHITE)
        self.screen.blit(self.small.render("DETECTED", True, (120, 145, 170)), (panel_x, 341))
        self.screen.blit(self.font.render(self.reading.gesture.value, True, gesture_color), (panel_x, 364))
        self.screen.blit(self.font.render(f"SCORE  {self.score:05d}", True, WHITE), (panel_x, 425))
        self.screen.blit(self.font.render(f"HULL   {self.health:3d}%", True, WHITE), (panel_x, 461))
        pygame.draw.rect(self.screen, (35, 45, 65), (panel_x, 501, 300, 14), border_radius=7)
        pygame.draw.rect(self.screen, CYAN if self.health > 25 else MAGENTA, (panel_x, 501, int(300 * self.health / 100), 14), border_radius=7)
        instructions = ["POINTER  move", "FIST     fire", "OPEN     shield", "", "Keyboard: arrows / SPACE / S"]
        for index, line in enumerate(instructions):
            self.screen.blit(self.small.render(line, True, (165, 190, 210)), (panel_x, 548 + index * 23))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="手のジェスチャーで遊ぶローカル画像認識ゲーム")
    parser.add_argument("--no-camera", action="store_true", help="キーボード操作で起動する")
    parser.add_argument("--camera-index", type=int, default=0, help="使用するカメラ番号")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    GestureArena(use_camera=not args.no_camera, camera_index=args.camera_index).run()


if __name__ == "__main__":
    main()

