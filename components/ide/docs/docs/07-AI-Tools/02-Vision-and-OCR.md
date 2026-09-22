# Object Detection and OCR

## Objects

```python
ai.load_app("yolo", model="nano")
result = ai.detect_objects("camera_objects", confidence=0.35)
for item in result["detections"]:
    print(item["class_name"], item["confidence"])
```

Higher confidence rejects uncertain detections. Larger YOLO models can require more
memory and time; they do not guarantee a better answer for every image.

## English text

```python
ai.load_app("ocr", model="standard", languages=["en"])
result = ai.read_text(
    "camera_text",
    confidence=0.20,
    preprocessing="scene",
    perspective="auto",
    save_visual=True,
)
print(result["text"])
```

Lower OCR confidence includes more uncertain text; higher confidence produces fewer,
more selective results. Use large printed text, even lighting, a steady camera, and a
front-facing page. Annotated images and JSON results are stored in `images/results`.

