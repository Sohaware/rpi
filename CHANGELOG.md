# Changelog

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
