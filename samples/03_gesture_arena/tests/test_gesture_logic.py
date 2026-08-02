from dataclasses import dataclass

import pytest

from gesture_logic import Gesture, classify_hand, raised_fingers


@dataclass
class Point:
    x: float = 0.5
    y: float = 0.5


def hand_with_raised(*finger_indexes: int, palm_x: float = 0.5) -> list[Point]:
    points = [Point(x=palm_x, y=0.6) for _ in range(21)]
    for pip in (6, 10, 14, 18):
        points[pip].y = 0.45
    for index, tip in enumerate((8, 12, 16, 20)):
        points[tip].y = 0.25 if index in finger_indexes else 0.65
    return points


def test_fist_is_recognized() -> None:
    assert classify_hand(hand_with_raised()).gesture is Gesture.FIST


def test_index_finger_is_pointer() -> None:
    assert classify_hand(hand_with_raised(0)).gesture is Gesture.POINTER


@pytest.mark.parametrize("raised", [(0, 1, 2), (0, 1, 2, 3)])
def test_three_or_four_fingers_are_open(raised: tuple[int, ...]) -> None:
    assert classify_hand(hand_with_raised(*raised)).gesture is Gesture.OPEN


def test_two_fingers_are_left_for_future_extension() -> None:
    assert classify_hand(hand_with_raised(0, 1)).gesture is Gesture.UNKNOWN


def test_horizontal_position_comes_from_palm() -> None:
    reading = classify_hand(hand_with_raised(0, palm_x=0.8))
    assert reading.x == pytest.approx(0.8)


def test_landmark_count_is_validated() -> None:
    with pytest.raises(ValueError, match="21"):
        raised_fingers([Point()] * 20)
