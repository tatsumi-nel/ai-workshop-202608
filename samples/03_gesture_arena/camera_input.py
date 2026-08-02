"""WebカメラとMediaPipeをゲーム入力へ変換するアダプター。"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any
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
        self.capture = cv2.VideoCapture(camera_index)
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
