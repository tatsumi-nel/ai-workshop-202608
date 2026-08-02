"""MediaPipeやカメラなしでテストできるジェスチャー判定。"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, Sequence


class Landmark(Protocol):
    x: float
    y: float


class Gesture(str, Enum):
    NONE = "NO HAND"
    POINTER = "POINTER / MOVE"
    FIST = "FIST / FIRE"
    OPEN = "OPEN / SHIELD"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class GestureReading:
    gesture: Gesture
    x: float = 0.5
    confidence: float = 0.0


FINGER_TIPS = (8, 12, 16, 20)
FINGER_PIPS = (6, 10, 14, 18)


def raised_fingers(landmarks: Sequence[Landmark], margin: float = 0.025) -> tuple[bool, ...]:
    """人差し指から小指まで、伸びているかを返す。"""

    if len(landmarks) != 21:
        raise ValueError("手のランドマークは21点必要です")
    return tuple(
        landmarks[tip].y < landmarks[pip].y - margin
        for tip, pip in zip(FINGER_TIPS, FINGER_PIPS, strict=True)
    )


def classify_hand(landmarks: Sequence[Landmark]) -> GestureReading:
    """4本の指の状態から、ゲーム用の3ジェスチャーへ分類する。"""

    raised = raised_fingers(landmarks)
    count = sum(raised)
    palm_x = sum(landmarks[index].x for index in (0, 5, 9, 13, 17)) / 5
    if count == 0:
        gesture = Gesture.FIST
    elif raised == (True, False, False, False):
        gesture = Gesture.POINTER
    elif count >= 3:
        gesture = Gesture.OPEN
    else:
        gesture = Gesture.UNKNOWN
    confidence = 1.0 if gesture is not Gesture.UNKNOWN else 0.45
    return GestureReading(gesture=gesture, x=max(0.0, min(palm_x, 1.0)), confidence=confidence)

