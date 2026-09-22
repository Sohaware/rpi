# Object Detection Reference

Load YOLO before detection:

```python
ai.load_app("yolo", model="nano")
```

## `detect_objects()`

```python
result = ai.detect_objects(
    image=None,
    confidence=0.35,
    iou=0.5,
    save_visual=True,
    output_suffix="objects",
)
```

| Parameter | Meaning |
| --- | --- |
| `image` | Saved image name; `None` selects `current.jpg` |
| `confidence` | Minimum detection score, normally `0.0..1.0` |
| `iou` | Non-maximum-suppression overlap threshold |
| `save_visual` | Save annotated JPG and JSON |
| `output_suffix` | Suffix added to result filenames |

The returned dictionary contains:

```python
{
    "image": "/home/client/images/photo.jpg",
    "model": "...model path...",
    "num_detections": 2,
    "detections": [
        {
            "class_id": 0,
            "class_name": "person",
            "confidence": 0.87,
            "bbox_xyxy": [x1, y1, x2, y2],
        }
    ],
    "elapsed_sec": 0.42,
    "annotated_image": "/home/client/images/results/photo_objects.jpg",
    "json_result": "/home/client/images/results/photo_objects.json",
}
```

When `save_visual=False`, both output paths are `None`. Coordinates are image pixels.
Reducing confidence returns more uncertain detections; increasing it returns fewer.

```python
people = [item for item in result["detections"]
          if item["class_name"] == "person"]
print("People:", len(people))
```

