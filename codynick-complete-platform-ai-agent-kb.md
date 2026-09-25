# CodyNick Complete Platform Knowledge Base for AI Agents
Purpose: compact source-grounded reference for generating Python programs on the installed CodyNick Raspberry Pi platform. Scope: CodyNick gadgets, controller Wi-Fi/cloud I/O, local Dashboard, USB camera, object detection, OCR, audio, speech-to-text, live voice commands, text-to-speech, files, errors, and lifecycle. Target release family: CodyNick 0.7.x. Prefer APIs below over direct serial, database, camera, ALSA, worker, or filesystem manipulation.

## 1. Core rules
- User script: `/home/client/active_script.py`; examples: `/home/client/CodyNick examples`; images: `/home/client/images`; vision/OCR results: `/home/client/images/results`; audio: `/home/client/audio`; STT/TTS results: `/home/client/audio/results`; logs: `/home/client/logs`.
- Hardware import: `import CodyNick`; connection: `cody=CodyNick.CN()`. Production guard: `if not cody.ensure_connected(): raise RuntimeError("CodyNick gadget not found.")`. Reuse one `cody`; finish with `cody.close()`.
- AI import: `from codynick_ai import CodyNickAI`; controller: `ai=CodyNickAI()`. Only one worker app (`yolo|ocr|stt|tts`) is active per controller. Load once, perform related work, then `ai.unload_app()` or `ai.close()`.
- Safe combined cleanup: `try: ... finally: ai.close(); CodyNick.RGB_Matrix.clear(cody); cody.close()`. `ai.close()` also closes camera, stops listening, and unloads worker.
- Sensor/communication failure generally returns `None`/`False`/`[]`; test before using. AI operations generally raise `CodyNickAIError` subclasses; TTS load/generation/playback normally return `{ok,error_code,message,...}`.
- In repeated loops use a small delay (`time.sleep(0.05)` or suitable sampling period). For setting many RGB LEDs, allow about `0.002` s between `set()` calls.
- Use stable media names to overwrite previous files and avoid junk. Names: letters/digits/underscore/hyphen; no path. Image `.jpg` optional; audio `.wav|.mp3|.m4a` optional.

## 2. Minimal skeletons
Hardware: `import time,CodyNick;cody=CodyNick.CN();assert cody.ensure_connected();...;cody.close()`.
AI: `from codynick_ai import CodyNickAI;ai=CodyNickAI();ai.load_app("yolo",model="nano");...;ai.close()`.
Camera with CodyJoy sounds: `path=ai.take_picture("photo",cody=cody,get_ready_sound=True)`; default `keep_open=False` releases camera immediately.
Dashboard: `import Dashboard;card=Dashboard.Card("gauge","Temperature",min_value=0,max_value=50,value=0);card.set(24.5);card.delete()`.

## 3. CodyNick connection/support APIs
`CodyNick.CN()` auto-detects USB serial (`/dev/ttyUSB*` or `/dev/ttyACM*`) and validates CodyJoy Pro identity. `cody.ensure_connected()->bool`; `cody.mark_disconnected()`; `cody.record_io_success()`; `cody.record_io_failure()`; `cody.close()`.
Low-level, normally avoid: `cody.serial.flush()`; `send_line(text,add_newline=False)`; `read_line(timeout=1.0,max_bytes=64,inter_char_timeout=0.05)->str|None`; `close_serial()`.
Utilities: `CodyNick.log(x)` timestamped output; `CodyNick.UpdateLib()` updates legacy library; `Memory.sync()`; `HID.get()`, `HID.clear()`, `HID.len()`.

## 4. RGB matrix (CodyJoy Pro 4x4)
`CodyNick.RGB_Matrix.set(cody,led,color)` where `led=0..15`; physical sequence bottom-to-top: `15 14 13 12 / 8 9 10 11 / 7 6 5 4 / 0 1 2 3`. `CodyNick.RGB_Matrix.set_xy(cody,x,y,color)` where `x,y=0..3`; `(0,0)` is bottom-left. `CodyNick.RGB_Matrix.clear(cody)`.
Color accepts palette integer, hex, or percentage RGB list: `0=red,1=cyan,2=blue,3=yellow,4=magenta,5=green,6=orange,7=white`; `"#RRGGBB"`; `[R,G,B]` each `0..100`. Examples: `set(cody,0,"#00FF00")`; `set_xy(cody,2,1,[100,0,50])`.

## 5. Joysticks
Devices: `"CJP"` (built-in) or `"Stand-Alone"`; numeric supported codes `0..5` are accepted but names are preferred. `CodyNick.Joystick.position(cody,device,pos)->bool`, `pos="up"|"down"|"left"|"right"` (lowercase). `CodyNick.Joystick.click(cody,device)->bool`. `CodyNick.Joystick.states(cody,device)->list[str]`, members `UP|DOWN|LEFT|RIGHT|CLICK`, possibly combined; failure/neutral `[]`.

