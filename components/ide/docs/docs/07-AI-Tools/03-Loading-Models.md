# Loading AI Applications and Models

```python
result = ai.load_app(
    app,
    model=None,
    languages=None,
    language=None,
    preload=None,
)
```

Configuration is keyword-only after `app`. Loading the already-active configuration
returns status with `already_loaded=True` instead of starting another worker.

## YOLO object detection

```python
ai.load_app("yolo", model="nano")
```

Installed model choices: `nano`, `small`, `medium`. Nano is fastest and uses the least
memory. Small and medium can take longer and use substantially more RAM.

## OCR

```python
ai.load_app("ocr", model="standard", languages=["en"])
```

Model choices: `fast`, `standard`, `best`. The current package installs English.
`languages` accepts a string or sequence of Tesseract language codes, but a requested
language works only when its data is installed.

## Speech-to-text

```python
ai.load_app("stt", model="small", language="en")
```

The controller recognizes `small` and `large` models and language keys `en`, `de`,
`fa`, and `ar-tn`; this release installs only the small English model. Requesting a
recognized but uninstalled combination raises `AppLoadError`.

## Text-to-speech

```python
status = ai.load_app("tts", model="fast", language="en")
if not status["ok"]:
    print(status["error_code"], status["message"])
```

Installed choices are English `fast` or its alias `default`, using `speaker1`. Unlike
the other loaders, expected TTS errors are returned as `{ok: False, error_code,
message, ...}` rather than raised.

`preload` is reserved metadata passed through the load result; it does not install
additional models.

