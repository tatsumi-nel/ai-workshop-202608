import time

from camera_input import CameraWorker


class BlockingController:
    def __init__(self, camera_index: int) -> None:
        assert camera_index == 7
        time.sleep(2)

    def read(self):
        raise AssertionError("初期化中に停止するので呼ばれない")

    def close(self) -> None:
        pass


def test_camera_initialization_does_not_block_main_thread() -> None:
    worker = CameraWorker(camera_index=7, controller_factory=BlockingController)

    started_at = time.monotonic()
    worker.start()

    assert time.monotonic() - started_at < 0.5
    worker.stop(timeout=0.1)
    assert worker.is_alive is False


class BrokenController:
    def __init__(self, camera_index: int) -> None:
        raise RuntimeError("permission denied")


def test_camera_error_is_reported_without_raising() -> None:
    worker = CameraWorker(controller_factory=BrokenController)
    worker.start()
    deadline = time.monotonic() + 2
    while worker.snapshot().status == "CAMERA STARTING..." and time.monotonic() < deadline:
        time.sleep(0.01)
    assert worker.snapshot().status == "CAMERA OFFLINE: RuntimeError"
    worker.stop()
