#!/usr/bin/env python3
"""Installer regressions; all filesystem mutations are confined to temporary fixtures."""
import importlib.util,json,os,subprocess,tarfile,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('installer',ROOT/'scripts/install.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class SafetyTests(unittest.TestCase):
 def fixture(self,folder):
  base=Path(folder);config=base/'config';config.mkdir();targets=[]
  for name in ('alacritty','mako'):
   target=config/name;target.mkdir();(target/'original').write_text(name)
   source=base/'release'/name;source.mkdir(parents=True)
   targets.append((target,source))
  backup=base/'backups/run';backup.mkdir(parents=True)
  return targets,backup
 def assert_originals(self,targets):
  for target,_ in targets:
   self.assertFalse(target.is_symlink());self.assertEqual((target/'original').read_text(),target.name)
 def test_longest_source_prefix_is_replaced_first(self):
  with patch.object(m,'ROOT',Path('/tmp/downloaded-source')):
   release=Path('/tmp/home/releases/current');config=Path('/tmp/home/config')
   for prefix in ('/home/andrew/dotfiles/niri-staging','/home/andrew/dotfiles','~/dotfiles/niri-staging','~/dotfiles','/tmp/downloaded-source'):
    self.assertEqual(m.runtime_text(prefix+'/assets/theme',release,config),str(release)+'/assets/theme')
 def test_initial_journal_failure_leaves_all_targets_untouched(self):
  with tempfile.TemporaryDirectory() as t:
   targets,backup=self.fixture(t)
   with patch.object(m,'write_manifest',side_effect=OSError('journal unavailable')):
    with self.assertRaises(OSError):m.install_links(targets,backup)
   self.assert_originals(targets)
 def test_final_journal_failure_restores_all_targets(self):
  with tempfile.TemporaryDirectory() as t:
   targets,backup=self.fixture(t);writer=m.write_manifest;calls=[]
   def write(path,data):
    calls.append(1)
    if len(calls)==2:raise OSError('final journal write failed')
    return writer(path,data)
   with patch.object(m,'write_manifest',side_effect=write):
    with self.assertRaises(OSError):m.install_links(targets,backup)
   self.assert_originals(targets)
 def test_symlink_failure_restores_changed_and_current_target(self):
  with tempfile.TemporaryDirectory() as t:
   targets,backup=self.fixture(t);original=Path.symlink_to
   def fail(path,*args,**kwargs):
    if path==targets[1][0]:raise OSError('link failure')
    return original(path,*args,**kwargs)
   with patch.object(Path,'symlink_to',fail):
    with self.assertRaises(OSError):m.install_links(targets,backup)
   self.assert_originals(targets)
 def test_recover_pending_journal_with_untouched_targets(self):
  with tempfile.TemporaryDirectory() as t:
   targets,backup=self.fixture(t);items=[]
   for i,(target,source) in enumerate(targets):items.append(dict(target=str(target),source=str(source),backup=str(backup/str(i)),existed=True,installed=False))
   manifest=backup/'manifest.json';m.write_manifest(manifest,items)
   targets[0][0].rename(backup/'0');targets[0][0].symlink_to(targets[0][1])
   with patch.object(m.subprocess,'run'):m.rollback(manifest)
   self.assert_originals(targets)
 def test_recover_pending_journal_after_backup_before_link(self):
  with tempfile.TemporaryDirectory() as t:
   targets,backup=self.fixture(t);target,source=targets[0]
   items=[dict(target=str(target),source=str(source),backup=str(backup/'0'),existed=True,installed=False)]
   manifest=backup/'manifest.json';m.write_manifest(manifest,items)
   target.rename(backup/'0')
   with patch.object(m.subprocess,'run'):m.rollback(manifest)
   self.assert_originals(targets)
 def test_completed_rollback_refuses_to_overwrite_later_edits(self):
  with tempfile.TemporaryDirectory() as t:
   targets,backup=self.fixture(t);manifest=m.install_links(targets,backup)
   target=targets[1][0];target.unlink();target.write_text('later user edit')
   with self.assertRaises(RuntimeError):m.rollback(manifest)
   self.assertTrue(targets[0][0].is_symlink());self.assertEqual(target.read_text(),'later user edit')
 def test_bootstrap_check_uses_validation_not_install(self):
  with tempfile.TemporaryDirectory() as t:
   base=Path(t);source=base/'fixture';(source/'scripts').mkdir(parents=True);(source/'quickshell').mkdir()
   (source/'scripts/install.py').write_text('');(source/'quickshell/Dashboard.qml').write_text('')
   (source/'install.sh').write_text('#!/bin/sh\nprintf "%s\\n" "$@" > "$BOOTSTRAP_ARGS"\n')
   (source/'scripts/install-deps.sh').write_text('#!/bin/sh\ntouch "$FORBIDDEN_INSTALL"\n')
   archive=base/'source.tar.gz'
   with tarfile.open(archive,'w:gz') as tar:tar.add(source,arcname='repository')
   binary=base/'bin';binary.mkdir();gh=binary/'gh'
   gh.write_text('#!/bin/sh\nif [ "$1" = auth ]; then exit 0; fi\ncat "$BOOTSTRAP_ARCHIVE"\n');gh.chmod(0o755)
   args=base/'args';forbidden=base/'installed'
   env=dict(os.environ,PATH=str(binary)+os.pathsep+os.environ['PATH'],BOOTSTRAP_ARCHIVE=str(archive),BOOTSTRAP_ARGS=str(args),FORBIDDEN_INSTALL=str(forbidden))
   p=subprocess.run(['bash',str(ROOT/'bootstrap.sh'),'--check'],env=env,capture_output=True,text=True)
   self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(args.read_text().splitlines(),['--portable','--check']);self.assertFalse(forbidden.exists())
if __name__=='__main__':unittest.main()
