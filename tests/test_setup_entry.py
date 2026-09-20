"""Exercise the actual Bash dispatcher with isolated, checksum-verified fake stages."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).parents[1]


@unittest.skipUnless(os.name == 'posix' and shutil.which('bash'), 'Linux Bash integration test')
class SetupEntryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.state = self.root / 'state.json'
        self.trace = self.root / 'trace.txt'
        self.bin = self.root / 'bin'; self.bin.mkdir()
        control = '''#!/usr/bin/python3
import json,os,sys,shutil
from pathlib import Path
root=Path(os.environ['FAKE_ROOT']); state=root/'state.json'
cmd=Path(sys.argv[0]).name
if cmd=='control': cmd=sys.argv[1]
with (root/'trace.txt').open('a') as log: log.write(cmd+' '+ ' '.join(sys.argv[1:])+'\\n')
if cmd=='wget':
 target=sys.argv[sys.argv.index('-O')+1]
 shutil.copyfile(root/('network.sh' if '/v0.1.2-network/' in sys.argv[-1] else 'apps.sh'),target)
elif cmd=='network':
 if not state.exists(): state.write_text(json.dumps({'stage':'pending'}))
elif cmd=='codynick-setup': state.write_text(json.dumps({'stage':'network-ready'}))
elif cmd=='systemctl' and os.environ.get('MISSING_SERVICE')=='1': raise SystemExit(1)
'''
        for name in ('control', 'wget', 'systemctl', 'journalctl', 'codynick-setup'):
            path=self.bin/name; path.write_text(control); path.chmod(0o755)
        for name in ('network', 'apps'):
            (self.root/(name+'.sh')).write_text('#!/bin/bash\n"$FAKE_ROOT/bin/control" '+name+'\n')
        script=(ROOT/'setup.sh').read_text()
        script=script.replace('[[ $EUID -eq 0 ]]','[[ 1 -eq 1 ]]')
        script=script.replace('/run/lock/', str(self.root)+'/')
        script=script.replace('/var/lib/codynick/network-setup.json', str(self.state))
        script=script.replace('/usr/local/sbin/codynick-setup', str(self.bin/'codynick-setup'))
        for key,name in (('NETWORK','network'),('APPS','apps')):
            digest=hashlib.sha256((self.root/(name+'.sh')).read_bytes()).hexdigest()
            script=re.sub(key+r'_SHA256="[^"]+"',key+'_SHA256="'+digest+'"',script)
        self.entry=self.root/'entry.sh'; self.entry.write_text(script)

    def invoke(self, ssh='10.47.14.2 1234 10.47.14.63 22', **extra):
        env=dict(os.environ, PATH=str(self.bin)+':'+os.environ['PATH'], FAKE_ROOT=str(self.root), SSH_CONNECTION=ssh, **extra)
        return subprocess.run(['bash',str(self.entry)], env=env, capture_output=True, text=True, timeout=15)

    def test_fresh_then_same_command_confirms_and_installs_without_ssh_environment(self):
        first=self.invoke()
        self.assertEqual(first.returncode,0,first.stderr)
        self.assertNotIn('\napps ', '\n'+self.trace.read_text())
        second=self.invoke('')
        self.assertEqual(second.returncode,0,second.stderr)
        self.assertEqual(json.loads(self.state.read_text())['stage'],'network-ready')
        self.assertIn('codynick-setup --confirm',self.trace.read_text())
        self.assertIn('\napps ', '\n'+self.trace.read_text())

    def test_ready_repeated_command_never_reconfigures_network(self):
        self.state.write_text(json.dumps({'stage':'network-ready'}))
        for _ in range(2):
            result=self.invoke()
            self.assertEqual(result.returncode,0,result.stderr)
        trace=self.trace.read_text()
        self.assertNotIn('/v0.1.2-network/',trace)
        self.assertNotIn('systemctl start',trace)
        self.assertEqual(trace.count('\napps '),2)

    def test_broken_network_blocks_application_deployment(self):
        self.state.write_text(json.dumps({'stage':'network-ready'}))
        result=self.invoke(MISSING_SERVICE='1')
        self.assertNotEqual(result.returncode,0)
        self.assertNotIn('\napps ', '\n'+self.trace.read_text())
