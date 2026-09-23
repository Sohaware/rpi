# Changelog

## 0.7.2-teacher-guides - Protected presenter library and release identity

- Add a password-protected offline teacher portal at `/teachers/`, with the initial
  login `teacher` / `codynick` and an administrator command for changing its password.
- Add the first progressive live-coding guide, building a temperature alarm through
  LED, blink, seven-segment, counter, sensor, color, melody, and joystick-inhibit steps.
- Preserve changed teacher credentials during installation, repair, and upgrades.
- Display the installed software version and real release date on `start.codynick`.
- Make application release state readable so `codynick-version` works without `sudo`.
- Verify that the main page carries current release identity and that teacher pages
  reject unauthenticated requests.

## 0.7.1-api-reference - Complete IoT and AI programming reference

- Document the local Dashboard module's database functions, complete `Card` constructor,
  attributes, methods, lifecycle, all eleven card types, accepted structured values,
  browser interaction patterns, and race/cleanup considerations.
- Document every public `CodyNick.WiFi_IoT` connection, credential, keep-alive, status,
  reset, typed cloud read, and typed cloud write command with limits and return values.
- Document the `CodyNickAI` constructor, model loading, camera/image storage, object
  detection, OCR, audio recording, STT, live commands, TTS/playback, result dictionaries,
  exceptions, output paths, and resource lifecycle.
- Clearly distinguish API-supported model/language keys from the English models actually
  installed in this release.

## 0.7.0-offline-docs-camera - Offline learning guide and camera cleanup

- Replace generic on-device pages with an offline guide for the main panel, Python
  IDE, Blockly, gadgets, dashboard/IoT, camera/media, installed AI tools, examples,
  updates, and troubleshooting.
- Store the working gadget illustrations on the Pi and bundle Blockly locally so the
  linked learning tools no longer depend on public CDNs during normal use.
- Release the webcam automatically after ordinary one-shot captures. Require repeated
  capture programs to opt into `keep_open=True` and close the camera after the loop.
- Configure the student-script service to send `SIGINT` before its ten-second stop
  timeout, allowing Python `finally` cleanup during IDE-triggered restarts.

## 0.6.1-tts-permissions - Repair restored TTS ownership

- Assign the managed TTS environment, English model, and vocoder cache to `client`
  after every restore. Coqui rewrites cached configuration paths during model loading,
  so read-only root ownership caused the 0.6.0 health check to fail.
- Reuse the verified 0.6.0 release assets and cache. Rerunning the unified setup command
  repairs an interrupted 0.6.0 installation without downloading those assets again.

## 0.6.0-tts - Offline speech generation and reusable audio

- Package the approved-image ARM64 Coqui TTS 0.22 environment, English Glow-TTS
  model, and MultiBand-MelGAN vocoder as versioned SHA256-checked release assets.
- Limit the first supported TTS release to the tested fast English voice. Install and
  load-check its model without synthesizing speech during setup.
- Add `create_speech_file.py` to generate a named WAV once and preserve it in
  `/home/client/audio`. It does not overwrite an existing recording automatically.
- Add `play_saved_audio.py` to replay that saved file without loading or running the
  TTS worker. Cache the 48 kHz stereo conversion privately and reuse it while the
  source file and requested volume are unchanged.
- Add audio listing, existence, and deletion helpers to the controller. Preserve the
  Audio folder, student files, and prior AI assets during installation and repair.
- Add archive-safety, repeat-restore, and generate-once/play-many tests. Face features,
  chapter 8, configurable uplinks, dongle reconciliation, and swap remain deferred.

## 0.5.3-examples-polish - Managed demos and clear version status

- Treat `/home/client/userfiles/CodyNick examples` as system-owned. Before every
  installation, repair, or upgrade, copy its old contents into the release backup,
  remove the complete live folder, and install only the current example set.
- Replace random camera image names with stable per-demo names, so repeated runs
  overwrite prior inputs, annotated images, and JSON results. Model comparison keeps
  one stable output per model.
- Set OCR demo confidence through `OCR_CONFIDENCE` (default `0.20`). Add adjustable
  `MATCH_SIMILARITY` (default `0.80`) so the joystick demo tolerates a small OCR error.
- Keep the joystick OCR result LEDs illuminated for five seconds, then clear them,
  including defensive cleanup after failures.
- Add `codynick-version` to report the installed release, component versions, stage,
  and checksum status (`current`, `modified`, `missing`, or `unexpected`) for every
  example. READY now requires this audit to pass.

## 0.5.2-camera-sounds - Camera countdown and shutter feedback

- Enable the established CodyJoy get-ready countdown/cue and USB-speaker shutter
  sound in all five bundled camera-capture examples: object detection, object
  counting, model comparison, camera OCR, and joystick-triggered OCR.
