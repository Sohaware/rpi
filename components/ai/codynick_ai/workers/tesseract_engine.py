"""Persistent Python wrapper around the original CodyNick Tesseract OCR."""

from __future__ import annotations

import json
import shutil
import time
from collections import OrderedDict
from pathlib import Path

import cv2
import numpy as np
import pytesseract
from pytesseract import Output


LANGUAGE_CODES = {
    "en": "eng", "fr": "fra", "es": "spa",
    "de": "deu", "it": "ita", "pt": "por",
}


def auto_document_perspective(image):
    """Warp the largest document-like quadrilateral; otherwise return unchanged."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(cv2.GaussianBlur(gray, (5, 5), 0), 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    minimum_area = image.shape[0] * image.shape[1] * 0.20
    for contour in sorted(contours, key=cv2.contourArea, reverse=True)[:20]:
        if cv2.contourArea(contour) < minimum_area:
            break
        perimeter = cv2.arcLength(contour, True)
        polygon = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
        if len(polygon) != 4:
            continue
        points = polygon.reshape(4, 2).astype(np.float32)
        ordered = np.zeros((4, 2), dtype=np.float32)
        sums = points.sum(axis=1)
        differences = np.diff(points, axis=1).reshape(-1)
        ordered[0] = points[np.argmin(sums)]
        ordered[2] = points[np.argmax(sums)]
        ordered[1] = points[np.argmin(differences)]
        ordered[3] = points[np.argmax(differences)]
        top_left, top_right, bottom_right, bottom_left = ordered
        width = int(max(
            np.linalg.norm(bottom_right - bottom_left),
            np.linalg.norm(top_right - top_left),
        ))
        height = int(max(
            np.linalg.norm(top_right - bottom_right),
            np.linalg.norm(top_left - bottom_left),
        ))
        if width < 100 or height < 100:
            continue
        destination = np.array(
            [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]],
            dtype=np.float32,
        )
        transform = cv2.getPerspectiveTransform(ordered, destination)
        return cv2.warpPerspective(image, transform, (width, height)), True
    return image, False


class TesseractOcrEngine:
    def __init__(
        self,
        languages: list[str],
        *,
        model_name: str = "fast",
        tessdata_directory: str | Path | None = None,
    ):
        started = time.perf_counter()
        executable = shutil.which("tesseract")
        if not executable:
            raise RuntimeError("Tesseract is not installed. Install tesseract-ocr.")
        pytesseract.pytesseract.tesseract_cmd = executable
        self.model_name = model_name
        self.tessdata_directory = (
            Path(tessdata_directory).expanduser().resolve()
            if tessdata_directory
            else None
        )
        if self.tessdata_directory and not self.tessdata_directory.is_dir():
            raise RuntimeError(
                f"Tesseract {model_name} model directory is missing: "
                f"{self.tessdata_directory}"
            )
        self.tessdata_config = (
            f'--tessdata-dir "{self.tessdata_directory}"'
            if self.tessdata_directory
            else ""
        )
        self.languages = languages
        self.tesseract_languages = [
            LANGUAGE_CODES.get(language, language) for language in languages
        ]
        installed = set(pytesseract.get_languages(config=self.tessdata_config))
        missing = [code for code in self.tesseract_languages if code not in installed]
        if missing:
            raise RuntimeError("Missing Tesseract language data: " + ", ".join(missing))
        self.language_argument = "+".join(self.tesseract_languages)
        self.load_seconds = time.perf_counter() - started

    def read_text(
        self,
        image_path: str | Path,
        *, confidence: float = 0.30,
        page_mode: int = 6,
        engine_mode: int = 3,
        preprocessing: str = "none",
        perspective: str = "none",
        min_characters: int = 1,
        min_box_height: int = 0,
        allowlist: str | None = None,
        save_visual: bool = True,
        output_dir: str | Path | None = None,
        output_suffix: str = "ocr",
    ) -> dict:
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if not 0 <= int(page_mode) <= 13:
            raise ValueError("page_mode must be between 0 and 13")
        if not 0 <= int(engine_mode) <= 3:
            raise ValueError("engine_mode must be between 0 and 3")
        preprocessing = str(preprocessing).strip().lower()
        if preprocessing not in {"none", "scene", "document"}:
            raise ValueError("preprocessing must be: none, scene, or document")
        perspective = str(perspective).strip().lower()
        if perspective not in {"none", "auto"}:
            raise ValueError("perspective must be: none or auto")
        min_characters = max(1, int(min_characters))
        min_box_height = max(0, int(min_box_height))
        if allowlist is not None:
            allowlist = str(allowlist)
            if not allowlist or any(character.isspace() for character in allowlist):
                raise ValueError("allowlist must be a non-empty string without spaces")

        started = time.perf_counter()
        image_path = Path(image_path).expanduser().resolve()
        image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError(f"Failed to read image: {image_path}")
        perspective_applied = False
        if perspective == "auto":
            image, perspective_applied = auto_document_perspective(image)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        scale = 1.0
        processed = gray
        annotated = image.copy()
        if preprocessing in {"scene", "document"}:
            scale = 2.0
            processed = cv2.resize(
                gray,
                None,
                fx=scale,
                fy=scale,
                interpolation=cv2.INTER_CUBIC,
            )
            annotated = cv2.resize(
                image,
                None,
                fx=scale,
                fy=scale,
                interpolation=cv2.INTER_CUBIC,
            )
        if preprocessing == "scene":
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            processed = clahe.apply(processed)
            blurred = cv2.GaussianBlur(processed, (0, 0), 1.2)
            processed = cv2.addWeighted(processed, 1.8, blurred, -0.8, 0)
        elif preprocessing == "document":
            processed = cv2.GaussianBlur(processed, (3, 3), 0)
            processed = cv2.adaptiveThreshold(
                processed,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                31,
                15,
            )
            annotated = cv2.cvtColor(processed, cv2.COLOR_GRAY2BGR)
        tesseract_config = (
            f"{self.tessdata_config} --oem {int(engine_mode)} "
            f"--psm {int(page_mode)}"
        ).strip()
        if allowlist:
            tesseract_config += f" -c tessedit_char_whitelist={allowlist}"
        data = pytesseract.image_to_data(
            processed,
            lang=self.language_argument,
            config=tesseract_config,
            output_type=Output.DICT,
        )

        items = []
        lines: OrderedDict[tuple[int, int, int], list[str]] = OrderedDict()
        threshold = confidence * 100.0
        for index, raw_text in enumerate(data.get("text", [])):
            text = str(raw_text).strip()
            try:
                score_percent = float(data["conf"][index])
            except (TypeError, ValueError):
                score_percent = -1.0
            if not text or score_percent < threshold:
                continue
            x = int(data["left"][index]); y = int(data["top"][index])
            width = int(data["width"][index]); height = int(data["height"][index])
            if len(text) < min_characters or height < min_box_height:
                continue
            items.append({
                "text": text,
                "confidence": score_percent / 100.0,
                "box_xywh": [x, y, width, height],
            })
            key = (
                int(data["block_num"][index]),
                int(data["par_num"][index]),
                int(data["line_num"][index]),
            )
            lines.setdefault(key, []).append(text)
            if save_visual:
                cv2.rectangle(annotated, (x, y), (x + width, y + height), (0, 255, 0), 2)

        result = {
            "image": str(image_path), "engine": "tesseract",
            "model_name": self.model_name,
            "preprocessing": preprocessing,
            "processing_scale": scale,
            "perspective": perspective,
            "perspective_applied": perspective_applied,
            "min_characters": min_characters,
            "min_box_height": min_box_height,
            "allowlist": allowlist,
            "languages": self.languages,
            "tesseract_languages": self.tesseract_languages,
            "page_mode": int(page_mode), "engine_mode": int(engine_mode),
            "text": "\n".join(" ".join(words) for words in lines.values()),
            "num_text_regions": len(items), "items": items,
            "elapsed_sec": time.perf_counter() - started,
            "annotated_image": None, "json_result": None,
        }
        if save_visual:
            destination = Path(output_dir).expanduser().resolve() if output_dir else image_path.parent
            destination.mkdir(parents=True, exist_ok=True)
            stem = f"{image_path.stem}_{output_suffix}"
            output_image = destination / f"{stem}.jpg"
            output_json = destination / f"{stem}.json"
            if not cv2.imwrite(str(output_image), annotated):
                raise OSError(f"Failed to save annotated image: {output_image}")
            result["annotated_image"] = str(output_image)
            result["json_result"] = str(output_json)
            output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        return result
