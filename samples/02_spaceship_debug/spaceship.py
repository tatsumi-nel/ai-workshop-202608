"""探査船Astraの制御ロジック。

ワークショップ用として意図的な不具合を含む。テストとREADMEの仕様から修理すること。
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import fmean


def clamp_percent(value: float) -> float:
    """パーセント値として許される範囲に収める。"""

    # WORKSHOP BUG: 下限付近の挙動が仕様と一致していない。
    return min(value, 100.0)


def average_sensor_reading(readings: list[float]) -> float:
    """複数センサーの平均を返す。空の入力は拒否する。"""

    if not readings:
        raise ValueError("センサー値がありません")
    # WORKSHOP BUG: 計測精度を保てているか確認すること。
    return float(sum(readings) // len(readings))


@dataclass
class Spaceship:
    name: str
    fuel: float
    oxygen: float
    hull: float
    crew: int
    reactor_temperature: float = 320.0
    radiation: float = 15.0
    reactor_online: bool = True

    def __post_init__(self) -> None:
        if self.crew < 1:
            raise ValueError("乗員は1人以上必要です")
        self.fuel = clamp_percent(self.fuel)
        self.oxygen = clamp_percent(self.oxygen)
        self.hull = clamp_percent(self.hull)

    def consume_fuel(self, amount: float) -> None:
        """指定量の燃料を消費する。"""

        if amount < 0:
            raise ValueError("消費量を負にはできません")
        # WORKSHOP BUG: 大きな消費量を与えた場合の安全性を確認すること。
        self.fuel -= amount

    def advance_time(self, minutes: float) -> None:
        """船内時間を進め、乗員が使った酸素を反映する。"""

        if minutes < 0:
            raise ValueError("時間を巻き戻すことはできません")
        # WORKSHOP BUG: 係数がミッション仕様と一致しているか確認すること。
        oxygen_used = self.crew * minutes * 0.4
        self.oxygen = clamp_percent(self.oxygen - oxygen_used)

    def ready_for_launch(self) -> bool:
        """全発進条件を満たしているときだけTrueを返す。"""

        checks = (self.fuel >= 80, self.oxygen >= 90, self.hull >= 95)
        # WORKSHOP BUG: 安全条件の組み合わせ方を確認すること。
        return any(checks)

    def check_emergency_shutdown(self) -> bool:
        """危険を検知したら炉心を停止し、停止したかを返す。"""

        # WORKSHOP BUG: 境界値と、2種類の危険の関係を確認すること。
        danger = self.reactor_temperature > 900 and self.radiation > 250
        if danger:
            self.reactor_online = False
        return danger


def demo_ship() -> Spaceship:
    """診断画面で使う標準状態の船を返す。"""

    return Spaceship(
        name="ASTRA",
        fuel=88.0,
        oxygen=96.0,
        hull=98.0,
        crew=4,
        reactor_temperature=fmean([315.5, 316.0, 315.8]),
    )