- Use the CodyJoy buzzer as the shutter fallback when no USB playback device is
  available or audio playback fails. Capture occurs after the cue so sound-time
  frames are discarded.
- Keep the controller API opt-in for third-party scripts. Reuse the verified 0.5.0
  vision/OCR assets and 0.4.0 speech assets. Upgrade untouched published camera
  examples while preserving student-edited copies and other user files.

## 0.5.1-ocr-led - Joystick-triggered OCR result

- Add `joystick_ocr_led.py`, a one-shot beginner demo that waits for the CodyJoy
  Pro joystick to move up before taking a USB-camera picture or starting OCR.
- Normalize recognized text for case, spaces, and punctuation. Fill all 16 RGB LEDs
  green when the result contains `codynick`; otherwise fill them red.
- Reuse the verified 0.5.0 OCR environment and model assets. Preserve existing user
  files and examples during upgrade.

## 0.5.0-ocr - Offline English camera OCR

- Package a slim, approved-image ARM64 OCR environment plus English standard and
  best Tesseract data; use Ubuntu's English data as the fast model.
- Add `camera_read_text.py`: capture from a USB webcam, apply scene preprocessing
  and optional perspective correction, print text/confidence, and save annotated
  JPG and JSON results under Images/results.
- Install and health-check Tesseract plus fast/standard/best English models without
  capturing a photo during installation. Preserve existing examples and user data.
- Reset Apache's accumulated directory-index list before selecting `index.php`, and
  fail health checks if `/` is still the Apache default page instead of CodyNick.
- Retry interrupted source and OCR-asset downloads. Release the unified setup lock
  before following the background log, so a completed/failed worker cannot leave a
  harmless log viewer blocking repair.
- Keep network component 0.1.2 and the existing Wi-Fi credentials. Configurable
  uplinks, replaced-dongle reconciliation, swap, TTS, face features, and chapter 8
  remain deferred.

## 0.4.1-setup - Reliable same-command hotspot confirmation

- Remember the network stage seen at entry. A second run begun in pending/applying
  invokes the existing confirmation flow even when sudo omits SSH_CONNECTION.
- Keep the first-run handover behavior, confirmation prompt, alternative-internet
  check, rollback timer, and pinned 0.4.0 application payload unchanged.
- Exercise the two-run clean-install flow with an empty SSH_CONNECTION value.

## 0.4.0-speech - Offline voice commands

- Package the approved ARM64 Vosk speech environment and small English model from
  the supplied Pi image as two SHA256-checked release assets.
- Install ALSA recording tools and FFmpeg; verify the model without recording audio.
  Installation reports microphones but never captures audio automatically.
- Add voice_led_colors.py: constrained offline color commands control all 16 RGB
  LEDs, print confidence scores, and clean up microphone/model/serial resources.
- Include the renamed camera, per-photo counter, and same-photo model-comparison
  demos prepared in the unpublished 0.3.1 candidate.
- Accept upgrades from 0.3.0, preserve all existing examples and user data, reuse
  the immutable 0.3.0 vision payload, and add speech archive/security/demo tests.
- OCR, text-to-speech, face features, chapter 8, and swap configuration remain deferred.

## 0.3.1-vision - Unpublished object demo candidate

- Rename the distributed camera demo to camera_objects.py; preserve the old file
  on upgraded devices because it may contain student edits.
- Add finite object_counter.py and model_comparison.py demos with cleanup,
  unique photo names, per-frame counts and same-photo sequential model timing.
- Reuse immutable 0.3.0 runtime/model assets and cache. Accept upgrades from 0.3.0.
- Add mock-based tests for demo results, missing cameras, failures and comparison.
- User confirmed 0.3.0 USB capture/default-model detection on Pi. New demos await
  hardware acceptance. Speech recognition and voice commands are the next stage.

## 0.3.0-vision - Unified entry point, USB vision, and ANSI logs

- Adds setup.sh: one public download/run command selects network preparation,
  hotspot confirmation, or application install/repair/upgrade. A fresh handover
  still requires reconnecting and rerunning the same command within 15 minutes.
- Accepts 0.2.0/0.2.1/0.2.2 and repeated 0.3.0 installs. Leaves a working hotspot
  alone; arbitrary network/OS corruption and unknown release migrations are not supported.
- Deploys allowlisted Python 3.10 ARM64, controller/YOLO environments, and three
  YOLO ONNX models from the supplied image, as SHA256-checked GitHub release assets.
  Rejects archive traversal, special files, conflicting links, and link-parent writes.
- Runs student code through the controller environment; preserves the old core
  environment on upgrades. Adds native USB-video/runtime libraries and model warmup.
