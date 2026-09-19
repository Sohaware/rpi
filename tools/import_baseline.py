"""Import selected application sources and installed package versions from a Pi image.

No account databases, SSH keys, network credentials, logs, or student data are imported.
"""
import argparse
from email.parser import Parser
import hashlib
import json
from pathlib import Path
import struct
import tarfile


class ExtImage:
    def __init__(self, path):
        self.f = open(path, 'rb')
        mbr = self.f.read(512)
        assert mbr[510:] == b'\x55\xaa'
        off = 446 + 16
        assert mbr[off + 4] == 0x83
        self.base = self.u32(mbr, off + 8) * 512
        sb = self.read(1024, 1024)
        assert self.u16(sb, 56) == 0xef53
        self.bs = 1024 << self.u32(sb, 24)
        self.ipg, self.isize = self.u32(sb, 40), self.u16(sb, 88)
        self.ds = max(32, self.u16(sb, 254)) if self.u32(sb, 96) & 128 else 32
        self.gd = (2 if self.bs == 1024 else 1) * self.bs

    @staticmethod
    def u16(b, o): return struct.unpack_from('<H', b, o)[0]

    @staticmethod
    def u32(b, o): return struct.unpack_from('<I', b, o)[0]

    def read(self, offset, size):
        self.f.seek(self.base + offset)
        b = self.f.read(size)
        if len(b) != size: raise ValueError('Truncated image')
        return b

    def inode(self, n):
        group, index = divmod(n - 1, self.ipg)
        d = self.read(self.gd + group * self.ds, self.ds)
        table = self.u32(d, 8) + ((self.u32(d, 40) << 32) if self.ds >= 64 else 0)
        return self.read(table * self.bs + index * self.isize, self.isize)

    def extents(self, b):
        assert self.u16(b, 0) == 0xf30a
        for i in range(self.u16(b, 2)):
            o = 12 + i * 12
            if self.u16(b, 6):
                yield from self.extents(self.read((self.u32(b,o+4)+(self.u16(b,o+8)<<32))*self.bs, self.bs))
            else:
                length = self.u16(b, o+4)
                yield self.u32(b,o), length if length <= 32768 else length-32768, self.u32(b,o+8)+(self.u16(b,o+6)<<32), length>32768

    def data(self, n):
        b = self.inode(n)
        size = self.u32(b,4)+(self.u32(b,108)<<32)
        if size > 32 * 1024 * 1024: raise ValueError('Metadata/source file too large')
        if self.u16(b,0)&0xf000 == 0xa000: raise ValueError('Symlinks are not imported')
        out = bytearray(size)
        if size:
            assert self.u32(b,32)&0x80000, 'Non-extent inode unsupported'
            for logical,count,physical,unwritten in self.extents(b[40:100]):
                start = logical*self.bs
                amount = min(count*self.bs, size-start)
                if amount > 0 and not unwritten: out[start:start+amount] = self.read(physical*self.bs, amount)
        return bytes(out)

    def entries(self, n):
        b = self.data(n)
        pos = 0
        while pos + 8 <= len(b):
            ino, length, nl = self.u32(b,pos), self.u16(b,pos+4), b[pos+6]
            if length < 8: raise ValueError('Invalid directory entry')
            name = b[pos+8:pos+8+nl].decode()
            if ino and name not in ('.','..'): yield name, ino
            pos += length

    def lookup(self, path):
        n = 2
        for part in path.strip('/').split('/'):
            n = dict(self.entries(n))[part]
        return n

    def tree(self, path):
        def descend(n, prefix):
            for name, ino in self.entries(n):
                if name.startswith('.') or name == '__pycache__': continue
                child = prefix / name
                mode = self.u16(self.inode(ino),0)&0xf000
                if mode == 0x4000: yield from descend(ino, child)
                elif mode == 0x8000: yield child, self.data(ino)
        yield from descend(self.lookup(path), Path())


def import_image(image, setup, output):
    ext = ExtImage(image)
    out = Path(output)
    evidence = {}
    def put(relative, data, source):
        target = out / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        evidence[str(relative).replace('\\','/')] = {'source':source, 'sha256':hashlib.sha256(data).hexdigest()}

    for name in ['CodyNick.py', 'Dashboard.py']:
        src = '/home/client/' + name
        put(Path('components/client')/name, ext.data(ext.lookup(src)), 'image:' + src)
    for name in ['service.py','security.py']:
        src = '/root/codynick/' + name
        put(Path('components/watchdog')/name, ext.data(ext.lookup(src)), 'image:' + src)
    for folder in ['codynick_ai','sounds']:
        src = '/home/client/vhl_object_detection/' + folder
        for relative, data in ext.tree(src):
            if relative.suffix not in ['.py','.wav','.md']: continue
            put(Path('components/ai')/folder/relative, data, 'image:'+src+'/'+relative.as_posix())
    runtimes = {}
    for env in ['controller','yolo','ocr','stt','tts']:
        lib = '/home/client/.codynick-ai/envs/'+env+'/lib'
        py = [name for name, _ in ext.entries(ext.lookup(lib)) if name.startswith('python')]
        assert len(py) == 1
        runtimes[env] = py[0].removeprefix('python')
        src = lib+'/'+py[0]+'/site-packages'
        packages = []
        for name, ino in ext.entries(ext.lookup(src)):
            if not name.endswith('.dist-info'): continue
            meta = dict(ext.entries(ino)).get('METADATA')
            if meta is None: continue
            headers = Parser().parsestr(ext.data(meta).decode(), headersonly=True)
            packages.append(headers['Name']+'=='+headers['Version'])
        put(Path('environments')/(env+'.txt'), ('\n'.join(sorted(packages,key=str.lower))+'\n').encode(), 'image:'+src+'/*.dist-info/METADATA')
    put(Path('environments/runtimes.json'), (json.dumps(runtimes,indent=2)+'\n').encode(), 'image:environment lib directories')

    # The vetted web payload contains the maintained IDE, not the image's student files.
    with tarfile.open(Path(setup)/'server-upload/Rev.B2/payloads/ide-Rev.B2.tar.gz') as archive:
        for member in archive:
            p = Path(member.name)
            if not member.isfile() or '..' in p.parts or not p.parts or p.parts[0] != 'html': continue
            if p.suffix == '.zip' or member.name == 'html/blocks/data/main.json': continue
            if member.size > 5*1024*1024: raise ValueError('Unexpected large web payload')
            put(Path('components/ide')/Path(*p.parts[1:]), archive.extractfile(member).read(), 'Rev.B2 IDE payload:'+member.name)
    put(Path('components/ide/blocks/data/main.json'), b'{"blocks":{"languageVersion":0,"blocks":[]}}\n', 'empty new-install default')
    (out/'releases').mkdir(exist_ok=True)
    (out/'releases/baseline-sources.json').write_text(json.dumps({'image_size':Path(image).stat().st_size,'files':evidence},indent=2)+'\n')
    print('Imported',len(evidence),'source/lock files; chapter 8 and personal data excluded.')

if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--image',required=True); p.add_argument('--setup',required=True); p.add_argument('--output',required=True)
    a=p.parse_args(); import_image(a.image,a.setup,a.output)
