# OCR Reference

```python
ai.load_app("ocr", model="standard", languages=["en"])
```

## `read_text()`

```python
result = ai.read_text(
    image=None,
    confidence=0.30,
    page_mode=6,
    engine_mode=3,
    preprocessing="none",
    perspective="none",
    min_characters=1,
    min_box_height=0,
    allowlist=None,
    save_visual=True,
    output_suffix="ocr",
)
```

| Parameter | Meaning |
| --- | --- |
| `image` | Saved image name; `None` selects `current.jpg` |
| `confidence` | Minimum normalized word confidence (`0.0..1.0`) |
| `page_mode` | Tesseract page segmentation mode; `6` assumes one uniform text block |
| `engine_mode` | Tesseract OCR engine mode; installed default is `3` |
| `preprocessing` | `none`, `scene`, or `document` |
| `perspective` | `none` or `auto` perspective correction |
| `min_characters` | Reject shorter recognized items |
| `min_box_height` | Reject text boxes shorter than this pixel height |
| `allowlist` | Optional string of permitted characters |
| `save_visual` | Save annotated JPG and JSON result |
| `output_suffix` | Result filename suffix |

The result includes `text`, `items`, timing/settings fields, `annotated_image`, and
`json_result`. Each item contains recognized text, normalized confidence, and its box.

```python
print(result["text"])
for item in result["items"]:
    print(item["text"], item["confidence"], item["box_xywh"])
```

Use `scene` for signs and objects photographed in a room. Use `document` for a
high-contrast page with adaptive thresholding. Lower confidence keeps more uncertain words. OCR quality also
depends on focus, lighting, text size, orientation, and perspective.
