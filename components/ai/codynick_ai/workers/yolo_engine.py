"""Persistent YOLOv8 ONNX detector derived from the legacy CodyNick engine."""

from __future__ import annotations

import json
import time
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort


COCO80 = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat", "traffic light",
    "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat", "dog", "horse", "sheep", "cow",
    "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
    "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove", "skateboard", "surfboard",
    "tennis racket", "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
    "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch",
    "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse", "remote", "keyboard", "cell phone",
    "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors", "teddy bear",
    "hair drier", "toothbrush",
]


def _json_default(value):
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    return str(value)


def letterbox(image: np.ndarray, new_shape: int = 640):
    height, width = image.shape[:2]
    ratio = min(new_shape / height, new_shape / width)
    new_height = int(round(height * ratio))
    new_width = int(round(width * ratio))
    pad_height = new_shape - new_height
    pad_width = new_shape - new_width
    top = pad_height // 2
    bottom = pad_height - top
    left = pad_width // 2
    right = pad_width - left
    image = cv2.resize(image, (new_width, new_height))
    image = cv2.copyMakeBorder(
        image,
        top,
        bottom,
        left,
        right,
        cv2.BORDER_CONSTANT,
        value=(114, 114, 114),
    )
    return image, ratio, (left, top)


def nms(
    boxes: np.ndarray,
    scores: np.ndarray,
    class_ids: np.ndarray,
    iou_threshold: float = 0.5,
):
    """Apply class-aware NMS so different object classes never suppress each other."""
    indexes = scores.argsort()[::-1]
    keep = []
    while indexes.size > 0:
        index = indexes[0]
        keep.append(index)
        if indexes.size == 1:
            break

        xx1 = np.maximum(boxes[index, 0], boxes[indexes[1:], 0])
        yy1 = np.maximum(boxes[index, 1], boxes[indexes[1:], 1])
        xx2 = np.minimum(boxes[index, 2], boxes[indexes[1:], 2])
        yy2 = np.minimum(boxes[index, 3], boxes[indexes[1:], 3])

        intersection = np.maximum(0, xx2 - xx1) * np.maximum(0, yy2 - yy1)
        area_i = (boxes[index, 2] - boxes[index, 0]) * (boxes[index, 3] - boxes[index, 1])
        area_j = (
            (boxes[indexes[1:], 2] - boxes[indexes[1:], 0])
            * (boxes[indexes[1:], 3] - boxes[indexes[1:], 1])
        )
        iou = intersection / (area_i + area_j - intersection + 1e-6)
        remaining = indexes[1:]
        same_class = class_ids[remaining] == class_ids[index]
        indexes = remaining[(~same_class) | (iou <= iou_threshold)]
    return keep


