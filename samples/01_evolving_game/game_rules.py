"""画面表示に依存しない、テストしやすいゲームルール。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScoreEvent:
    """ブロック破壊時に計算された得点と次のコンボ。"""

    points: int
    combo: int


def clamp(value: float, minimum: float, maximum: float) -> float:
    """値を閉区間内に収める。"""

    return max(minimum, min(value, maximum))


def score_for_brick(row: int, combo: int) -> ScoreEvent:
    """上段ほど、また連続して壊すほど高い得点にする。"""

    if row < 0 or combo < 0:
        raise ValueError("row と combo は0以上でなければなりません")
    next_combo = combo + 1
    base = 100 + max(0, 5 - row) * 25
    multiplier = 1 + min(next_combo - 1, 9) * 0.1
    return ScoreEvent(points=int(base * multiplier), combo=next_combo)


def bounce_from_paddle(
    ball_x: float,
    paddle_center_x: float,
    paddle_width: float,
    speed: float,
) -> tuple[float, float]:
    """衝突位置を反映した新しい速度ベクトルを返す。"""

    if paddle_width <= 0 or speed <= 0:
        raise ValueError("paddle_width と speed は正でなければなりません")
    offset = clamp((ball_x - paddle_center_x) / (paddle_width / 2), -1.0, 1.0)
    velocity_x = speed * offset * 0.85
    velocity_y = -(speed**2 - velocity_x**2) ** 0.5
    return velocity_x, velocity_y


def next_ball_speed(current_speed: float, broken_bricks: int) -> float:
    """一定数のブロック破壊ごとに少しだけ難しくする。"""

    if current_speed <= 0 or broken_bricks < 0:
        raise ValueError("速度は正、破壊数は0以上でなければなりません")
    if broken_bricks and broken_bricks % 8 == 0:
        return min(current_speed + 24.0, 620.0)
    return current_speed

