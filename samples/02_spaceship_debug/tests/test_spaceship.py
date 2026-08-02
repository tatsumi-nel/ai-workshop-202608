import pytest

from spaceship import Spaceship, average_sensor_reading, clamp_percent


def make_ship(**overrides: float | int | str | bool) -> Spaceship:
    values: dict[str, float | int | str | bool] = {
        "name": "TEST-1",
        "fuel": 90.0,
        "oxygen": 95.0,
        "hull": 99.0,
        "crew": 4,
    }
    values.update(overrides)
    return Spaceship(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("value", "expected"),
    [(-12.0, 0.0), (42.0, 42.0), (120.0, 100.0)],
)
def test_percent_is_always_clamped(value: float, expected: float) -> None:
    assert clamp_percent(value) == expected


def test_fuel_never_becomes_negative() -> None:
    ship = make_ship(fuel=10.0)
    ship.consume_fuel(25.0)
    assert ship.fuel == 0.0


def test_oxygen_consumption_uses_mission_coefficient() -> None:
    ship = make_ship(oxygen=100.0, crew=4)
    ship.advance_time(10)
    assert ship.oxygen == pytest.approx(98.4)


@pytest.mark.parametrize(
    ("fuel", "oxygen", "hull"),
    [(79, 95, 99), (90, 89, 99), (90, 95, 94)],
)
def test_launch_requires_every_check(fuel: float, oxygen: float, hull: float) -> None:
    assert make_ship(fuel=fuel, oxygen=oxygen, hull=hull).ready_for_launch() is False


def test_launch_succeeds_when_every_check_passes() -> None:
    assert make_ship(fuel=80, oxygen=90, hull=95).ready_for_launch() is True


@pytest.mark.parametrize(
    ("temperature", "radiation"),
    [(900, 20), (400, 250), (950, 300)],
)
def test_either_hazard_triggers_shutdown(temperature: float, radiation: float) -> None:
    ship = make_ship(reactor_temperature=temperature, radiation=radiation)
    assert ship.check_emergency_shutdown() is True
    assert ship.reactor_online is False


def test_safe_reactor_stays_online() -> None:
    ship = make_ship(reactor_temperature=899, radiation=249)
    assert ship.check_emergency_shutdown() is False
    assert ship.reactor_online is True


def test_sensor_average_keeps_decimal_precision() -> None:
    assert average_sensor_reading([315.5, 316.0, 315.8]) == pytest.approx(315.7666667)


def test_empty_sensor_readings_are_rejected() -> None:
    with pytest.raises(ValueError, match="センサー値"):
        average_sensor_reading([])
