import importlib.util
import io
from pathlib import Path
import tarfile
import tempfile
import unittest

spec = importlib.util.spec_from_file_location(
    "ocr_setup", Path(__file__).parents[1] / "installer/ocr_setup.py"
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class OcrSetupTests(unittest.TestCase):
    def test_runtime_link_allowed_but_external_link_rejected(self):
        member = tarfile.TarInfo("home/client/.codynick-ai/envs/ocr/bin/python")
        member.type = tarfile.SYMTYPE
        member.linkname = (
            "/home/client/.local/share/uv/python/"
            "cpython-3.9-linux-aarch64-gnu/bin/python3.9"
        )
        m.validate_member(member)
        member.linkname = "/etc/shadow"
        with self.assertRaises(ValueError):
            m.validate_member(member)

    def test_unowned_and_special_paths_rejected(self):
        for name in (
            "../../etc/passwd",
            "/etc/passwd",
            "home/client/userfiles/test.py",
            "home/client/.codynick-ai/models/easyocr/file",
        ):
            with self.assertRaises(ValueError):
                m.validate_member(tarfile.TarInfo(name))
        device = tarfile.TarInfo("home/client/.codynick-ai/envs/ocr/device")
        device.type = tarfile.CHRTYPE
        with self.assertRaises(ValueError):
            m.validate_member(device)

    def test_restore_is_repeatable_and_preserves_unmanaged_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "home/client/.codynick-ai/envs/ocr/module.py"
            archive = root / "ocr.tar.gz"
            with tarfile.open(archive, "w:gz") as bundle:
                member = tarfile.TarInfo("home/client/.codynick-ai/envs/ocr/module.py")
                member.size = 5
                bundle.addfile(member, io.BytesIO(b"hello"))
            m.restore_archive(archive, root)
            target.write_text("damaged")
            other = target.parent / "notes.txt"
            other.write_text("preserve")
            m.restore_archive(archive, root)
            self.assertEqual(target.read_text(), "hello")
            self.assertEqual(other.read_text(), "preserve")

    def test_link_parent_rejected_before_writes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "bad.tar"
            with tarfile.open(archive, "w") as bundle:
                link = tarfile.TarInfo("home/client/.codynick-ai/envs/ocr/link")
                link.type = tarfile.SYMTYPE
                link.linkname = "lib"
                bundle.addfile(link)
                child = tarfile.TarInfo(link.name + "/evil")
                child.size = 1
                bundle.addfile(child, io.BytesIO(b"x"))
            with self.assertRaises(ValueError):
                m.restore_archive(archive, root)
            self.assertFalse((root / "home").exists())


if __name__ == "__main__":
    unittest.main()
