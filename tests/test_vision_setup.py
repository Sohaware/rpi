import importlib.util
import io
from pathlib import Path
import tarfile
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('vision_setup', Path(__file__).parents[1] / 'installer/vision_setup.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class VisionTests(unittest.TestCase):
    def test_allowed_link_and_escape_rejected(self):
        good = tarfile.TarInfo('home/client/.codynick-ai/envs/yolo/bin/python')
        good.type = tarfile.SYMTYPE
        good.linkname = '/home/client/.local/share/uv/python/cpython-3.10-linux-aarch64-gnu/bin/python3.10'
        m.validate_member(good)
        good.linkname = '/etc/shadow'
        with self.assertRaises(ValueError): m.validate_member(good)

    def test_traversal_special_and_unowned_paths_rejected(self):
        for name in ('../../etc/passwd', '/etc/passwd', 'home/client/userfiles/test.py', 'home/client/.codynick-ai/envs/yolo/../../bad'):
            with self.assertRaises(ValueError): m.validate_member(tarfile.TarInfo(name))
        member = tarfile.TarInfo('home/client/.codynick-ai/envs/yolo/device')
        member.type = tarfile.CHRTYPE
        with self.assertRaises(ValueError): m.validate_member(member)

    def test_restore_repeatedly_and_preserve_unmanaged_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / 'home/client/.codynick-ai/envs/yolo/module.py'
            archive = root / 'runtime.tar.gz'
            with tarfile.open(archive, 'w:gz') as tar:
                member = tarfile.TarInfo('home/client/.codynick-ai/envs/yolo/module.py')
                member.size = 5
                tar.addfile(member, io.BytesIO(b'hello'))
            m.restore_archive(archive, root)
            target.write_text('damaged')
            other = target.parent / 'notes.txt'; other.write_text('preserve')
            m.restore_archive(archive, root)
            self.assertEqual(target.read_text(),'hello')
            self.assertEqual(other.read_text(),'preserve')

    def test_archive_link_parent_rejected_before_writes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); archive=root/'bad.tar'
            with tarfile.open(archive,'w') as tar:
                link=tarfile.TarInfo('home/client/.codynick-ai/envs/yolo/link')
                link.type=tarfile.SYMTYPE; link.linkname='lib'; tar.addfile(link)
                child=tarfile.TarInfo(link.name+'/evil'); child.size=1; tar.addfile(child,io.BytesIO(b'x'))
            with self.assertRaises(ValueError): m.restore_archive(archive,root)
            self.assertFalse((root/'home').exists())
