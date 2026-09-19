"""Build the 0.3.0 USB vision baseline from allowlisted image paths."""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import tarfile
try:
    from .import_baseline import ExtImage
except ImportError:
    from import_baseline import ExtImage

VERSION = '0.3.0'

def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda:f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()

class InodeStream:
    def __init__(self, image, inode):
        self.image = image
        b = image.inode(inode)
        self.size = image.u32(b,4)+(image.u32(b,108)<<32)
        self.pos = 0
        self.blocks = list(image.extents(b[40:100])) if self.size else []

    def read(self, size):
        size = min(size, self.size-self.pos)
        out = bytearray(size)
        end = self.pos+size
        for logical,count,physical,unwritten in self.blocks:
            lo = logical*self.image.bs
            hi = lo+count*self.image.bs
            start, stop = max(self.pos,lo), min(end,hi)
            if stop>start and not unwritten:
                out[start-self.pos:stop-self.pos] = self.image.read(physical*self.image.bs+start-lo,stop-start)
        self.pos=end
        return bytes(out)

def link_target(image, inode):
    b=image.inode(inode); size=image.u32(b,4)
    raw=b[40:40+size] if size <= 60 else InodeStream(image,inode).read(size)
    return raw.decode()

def pack_image(image, paths, destination):
    expanded=0
    def add(tar, path, inode):
        nonlocal expanded
        b=image.inode(inode); mode=image.u16(b,0); kind=mode&0xf000
        item=tarfile.TarInfo(path.lstrip('/')); item.mode=mode&0o777
        item.uid=item.gid=0; item.uname=item.gname='root'; item.mtime=0
        if kind==0x4000:
            item.type=tarfile.DIRTYPE; item.mode=0o755; tar.addfile(item)
            for name,child in image.entries(inode):
                if name in ('__pycache__','.lock','.gitignore'): continue
                add(tar,path+'/'+name,child)
        elif kind==0xa000:
            item.type=tarfile.SYMTYPE; item.linkname=link_target(image,inode)
            tar.addfile(item)
        elif kind==0x8000:
            item.size=image.u32(b,4)+(image.u32(b,108)<<32)
            item.mode=0o755 if mode&0o111 else 0o644
            expanded+=item.size
            tar.addfile(item,InodeStream(image,inode))
        else: raise ValueError('Unexpected special image file: '+path)
    with tarfile.open(destination,'w:gz',compresslevel=3) as tar:
        for path in paths: add(tar,path,image.lookup(path))
    return expanded

def build(image_path, setup, root, output):
    root=Path(root); output=Path(output); output.mkdir(parents=True,exist_ok=True)
    image=ExtImage(image_path); assets=[]
    def record(path, kind, expanded=0):
        item=dict(name=path.name,kind=kind,size=path.stat().st_size,sha256=digest(path),expanded_size=expanded)
        assets.append(item); print(item['name'],item['size'],flush=True)
    runtime_paths=['/home/client/.local/share/uv/python/'+n for n in
        ['cpython-3.10.20-linux-aarch64-gnu','cpython-3.10-linux-aarch64-gnu']]
    plans=[('python-runtimes',runtime_paths)]
    plans += [(env+'-environment',['/home/client/.codynick-ai/envs/'+env]) for env in ['controller','yolo']]
    for name,paths in plans:
        target=output/(name+'-'+VERSION+'.tar.gz')
        expanded=pack_image(image,paths,target)
        record(target,'runtime',expanded)
    model_paths=['/home/client/.deepface/weights/'+n for n in ['yolov8n.onnx','yolov8s.onnx','yolov8m.onnx']]
    # Split TTS from other models to keep each GitHub release asset below 2 GiB.
    for name,paths in [('vision-models',model_paths)]:
        target=output/(name+'-'+VERSION+'.tar.gz')
        record(target,'models',pack_image(image,paths,target))
    manifest=dict(version=VERSION,tag='v'+VERSION+'-vision',os='ubuntu',os_version='26.04',arch='aarch64',
                  components={'library':'1.20.1','ide':'Rev.B2','ai':'Rev.B2-image-20260711','watchdog':'Rev.B2-image-20260711'},
                  predecessor_versions=[],chapter8=False,assets=assets)
    (output/'release.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (root/'releases'/('vision-'+VERSION+'.json')).write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print('Total compressed bytes',sum(a['size'] for a in assets),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--image',required=True); p.add_argument('--setup',default='')
    p.add_argument('--root',default='.'); p.add_argument('--output',default='dist/0.3.0')
    a=p.parse_args(); build(a.image,a.setup,a.root,a.output)
