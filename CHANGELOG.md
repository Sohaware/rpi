# Changelog

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