class YoloObjectDetector:
    """Load one ONNX session and reuse it for every detection request."""

    def __init__(self, model_path: str | Path):
        self.model_path = Path(model_path).expanduser().resolve()
        if not self.model_path.is_file():
            raise FileNotFoundError(
                f"YOLO ONNX model not found: {self.model_path}. "
                "The VHL installer never downloads model weights."
            )
        started = time.perf_counter()
        self.session = ort.InferenceSession(
            str(self.model_path), providers=["CPUExecutionProvider"]
        )
        self.input_name = self.session.get_inputs()[0].name
        self.load_seconds = time.perf_counter() - started

    def warmup(self) -> float:
        started = time.perf_counter()
        sample = np.zeros((1, 3, 640, 640), dtype=np.float32)
        self.session.run(None, {self.input_name: sample})
        return time.perf_counter() - started

    def detect(
        self,
        image_path: str | Path,
        *,
        conf_threshold: float = 0.35,
        iou_threshold: float = 0.5,
        save_visual: bool = True,
        output_dir: str | Path | None = None,
        output_suffix: str = "objects",
    ) -> dict:
        started = time.perf_counter()
        image_path = Path(image_path).expanduser().resolve()
        if not image_path.is_file():
            raise FileNotFoundError(f"Image not found: {image_path}")
        if not 0.0 <= conf_threshold <= 1.0:
            raise ValueError("conf_threshold must be between 0 and 1.")
        if not 0.0 <= iou_threshold <= 1.0:
            raise ValueError("iou_threshold must be between 0 and 1.")

        original = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        if original is None:
            raise ValueError(f"Failed to read image: {image_path}")

        prepared, ratio, (offset_x, offset_y) = letterbox(original.copy(), 640)
        prepared = cv2.cvtColor(prepared, cv2.COLOR_BGR2RGB)
        blob = (
            (prepared.astype(np.float32) / 255.0)
            .transpose(2, 0, 1)[None, :, :, :]
        )
        output = self.session.run(None, {self.input_name: blob})[0]
        if output.ndim == 3 and output.shape[0] == 1:
            output = output[0]

        if output.ndim == 2 and (
            output.shape[1] in (84, 85) or output.shape[0] in (84, 85)
        ):
            if output.shape[0] in (84, 85):
                output = output.T
            _, dimensions = output.shape
            xywh = output[:, :4].astype(np.float32).copy()

            if dimensions == 84:
                class_scores = output[:, 4:].astype(np.float32).copy()
                if class_scores.max() > 1.0 or class_scores.min() < 0.0:
                    class_scores = 1.0 / (1.0 + np.exp(-class_scores))
                scores = class_scores
            elif dimensions == 85:
                object_score = output[:, 4:5].astype(np.float32).copy()
                class_scores = output[:, 5:].astype(np.float32).copy()
                if object_score.max() > 1.0 or object_score.min() < 0.0:
                    object_score = 1.0 / (1.0 + np.exp(-object_score))
                if class_scores.max() > 1.0 or class_scores.min() < 0.0:
                    class_scores = 1.0 / (1.0 + np.exp(-class_scores))
                scores = object_score * class_scores
            else:
                raise RuntimeError(f"Unexpected YOLO output width: {dimensions}")

            confidence = scores.max(axis=1)
            class_ids = scores.argmax(axis=1)
            if xywh.max() <= 2.0:
                xywh *= 640.0
            boxes = np.empty_like(xywh)
            boxes[:, 0] = xywh[:, 0] - xywh[:, 2] / 2
            boxes[:, 1] = xywh[:, 1] - xywh[:, 3] / 2
            boxes[:, 2] = xywh[:, 0] + xywh[:, 2] / 2
            boxes[:, 3] = xywh[:, 1] + xywh[:, 3] / 2

            mask = confidence > conf_threshold
            boxes = boxes[mask]
            confidence = confidence[mask]
            class_ids = class_ids[mask]
            kept = (
                nms(boxes, confidence, class_ids, iou_threshold)
                if len(boxes)
                else []
            )
            boxes = boxes[kept]
            confidence = confidence[kept]
            class_ids = class_ids[kept]
        elif output.ndim == 2 and output.shape[1] == 6:
            boxes = output[:, :4].astype(np.float32).copy()
            confidence = output[:, 4].astype(np.float32).copy()
            class_ids = output[:, 5].astype(np.int32).copy()
            mask = confidence > conf_threshold
            boxes = boxes[mask]
            confidence = confidence[mask]
            class_ids = class_ids[mask]
        elif output.ndim == 1 and output.shape[0] == 6:
            boxes = output[:4][None, :].astype(np.float32)
            confidence = np.array([float(output[4])], dtype=np.float32)
            class_ids = np.array([int(output[5])], dtype=np.int32)
        else:
            raise RuntimeError(f"Unhandled ONNX output layout: {output.shape}")

        if len(boxes):
            boxes[:, [0, 2]] -= offset_x
            boxes[:, [1, 3]] -= offset_y
            boxes /= ratio
            boxes = boxes.clip(
                [0, 0, 0, 0],
                [
                    original.shape[1] - 1,
                    original.shape[0] - 1,
                    original.shape[1] - 1,
                    original.shape[0] - 1,
                ],
            )

        annotated = original.copy()
        detections = []
        for (x1, y1, x2, y2), score, class_id_value in zip(
            boxes, confidence, class_ids
        ):
            class_id = int(class_id_value)
            class_name = (
                COCO80[class_id] if 0 <= class_id < len(COCO80) else str(class_id)
            )
            detections.append(
                {
                    "class_id": class_id,
                    "class_name": class_name,
                    "confidence": float(score),
                    "bbox_xyxy": [float(x1), float(y1), float(x2), float(y2)],
                }
            )
            if save_visual:
                cv2.rectangle(
                    annotated,
                    (int(x1), int(y1)),
                    (int(x2), int(y2)),
                    (0, 255, 0),
                    2,
                )
                cv2.putText(
                    annotated,
                    f"{class_name} {score:.2f}",
                    (int(x1), max(0, int(y1) - 5)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2,
                )

        result = {
            "image": str(image_path),
            "model": str(self.model_path),
            "num_detections": len(detections),
            "detections": detections,
            "elapsed_sec": time.perf_counter() - started,
            "annotated_image": None,
            "json_result": None,
        }

        if save_visual:
            destination = (
                Path(output_dir).expanduser().resolve()
                if output_dir is not None
                else image_path.parent
            )
            destination.mkdir(parents=True, exist_ok=True)
            output_stem = f"{image_path.stem}_{output_suffix}"
            output_image = destination / f"{output_stem}.jpg"
            output_json = destination / f"{output_stem}.json"
            if not cv2.imwrite(str(output_image), annotated):
                raise OSError(f"Failed to save annotated image: {output_image}")
            result["annotated_image"] = str(output_image)
            result["json_result"] = str(output_json)
            with output_json.open("w", encoding="utf-8") as stream:
                json.dump(
                    result,
                    stream,
                    ensure_ascii=False,
                    indent=2,
                    default=_json_default,
                )

        return result


def detect_objects(image_path: str | Path, model_path: str | Path, **kwargs) -> dict:
    """Compatibility helper for one-shot use; persistent code should use the class."""
    return YoloObjectDetector(model_path).detect(image_path, **kwargs)
