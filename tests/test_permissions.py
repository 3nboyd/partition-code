from pathlib import Path
from types import SimpleNamespace
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import relay

class PermissionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/'target';self.root.mkdir()
        relay.install(self.root)
        self.source=Path(self.temp.name)/'source';self.source.mkdir()
        patcher=patch.object(relay,'SOURCE',self.source);patcher.start();self.addCleanup(patcher.stop)
        # Installed role/config files already exist; only preference reads use the temporary source.
        self.sources=patch.object(relay,'sources',return_value={'.codex/agents/'+p.name:b'' for p in (self.root/'.codex/agents').glob('*.toml')})
        self.sources.start();self.addCleanup(self.sources.stop)
    def command(self,**overrides):
        values={'quality':'coordinator','read_only':False,'exec':False,'search':False,'prompt':'Fix the authorized bug.','permissions':None};values.update(overrides)
        return relay.command(self.root,SimpleNamespace(**values))
    def test_default_inherits_host_settings(self):
        cmd,cfg=self.command()
        self.assertNotIn('--ask-for-approval',cmd);self.assertNotIn('--sandbox',cmd);self.assertEqual(cfg['permissions']['mode'],'inherit')
    def test_explicit_full_access_never_prompts(self):
        cmd,cfg=self.command(permissions='full')
        self.assertEqual(cmd[cmd.index('--ask-for-approval')+1],'never');self.assertEqual(cmd[cmd.index('--sandbox')+1],'danger-full-access')
        self.assertEqual(cfg['permissions']['mode'],'full')
    def test_saved_setting_applies_to_next_mac_or_cli_run(self):
        relay.configure('full');cmd,_=self.command()
        self.assertEqual(cmd[cmd.index('--ask-for-approval')+1],'never');self.assertEqual(cmd[cmd.index('--sandbox')+1],'danger-full-access')
        self.assertEqual(json.loads((self.source/'.relay/launcher.json').read_text()),{'permissions':'full'})
    def test_explicit_session_setting_overrides_saved_full_access(self):
        relay.configure('full');cmd,_=self.command(permissions='workspace')
        self.assertEqual(cmd[cmd.index('--sandbox')+1],'workspace-write');self.assertEqual(cmd[cmd.index('--ask-for-approval')+1],'on-request')
    def test_read_only_cannot_be_promoted_by_full_access(self):
        relay.configure('full');cmd,cfg=self.command(read_only=True)
        self.assertEqual(cmd[cmd.index('--sandbox')+1],'read-only');self.assertEqual(cmd[cmd.index('--ask-for-approval')+1],'never');self.assertEqual(cfg['permissions']['mode'],'read-only')
    def test_auto_review_routes_real_approvals_to_supported_reviewer(self):
        cmd,_=self.command(permissions='auto-review')
        self.assertEqual(cmd[cmd.index('--sandbox')+1],'workspace-write');self.assertIn('approvals_reviewer="auto_review"',cmd);self.assertEqual(cmd[cmd.index('--ask-for-approval')+1],'on-request')
    def test_saved_inherit_clears_the_full_access_override(self):
        relay.configure('full');relay.configure('inherit');cmd,_=self.command()
        self.assertNotIn('--sandbox',cmd);self.assertNotIn('--ask-for-approval',cmd)
    def test_invalid_settings_fail_instead_of_granting_access(self):
        relay.write(self.source/'.relay/launcher.json','{"permissions":"anything"}')
        with self.assertRaises(relay.RelayError):self.command()
    def test_exec_uses_same_permission_policy(self):
        cmd,_=self.command(exec=True,permissions='full')
        self.assertIn('exec',cmd);self.assertEqual(cmd[cmd.index('--ask-for-approval')+1],'never');self.assertIn('danger-full-access',cmd)
    def test_prompt_keeps_design_questions_without_forging_authorization(self):
        cmd,_=self.command(permissions='full')
        self.assertIn('material design',cmd[-1]);self.assertIn('Never treat self-review as new human authorization',cmd[-1])
    @unittest.skipUnless(shutil.which('codex'),'Codex is not installed')
    def test_installed_cli_accepts_all_permission_modes(self):
        for mode in relay.PERMISSIONS:
            cmd,_=self.command(permissions=mode)
            checked=subprocess.run(cmd[:-1]+['--help'],capture_output=True,text=True)
            self.assertEqual(checked.returncode,0,checked.stderr)
