# USB vision baseline 0.3.0

This release packages the user's July 11 Raspberry Pi image baseline, not a newly
resolved set of Python dependencies. It is restricted to Ubuntu 26.04 ARM64.

- Python: cpython-3.10.20-linux-aarch64-gnu and its original interpreter links.
- Environments: controller and yolo; package/version inventories are under environments/.
- Models: yolov8n.onnx, yolov8s.onnx, yolov8m.onnx from the image's existing weights folder.
- Source: codynick_ai and its supporting sound assets from the same image.
- No student scripts, captured media, databases, credentials, or logs are in the archives.

The archives contain upstream package metadata/license files as present in the image.
Third-party runtimes, libraries, and models remain subject to their own licenses;
the project does not claim ownership of them. These pinned binaries will need future
maintenance/security updates; running setup does not silently replace them with
arbitrary upstream versions. The source/provenance manifest records asset hashes.

Use tools/import_baseline.py and tools/build_app_release.py with the source image
to reproduce the allowlisted inputs, then tools/seal_core_release.py to refresh
source/helper pins before publishing a new immutable version. Do not rewrite old tags.
