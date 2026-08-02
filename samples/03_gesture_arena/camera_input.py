"""WebカメラとMediaPipeをゲーム入力へ変換するアダプター。"""

from __future__ import annotations

import time
from dataclasses import dataclass
from multiprocessing import get_context
from multiprocessing.queues import Queue
from pathlib import Path
from platform import system
from queue import Empty, Full
from typing import Any, Callable
from urllib.request import urlopen

from gesture_logic import Gesture, GestureReading, classify_hand

MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/1/hand_landmarker.task"
)
MODEL_PATH = Path(__file__).parent / "models" / "hand_landmarker.task"
HAND_CONNECTIONS = (
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20), (0, 17),
)


def ensure_hand_model(path: Path = MODEL_PATH) -> Path:
    """公式の手認識モデルを初回だけ取得する。"""

    if path.is_file() and path.stat().st_size > 1_000_000:
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".part")
    with urlopen(MODEL_URL, timeout=60) as response, temporary.open("wb") as destination:
        while chunk := response.read(1024 * 1024):
            destination.write(chunk)
    temporary.replace(path)
    return path


class CameraGestureController:
    """カメラを所有し、各フレームのジェスチャーを返す。"""

    def __init__(self, camera_index: int = 0) -> None:
        import cv2
        import mediapipe as mp
        from mediapipe.tasks.python import BaseOptions, vision

        self.cv2 = cv2
        self.mp = mp
        backend = cv2.CAP_AVFOUNDATION if system() == "Darwin" else cv2.CAP_ANY
        self.capture = cv2.VideoCapture(camera_index, backend)
        if not self.capture.isOpened():
            self.capture.release()
            raise RuntimeError(f"カメラ {camera_index} を開けませんでした")
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        model_path = ensure_hand_model()
        options = vision.HandLandmarkerOptions(
            base_options=BaseOptions(
                model_asset_path=str(model_path),
                delegate=BaseOptions.Delegate.CPU,
            ),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=1,
            min_hand_detection_confidence=0.55,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.hands = vision.HandLandmarker.create_from_options(options)
        self.started_at = time.monotonic()

    def read(self) -> tuple[GestureReading, Any | None]:
        ok, frame = self.capture.read()
        if not ok:
            return GestureReading(Gesture.NONE), None
        frame = self.cv2.flip(frame, 1)
        rgb = self.cv2.cvtColor(frame, self.cv2.COLOR_BGR2RGB)
        image = self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=rgb)
        timestamp_ms = int((time.monotonic() - self.started_at) * 1000)
        result = self.hands.detect_for_video(image, timestamp_ms)
        if not result.hand_landmarks:
            return GestureReading(Gesture.NONE), rgb
        hand = result.hand_landmarks[0]
        reading = classify_hand(hand)
        self._draw_hand(frame, hand)
        preview = self.cv2.cvtColor(frame, self.cv2.COLOR_BGR2RGB)
        return reading, preview

    def _draw_hand(self, frame: Any, hand: Any) -> None:
        """認識できていることが分かるよう骨格を重ねる。"""

        height, width = frame.shape[:2]
        points = [(int(point.x * width), int(point.y * height)) for point in hand]
        for start, end in HAND_CONNECTIONS:
            self.cv2.line(frame, points[start], points[end], (255, 220, 60), 2)
        for point in points:
            self.cv2.circle(frame, point, 4, (255, 80, 210), -1)

    def close(self) -> None:
        self.hands.close()
        self.capture.release()


@dataclass(frozen=True)
class CameraSnapshot:
    """ゲーム側が安全に読み取れる、カメラプロセスの最新状態。"""

    reading: GestureReading
    preview: Any | None
    status: str


class CameraWorker:
    """ブロッキングするカメラ処理を別プロセスへ分離する。"""

    def __init__(
        self,
        camera_index: int = 0,
        controller_factory: Callable[[int], Any] = CameraGestureController,
    ) -> None:
        self.camera_index = camera_index
        self.controller_factory = controller_factory
        self._context = get_context("spawn")
        self._stop = self._context.Event()
        self._queue: Queue = self._context.Queue(maxsize=2)
        self._process = None
        self._snapshot = CameraSnapshot(
            reading=GestureReading(Gesture.NONE),
            preview=None,
            status="CAMERA STARTING...",
        )

    def start(self) -> None:
        """すぐに戻り、カメラ初期化はdaemonプロセスで行う。"""

        if self._process is not None:
            return
        self._process = self._context.Process(
            target=_camera_process,
            args=(
                self.camera_index,
                self.controller_factory,
                self._queue,
                self._stop,
            ),
            name="gesture-camera",
            daemon=True,
        )
        self._process.start()

    def snapshot(self) -> CameraSnapshot:
        while True:
            try:
                self._snapshot = self._queue.get_nowait()
            except Empty:
                return self._snapshot

    def stop(self, timeout: float = 0.5) -> None:
        """終了を通知し、OS内で停止中なら子プロセスだけを終了する。"""

        self._stop.set()
        if self._process is not None:
            self._process.join(timeout=timeout)
            if self._process.is_alive():
                self._process.terminate()
                self._process.join(timeout=timeout)
        self._queue.cancel_join_thread()
        self._queue.close()

    @property
    def is_alive(self) -> bool:
        return self._process is not None and self._process.is_alive()


def _publish(queue: Queue, snapshot: CameraSnapshot) -> None:
    """古いフレームを捨て、常に新しい状態を優先する。"""

    try:
        queue.put_nowait(snapshot)
        return
    except Full:
        pass
    try:
        queue.get_nowait()
    except Empty:
        pass
    try:
        queue.put_nowait(snapshot)
    except Full:
        pass


def _camera_process(
    camera_index: int,
    controller_factory: Callable[[int], Any],
    queue: Queue,
    stop: Any,
) -> None:
    """子プロセスでだけOpenCVとMediaPipeを読み込んで実行する。"""

    controller = None
    try:
        _publish(queue, CameraSnapshot(GestureReading(Gesture.NONE), None, "OPENING CAMERA..."))
        controller = controller_factory(camera_index)
        _publish(queue, CameraSnapshot(GestureReading(Gesture.NONE), None, "CAMERA ONLINE"))
        while not stop.is_set():
            reading, preview = controller.read()
            _publish(queue, CameraSnapshot(reading, preview, "CAMERA ONLINE"))
    except Exception as error:
        if isinstance(error, RuntimeError) and "カメラ" in str(error):
            message = "CAMERA OFFLINE - CHECK PERMISSION"
        else:
            message = f"CAMERA OFFLINE: {type(error).__name__}"
        _publish(queue, CameraSnapshot(GestureReading(Gesture.NONE), None, message))
        print(f"{message}: {error}", flush=True)
    finally:
        if controller is not None:
            controller.close()
