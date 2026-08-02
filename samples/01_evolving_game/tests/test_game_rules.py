import math

import pytest

from game_rules import bounce_from_paddle, clamp, next_ball_speed, score_for_brick


def test_clamp_keeps_value_inside_range() -> None:
    assert clamp(-5, 0, 10) == 0
    assert clamp(6, 0, 10) == 6
    assert clamp(20, 0, 10) == 10


def test_combo_increases_score() -> None:
    first = score_for_brick(row=2, combo=0)
    fifth = score_for_brick(row=2, combo=4)
    assert first.combo == 1
    assert fifth.combo == 5
    assert fifth.points > first.points


def test_upper_bricks_are_worth_more() -> None:
    assert score_for_brick(row=0, combo=0).points > score_for_brick(row=5, combo=0).points


def test_paddle_center_sends_ball_straight_up() -> None:
    vx, vy = bounce_from_paddle(100, 100, 120, 400)
    assert vx == pytest.approx(0)
    assert vy == pytest.approx(-400)


def test_paddle_edge_preserves_speed() -> None:
    vx, vy = bounce_from_paddle(160, 100, 120, 400)
    assert vx > 0
    assert vy < 0
    assert math.hypot(vx, vy) == pytest.approx(400)


def test_ball_accelerates_every_eight_bricks() -> None:
    assert next_ball_speed(400, 7) == 400
    assert next_ball_speed(400, 8) == 424
    assert next_ball_speed(620, 16) == 620