## 6. LED matrix (monochrome 8x8)
`CodyNick.LED_Matrix.display_text(cody,text,speed=1)`; speed `0|1|2|"slow"|"medium"|"fast"`. `set_pixel(cody,x,y,state)` where `x,y=0..7`, state bool/0/1. `on(cody,x,y)`; `off(cody,x,y)`; `clear(cody)`.

## 7. CodyJoy Pro sound maker
`CodyNick.CJP_Sound_Maker.play(cody,note,duration_ms)` starts note and continues. `play_until_done(cody,note,duration_ms)` waits. Note string range `B0..D#8`; sharps/flats accepted, e.g. `"C5"`, `"F#5"`, `"Gb5"`; duration `1..99999` ms. Melody: loop over `(note,ms)` and call `play_until_done`.

## 8. Displays and sensors
Seven segment: `CodyNick.Seven_Segment.display(cody,device,value)`; device `"Stand-Alone"|"UltraSeg"`; value number or numeric string. Do not use `"CJP"`. Stand-alone examples: `25`, `-123`; UltraSeg supports values such as `1.234`.
Temperature: `CodyNick.Temperature_Sensor.read(cody)->float|None`, Celsius.
Soil moisture: `CodyNick.Soil_Moisture_Sensor.read(cody)->float|None`.
Motion/PIR: `CodyNick.Motion_Detection.detect(cody)->bool`.
RFID: `CodyNick.RFID_Reader.readuid(cody)->str|None`.
Ultrasonic: `CodyNick.Ultrasonic_Sensor.read(cody,device)->float|None`, device `"Stand-Alone"|"UltraSeg"`, result centimeters.
Keypad: `CodyNick.Keypad.get()->key` (legacy interface).
Legacy `Sensors`: `temp_sensor_reading()`, `light_sensor_reading()`, `gas_sensor_reading()`, `soilhumidity_reading()`, `flow_sensor_reading()`, `ultrasonic_distance_reading()`; prefer dedicated classes above when available.

## 9. Controller Wi-Fi and IoT cloud
Credential strings must be ASCII and at most 40 characters. Setters return bool: `set_ssid(cody,ssid)`, `set_password(cody,password)`, `set_cloud_mode(cody,mode)`, `set_username(cody,username)`, `set_device_id(cody,device_id)`, `set_device_key(cody,device_key)`. Combined: `set_wifi(cody,ssid,password)->bool`; `set_iot(cody,username,device_id,device_key,cloud_mode=1)->bool`.
Control: `restart(cody)->bool`; `reset_wifi(cody)->bool`; `reset_iot(cody)->bool`; `reset(cody)` if exposed by installed revision. A successful reset means request accepted, not connection established.
Status: `status(cody)->{"wifi":int,"iot":int}|None`; `wifi_status(cody)->int|None`; `iot_status(cody)->int|None`; `wifi_connected(cody)->bool` (`wifi==3`); `iot_connected(cody)->bool` (`iot==1`).
Stored credentials: `credential_state(cody,step)->str|None`, steps `0:ssid,1:password,2:device_id,3:device_key,4:username,5:ESP_version,6:STM_version,7:library_version`; named getters: `get_ssid`/`get_wifi_ssid`, `get_password`/`get_wifi_password`, `get_device_id`, `get_device_key`, `get_username`, `get_esp_version`, `get_stm_version`, `get_library_version`/`get_lib_version`. Never log secrets.
Keep alive (call repeatedly in paced loop): `keep_alive_wifi(cody,ssid,password,Trst=15,Tchk=10,Tstartup=10)->bool`; `keep_alive_iot(cody,username,device_id,device_key,cloud_mode=1,Trst=15,Tchk=10,Tstartup=10)->bool`. `Tstartup`: initial connection allowance; `Tchk`: status interval; `Trst`: retry/reset timing.
Cloud values: index `0..3`; types `int|integer|float|bool|boolean|string|str`. `write(cody,index,type,value,verify=True)->bool`; `read(cody,index,type)->int|float|bool|str|None`. Typed: `write_int`, `write_float`, `write_bool`, `write_string` (optional `verify`); `read_int`, `read_float`, `read_bool`, `read_string`. Protocol settling is about `0.25` s; float verification tolerance `0.01`; string verification is limited by controller protocol (first six characters), so avoid relying on long-string verification.