- Adds a preserved USB-camera/object-detection example to the IDE. Actual camera
  capture is user-initiated; installation never captures images automatically.
- Renders ANSI foreground colors and bold through safe DOM text nodes, including
  split sequences across polls. Strips unsupported controls, bounds displayed output,
  prevents overlapping polls, and resets color state on clear/truncation/rotation.
- Adds archive-safety, ANSI rendering, and release-integrity checks. No OCR/speech/
  chapter 8 environments are deployed. Pi USB-camera acceptance remains pending.
- Records successful fresh-OS/core/IDE/RGB tests for the previous 0.2.2 baseline.

## 0.2.2-core - Test real web-user I/O

- Removes external `test -w` as a gate: 0.2.1 diagnostics showed correct modes,
  ACLs, and group membership, but this preliminary check still returned failure.
- Opens active_script.py and log.log read/write without truncating or writing their
  contents; verifies list/create/write/read/rename/delete in disposable subfolders
  inside the three shared directories, all running as www-data.
- Actual I/O failures remain fatal and retain permission diagnostics. The original
  test-command failure is not yet explained; this is not a claimed AppArmor fix.
- Allows repair from 0.2.0 and 0.2.1, with runtime and student data unchanged.
- Adds regression coverage for real access denial and absence of the external gate.
  Pi confirmation is still required.

## 0.2.1-core - Web-user permission repair

- Accepts incomplete/completed 0.2.0 installs for in-place repair; retains the
  core-0.2.0 Python environment, account passwords, student files, and database.
- Adds ACL tools and explicit www-data traversal/file/shared-folder access rather
  than relying only on mode bits and supplementary groups. No whole-home write grant.
- Checks actual non-truncating opens before application deployment and in final
  health checks. Failures print identity, path-mode, and ACL diagnostics.
- Clears stale failure text on a successful retry.
- Adds real Linux runuser/ACL tests for denied access, restrictive parents,
  repeat repair, content preservation, and inherited shared-file permissions.
- The original Pi denial's exact cause is not yet established; 0.2.0 already
  applied mode 0664. Device acceptance of this repair remains pending.

## 0.2.0-core - First core application trial

- Installs the Python IDE/live terminal, Blockly, dashboard, documentation,
  CodyNick.py 1.20.1, Dashboard.py, Apache/PHP/MariaDB, and script/watchdog services.
- Keeps verified network setup 0.1.2 untouched and runs installation independently
  of the administrator's SSH session.
- Pins source-file checksums and uses a private Python virtual environment, avoiding
  changes to Ubuntu's externally managed Python packages.
- Sets up client hardware/media permissions and limits the database grant to codynick.*.
- Preserves student data/configuration/passwords on repeats of the same version;
  rejects unreviewed legacy/version migrations and reports installation failures.
- Corrects Blockly's active-script path and adds a unique marker for repeat runs.
- Core manifest and installer versions are separate from the network version.
- Application source is based on the supplied Rev.B2 IDE package and July 11 image.
  AI environments/models and unfinished chapter 8 are not deployed in this release.
- Automated tests cover checksums, repeat-install preservation, path rejection,
  network prerequisites, and actual PHP run/log/Blockly endpoints. Hardware acceptance
  remains pending; this is not a production fleet release.

## Documentation update - 2026-09-18

- Document Imager preparation, mandatory reboot after Ubuntu first boot, SSH setup,
  hotspot confirmation, and post-reboot verification.
- Require the external codynick/codynick internet network before installation.
- Record repeated fresh-install and reboot tests on the tested Pi/dongle.
- Add release history and mark 0.1.0 and 0.1.1 superseded in README.md.
- Installer remains 0.1.2; no script changes or changes to published tags.

## 0.1.2 - Fix generated network configuration permissions

- Reset the private download umask before invoking the setup helper.
- Explicitly give subprocesses umask 022 so Netplan retains networkd group-read access.
- Keep credential YAML, state, and backup files private using their explicit modes.
- Add a regression test for the inherited-umask failure seen on the fresh Pi.

## 0.1.1 - Preserve SSH during USB preparation

- Fix premature SSH loss caused by global `netplan apply` during dongle preparation.
- Leave an already-correct, online dongle profile untouched.
- Apply new dongle settings only to that adapter's supplicant and networkd link.
- Arm timed rollback before any dongle configuration changes, and reset it at handover.
- Retry timed rollback after lock contention instead of losing the recovery attempt.

## 0.1.0 - Network bootstrap trial

- Detect the built-in Wi-Fi and one USB adapter dynamically.
- Verify alternative HTTPS internet before hotspot handover.
- Preserve administrator login and existing application directory layout.
- Add a separate confirmation step and timed network rollback.
- Store network setup version and stage; provide a read-only status command.

Full application install/upgrade is not included in this release.
