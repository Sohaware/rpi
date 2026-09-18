# Changelog

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