## 10. Local Dashboard
Installed DB is normally preconfigured; just `import Dashboard`. Optional override: `Dashboard.configure(host="localhost",user="codynick",password="codynick",database="codynick",port=3306)`. Maintenance: `ensure_database()`, `ensure_table()`, `clear()`.
Constructor: `Dashboard.Card(card_type,title,color="blue",min_value=None,max_value=None,value=None,description=None,*,auto_delete=True)`. Types: `led,gauge,textarea,info,button,switch,slider,graph,table,bar,pie`; custom type strings may be stored. Attributes: `id,type,title,color,min_value,max_value,value,description,auto_delete`.
Methods: `card.set(value,save=True)` updates local value and normally DB; `card.save()->None`; `card.sync()->bool` pulls current DB/UI values and reports whether row exists; `card.delete()`; `card.value_json()`; context manager supported (`with Card(...) as card:`). `auto_delete=True` removes card at normal cleanup; set false for persistence.
Values: led/button/switch bool; gauge/slider numeric with min/max; textarea/info text; graph list (`[12,14]`), point map (`{0:12,5:14}`), or series map (`{"room1":[...]}`); bar/pie category map (`{"A":4,"B":7}`); table structured object, commonly `{"columns":[...],"rows":[[...],...]}`. For UI controls call `sync()` in loop before reading `value`; detect button edges instead of repeating while held.

## 11. AI controller and model loading
`ai=CodyNickAI(camera_index=0,...)`; normally omit advanced path overrides. Properties: `active_app:str|None`, `active_model:str|None`, `camera_is_open:bool`, `listening_is_active:bool`.
`ai.load_app(app,*extra,model=None,languages=None,language=None,preload=None,**options)`. Apps/models: YOLO `app="yolo"`, models `nano|small|medium` (nano fastest); OCR `app="ocr"`, models `fast|standard|best`, languages list such as `["en"]`; STT `app="stt"`, models `small|large`, language keys `en|de|fa|ar-tn` but installed baseline is small English; TTS `app="tts"`, model `fast|default`, language `en`, speaker `speaker1`. Missing optional model payload raises/returns load failure. Loading another app unloads the previous worker. `ai.unload_app()`; `ai.close()`.

## 12. Camera and image storage
`ai.open_camera(width=1280,height=720,fps=30,use_mjpeg=True,warmup_seconds=3.0,warmup_frames=15)->dict`; result contains camera index, measured warm-up, valid frame count, actual dimensions/FPS/format; already-open result has `already_open=True`.
`ai.take_picture(name=None,*,warmup_seconds=3.0,warmup_frames=15,capture_mode="brightest",burst_frames=12,cody=None,get_ready_sound=False,keep_open=False)->absolute_path`. Modes `brightest|sharpest|last`; `sharpest` uses burst candidates. Every capture replaces `images/current.jpg`; named capture also replaces `images/<name>.jpg`. Pass connected `cody` plus `get_ready_sound=True` for CodyJoy ready/shutter cues. One-shot default releases camera; for repeated capture use `keep_open=True` and always `ai.close_camera()` in `finally`.
Storage: `close_camera()`; `save_picture("name")->path` copies current; `list_pictures()->sorted list[str]` without extension; `picture_exists(name_or_None)->bool`; `delete_picture(name)`.

## 13. Object detection
Load: `ai.load_app("yolo",model="nano")`. Call: `detect_objects(image=None,*,confidence=.35,iou=.5,save_visual=True,output_suffix="objects")->dict`; `image=None` uses current. Result: `{"image":path,"model":path,"num_detections":N,"detections":[{"class_id":int,"class_name":str,"confidence":float,"bbox_xyxy":[x1,y1,x2,y2]}],"elapsed_sec":float,"annotated_image":path|None,"json_result":path|None}`. Coordinates are pixels. Lower confidence yields more/less-certain detections. `save_visual=False` makes output paths `None`.

## 14. OCR
Load: `ai.load_app("ocr",model="standard",languages=["en"])`. Call: `read_text(image=None,*,confidence=.3,page_mode=6,engine_mode=3,preprocessing="none",perspective="none",min_characters=1,min_box_height=0,allowlist=None,save_visual=True,output_suffix="ocr")->dict`. `preprocessing=none|scene|document`; `perspective=none|auto`; confidence `0..1`; page mode 6 assumes uniform text block. Result includes `text:str`, `items:list`, settings/timing, `annotated_image`, `json_result`; each item includes `text`, normalized `confidence`, `box_xywh`. Use `scene` for signs/objects; `document` for high-contrast pages; `allowlist` restricts recognized characters.

## 15. Audio recording and files
`record_audio(name=None,*,duration=5,device="auto",sample_rate=16000)->path`; mono 16-bit WAV; duration integer `1..300`; sample rate `8000..48000`. Device: `auto` prefers webcam/USB capture; `webcam` requires webcam-named ALSA input; explicit ALSA `plughw:CARD,DEVICE` accepted. Every recording replaces `audio/current.wav`; named output also persists.
`list_audio()->list[str]` including extensions; `audio_exists(name)->bool`; `delete_audio(name)`.

