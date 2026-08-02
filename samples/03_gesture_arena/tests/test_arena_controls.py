import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from arena import ARENA_WIDTH, GestureArena
from camera_input import CameraSnapshot
from gesture_logic import Gesture, GestureReading


class FakeCameraWorker:
    def __init__(self, gesture: Gesture, x: float) -> None:
        self._snapshot = CameraSnapshot(
            reading=GestureReading(gesture=gesture, x=x, confidence=1.0),
            preview=None,
            status="CAMERA ONLINE",
        )

    def snapshot(self) -> CameraSnapshot:
        return self._snapshot


def test_q_key_quits() -> None:
    game = GestureArena(use_camera=False, camera_index=0)
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_q))
    game._events()
    assert game.running is False
    pygame.quit()


@pytest.mark.parametrize("gesture", [Gesture.POINTER, Gesture.FIST, Gesture.OPEN, Gesture.UNKNOWN])
def test_any_detected_hand_moves_ship_horizontally(gesture: Gesture) -> None:
    game = GestureArena(use_camera=False, camera_index=0)
    game.camera_worker = FakeCameraWorker(gesture=gesture, x=0.9)  # type: ignore[assignment]
    initial_x = game.player_x

    game._update(0.05)

    assert game.player_x > initial_x
    assert game.player_x <= ARENA_WIDTH * 0.9
    game.camera_worker = None
    pygame.quit()
