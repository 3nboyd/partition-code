import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import relay as r

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
    def test_install_preserves_existing_instructions_and_global_config(self):
        (self.root/'AGENTS.md').write_text('User instructions.\n');(self.root/'.codex').mkdir();config=self.root/'.codex/config.toml';config.write_text('model="custom"\n')
        r.install(self.root);self.assertIn('User instructions.',(self.root/'AGENTS.md').read_text());self.assertEqual(config.read_text(),'model="custom"\n');self.assertEqual(len(r.roles(self.root)),6)
    def test_preexisting_identical_file_survives_uninstall(self):
        f=self.root/'.codex/agents/relay_explorer.toml';f.parent.mkdir(parents=True);f.write_bytes((r.SOURCE/'agents/relay_explorer.toml').read_bytes())
        r.install(self.root);r.uninstall(self.root);self.assertTrue(f.exists())
    def test_repeat_install_is_stable(self):
        r.install(self.root);before={p.relative_to(self.root):p.read_bytes() for p in self.root.rglob('*') if p.is_file()};r.install(self.root)
        self.assertEqual(before,{p.relative_to(self.root):p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
    def test_conflict_fails_before_partial_writes(self):
        f=self.root/'.codex/agents/relay_reviewer.toml';f.parent.mkdir(parents=True);f.write_text('unrelated')
        with self.assertRaises(r.RelayError):r.install(self.root)
        self.assertFalse((self.root/'.relay/ROUTING.md').exists());self.assertEqual(f.read_text(),'unrelated')
    def test_modified_owned_file_preserved(self):
        r.install(self.root);f=self.root/'.codex/agents/relay_quick.toml';f.write_text('my edit')
        with self.assertRaises(r.RelayError):r.install(self.root)
        result=r.uninstall(self.root);self.assertIn('.codex/agents/relay_quick.toml',result['preserved_modified_files']);self.assertEqual(f.read_text(),'my edit')
    def test_uninstall_preserves_other_instruction_blocks(self):
        (self.root/'AGENTS.md').write_text('My instructions.\n');r.install(self.root);f=self.root/'AGENTS.md';f.write_text(f.read_text()+'More instructions.\n');r.uninstall(self.root)
        self.assertIn('More instructions.',f.read_text());self.assertIn('My instructions.',f.read_text());self.assertNotIn(r.BLOCK,f.read_text())
    def test_symlink_rejected(self):
        other=self.root/'elsewhere';other.mkdir();(self.root/'.relay').symlink_to(other,target_is_directory=True)
        with self.assertRaises(r.RelayError):r.install(self.root)
    def test_manifest_cannot_target_unowned_files(self):
        r.install(self.root);p=self.root/'.relay/state.json';data=json.loads(p.read_text());data['files']['secret.txt']={'sha256':'abc'};p.write_text(json.dumps(data))
        with self.assertRaises(r.RelayError):r.uninstall(self.root)
    def test_command_registers_roles_and_inherits_sandbox(self):
        r.install(self.root)
        class Args:quality='deep';read_only=True;exec=True;prompt='A task with $(literal shell text)';search=True
        cmd,cfg=r.command(self.root,Args());self.assertEqual(cfg['effort'],'high');self.assertIn('read-only',cmd);self.assertIn('exec',cmd);self.assertIn('agents.max_concurrent_threads_per_session=2',cmd)
        self.assertTrue(any('agents.relay_implementer.config_file=' in v for v in cmd));self.assertIn('$(literal shell text)',cmd[-1]);self.assertNotIn('--dangerously-bypass-approvals-and-sandbox',cmd)
    def test_unsupported_model_never_silently_falls_back(self):
        with patch.object(r,'models_available',return_value={'some-model':{'low'}}):
            with self.assertRaises(r.RelayError):r.validate_models([('other-model','low')])
    def test_models_match_role_files(self):
        r.install(self.root);cfg=r.settings(self.root)
        for _,d in r.roles(self.root):self.assertEqual(cfg['roles'][d['name']],{'model':d['model'],'effort':d['model_reasoning_effort']})
    def test_malformed_markers_preserve_file(self):
        p=self.root/'AGENTS.md';p.write_text(r.BEGIN)
        with self.assertRaises(r.RelayError):r.install(self.root)
        self.assertEqual(p.read_text(),r.BEGIN);self.assertFalse((self.root/'.relay').exists())
if __name__=='__main__':unittest.main()