## 16. Speech-to-text and live commands
Load: `ai.load_app("stt",model="small",language="en")`.
File STT: `transcribe(audio=None,*,mode="free",commands=None,min_confidence=0.0,output_suffix="stt",save_json=True)->dict`; audio None=current; mode `free|commands`; command mode normalizes text and requires exact command match plus threshold. Result keys: `text,accepted,matched_command,confidence,words,audio_duration_sec,transcription_sec,json_result`; each word has `word,confidence,start_sec,end_sec`.
Live: `listener=ai.listen(*,commands=None,min_confidence=0.0,device="auto")`; nonempty commands enables command mode, None free speech. `listener.active`; `listener.get(timeout=0.0)->event|None`; `listener.stop()`; iterable (`for event in listener`). Event: `{"type":"speech","text":str,"accepted":bool,"matched_command":str|None,"confidence":float,"words":[...],"received_at":ISO_str}`. Always stop in `finally`; `ai.close()` also stops it.

## 17. Text-to-speech and playback
Load: `status=ai.load_app("tts",model="fast",language="en")`; check `status["ok"]`. Generate once: `ai.tts(text,name,*extra,speaker="speaker1",volume=100,**options)->dict`; text length `1..1000`; required stable name; volume `0..300`. Success keys: `ok=True,error_code="OK",audio_file,current_audio,audio_duration_sec,synthesis_sec,speaker,volume,json_result`; expected validation/runtime failure: `ok=False,error_code,message`.
Replay without loading TTS: `ai.speak(name,*extra,device="auto",volume=100,**options)->dict`; accepts WAV/MP3/M4A; converts/caches 48-kHz stereo WAV at requested volume; auto prefers USB output. Success includes `audio_file,playback_file,playback_cache_reused,device,volume,playback_sec`. Common errors: `AUDIO_NOT_FOUND,NO_PLAYBACK_DEVICE,AUDIO_CONVERSION_FAILED,PLAYBACK_TIMEOUT,PLAYBACK_FAILED`. Prefer generating fixed messages once and replaying later.

## 18. AI exceptions
`from codynick_ai import CodyNickAIError,AppLoadError,AppNotLoadedError,WorkerCrashedError,CameraNotAvailableError,NoImageError,PictureNameError,PictureNotFoundError,NoAudioError,AudioNameError,AudioNotFoundError`. All listed inherit `CodyNickAIError`. Invalid Python arguments may raise `ValueError|TypeError`. TTS paths usually return structured failure instead. Agent rule: catch only where recovery is meaningful; report `error_code/message`; always clean resources in `finally`.

## 19. Compact composition recipes
Temperature display: `t=CodyNick.Temperature_Sensor.read(cody); CodyNick.Seven_Segment.display(cody,"Stand-Alone",round(t,1)) if t is not None else None`.
All RGB LEDs: `for led in range(16): CodyNick.RGB_Matrix.set(cody,led,"#00FF00"); time.sleep(.002)`.
Joystick event: `states=CodyNick.Joystick.states(cody,"CJP"); if "UP" in states: ...`.
Camera-to-YOLO: `ai.take_picture("camera",cody=cody,get_ready_sound=True);ai.load_app("yolo",model="nano");r=ai.detect_objects("camera")`.
Camera-to-OCR: `ai.take_picture("ocr",cody=cody,get_ready_sound=True);ai.load_app("ocr",model="standard",languages=["en"]);r=ai.read_text("ocr",preprocessing="scene")`.
Voice command: `ai.load_app("stt",model="small",language="en");listener=ai.listen(commands=["red","green","blue","lights off"],min_confidence=.6)`; react only when `event["accepted"]`.
Cloud sensor: ensure Wi-Fi/IoT keep-alive succeeds, then `write_float(cody,0,t)`; throttle loop.
Dashboard sensor: create once, then `card.set(t)`; do not create a new card every sample.

## 20. Agent generation checklist
1. Identify required hardware names exactly (`CJP`, `Stand-Alone`, `UltraSeg`); never infer that CJP contains a seven-segment display.
2. Create one hardware and one AI controller at most; do not reopen serial/camera/model per loop iteration.
3. Validate `None|False|[]` before arithmetic/branching; validate structured `ok` for TTS.
4. Use stable media/output names; use current files only when overwrite semantics are intended.
5. Pass `cody` and `get_ready_sound=True` for camera cue requirements.
6. Leave camera closed after one-shot captures; stop listener; clear outputs when appropriate; close controllers.
7. Use official Dashboard/IoT APIs rather than SQL or raw serial.
8. Keep beginner demos linear only when explicitly requested; production scripts should use `try/finally` cleanup.
9. Do not claim uninstalled models/features. Baseline documented AI: YOLO object detection, Tesseract OCR, English Vosk STT/live commands, English Coqui TTS/playback. Face detection/recognition, age/race analysis, and chapter-8 features are not part of this release unless separately installed.
