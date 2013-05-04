# vim:fileencoding=utf-8:noet
from powerline.lib import mergedicts, add_divider_highlight_group
from powerline.lib.humanize_bytes import humanize_bytes
from powerline.lib.vcs import guess
from subprocess import call, PIPE
import os
import sys
from functools import partial
from tests import TestCase, SkipTest


class TestLib(TestCase):
	def test_mergedicts(self):
		d = {}
		mergedicts(d, {'abc': {'def': 'ghi'}})
		self.assertEqual(d, {'abc': {'def': 'ghi'}})
		mergedicts(d, {'abc': {'def': {'ghi': 'jkl'}}})
		self.assertEqual(d, {'abc': {'def': {'ghi': 'jkl'}}})
		mergedicts(d, {})
		self.assertEqual(d, {'abc': {'def': {'ghi': 'jkl'}}})
		mergedicts(d, {'abc': {'mno': 'pqr'}})
		self.assertEqual(d, {'abc': {'def': {'ghi': 'jkl'}, 'mno': 'pqr'}})

	def test_add_divider_highlight_group(self):
		def decorated_function_name(**kwargs):
			return str(kwargs)
		func = add_divider_highlight_group('hl_group')(decorated_function_name)
		self.assertEqual(func.__name__, 'decorated_function_name')
		self.assertEqual(func(kw={}), [{'contents': repr({'kw': {}}), 'divider_highlight_group': 'hl_group'}])

	def test_humanize_bytes(self):
		self.assertEqual(humanize_bytes(0), '0 B')
		self.assertEqual(humanize_bytes(1), '1 B')
		self.assertEqual(humanize_bytes(1, suffix='bit'), '1 bit')
		self.assertEqual(humanize_bytes(1000, si_prefix=True), '1 kB')
		self.assertEqual(humanize_bytes(1024, si_prefix=True), '1 kB')
		self.assertEqual(humanize_bytes(1000000000, si_prefix=True), '1.00 GB')
		self.assertEqual(humanize_bytes(1000000000, si_prefix=False), '953.7 MiB')


class TestFilesystemWatchers(TestCase):
	def do_test_for_change(self, watcher, path):
		import time
		st = time.time()
		while time.time() - st < 1:
			if watcher(path):
				return
			time.sleep(0.1)
		self.fail('The change to {0} was not detected'.format(path))

	def test_file_watcher(self):
		from powerline.lib.file_watcher import create_file_watcher
		w = create_file_watcher(use_stat=False)
		if w.is_stat_based:
			raise SkipTest('This test is not suitable for a stat based file watcher')
		f1, f2 = os.path.join(INOTIFY_DIR, 'file1'), os.path.join(INOTIFY_DIR, 'file2')
		with open(f1, 'wb'):
			with open(f2, 'wb'):
				pass
		ne = os.path.join(INOTIFY_DIR, 'notexists')
		self.assertRaises(OSError, w, ne)
		self.assertTrue(w(f1))
		self.assertTrue(w(f2))
		os.utime(f1, None), os.utime(f2, None)
		self.do_test_for_change(w, f1)
		self.do_test_for_change(w, f2)
		# Repeat once
		os.utime(f1, None), os.utime(f2, None)
		self.do_test_for_change(w, f1)
		self.do_test_for_change(w, f2)
		# Check that no false changes are reported
		self.assertFalse(w(f1), 'Spurious change detected')
		self.assertFalse(w(f2), 'Spurious change detected')
		# Check that open the file with 'w' triggers a change
		with open(f1, 'wb'):
			with open(f2, 'wb'):
				pass
		self.do_test_for_change(w, f1)
		self.do_test_for_change(w, f2)
		# Check that writing to a file with 'a' triggers a change
		with open(f1, 'ab') as f:
			f.write(b'1')
		self.do_test_for_change(w, f1)
		# Check that deleting a file registers as a change
		os.unlink(f1)
		self.do_test_for_change(w, f1)

	def test_tree_watcher(self):
		from powerline.lib.tree_watcher import TreeWatcher
		tw = TreeWatcher()
		subdir = os.path.join(INOTIFY_DIR, 'subdir')
		os.mkdir(subdir)
		if tw.watch(INOTIFY_DIR).is_dummy:
			raise SkipTest('No tree watcher available')
		import shutil
		self.assertTrue(tw(INOTIFY_DIR))
		self.assertFalse(tw(INOTIFY_DIR))
		changed = partial(self.do_test_for_change, tw, INOTIFY_DIR)
		open(os.path.join(INOTIFY_DIR, 'tree1'), 'w').close()
		changed()
		open(os.path.join(subdir, 'tree1'), 'w').close()
		changed()
		os.unlink(os.path.join(subdir, 'tree1'))
		changed()
		os.rmdir(subdir)
		changed()
		os.mkdir(subdir)
		changed()
		os.rename(subdir, subdir + '1')
		changed()
		shutil.rmtree(subdir + '1')
		changed()
		os.mkdir(subdir)
		f = os.path.join(subdir, 'f')
		open(f, 'w').close()
		changed()
		with open(f, 'a') as s:
			s.write(' ')
		changed()
		os.rename(f, f + '1')
		changed()

use_mercurial = use_bzr = sys.version_info < (3, 0)


class TestVCS(TestCase):
	def do_branch_rename_test(self, repo, q):
		import time
		st = time.time()
		while time.time() - st < 1:
			# Give inotify time to deliver events
			ans = repo.branch()
			if ans == q:
				break
			time.sleep(0.01)
		self.assertEqual(ans, q)

	def test_git(self):
		repo = guess(path=GIT_REPO)
		self.assertNotEqual(repo, None)
		self.assertEqual(repo.branch(), 'master')
		self.assertEqual(repo.status(), None)
		self.assertEqual(repo.status('file'), None)
		with open(os.path.join(GIT_REPO, 'file'), 'w') as f:
			f.write('abc')
			f.flush()
			self.assertEqual(repo.status(), '  U')
			self.assertEqual(repo.status('file'), '??')
			call(['git', 'add', '.'], cwd=GIT_REPO)
			self.assertEqual(repo.status(), ' I ')
			self.assertEqual(repo.status('file'), 'A ')
			f.write('def')
			f.flush()
			self.assertEqual(repo.status(), 'DI ')
			self.assertEqual(repo.status('file'), 'AM')
		os.remove(os.path.join(GIT_REPO, 'file'))
		# Test changing branch
		self.assertEqual(repo.branch(), 'master')
		call(['git', 'branch', 'branch1'], cwd=GIT_REPO)
		call(['git', 'checkout', '-q', 'branch1'], cwd=GIT_REPO)
		self.do_branch_rename_test(repo, 'branch1')
		# For some reason the rest of this test fails on travis and only on
		# travis, and I can't figure out why
		if 'TRAVIS' in os.environ:
			raise SkipTest('Part of this test fails on Travis for unknown reasons')
		call(['git', 'branch', 'branch2'], cwd=GIT_REPO)
		call(['git', 'checkout', '-q', 'branch2'], cwd=GIT_REPO)
		self.do_branch_rename_test(repo, 'branch2')
		call(['git', 'checkout', '-q', '--detach', 'branch1'], cwd=GIT_REPO)
		self.do_branch_rename_test(repo, '[DETACHED HEAD]')

	if use_mercurial:
		def test_mercurial(self):
			repo = guess(path=HG_REPO)
			self.assertNotEqual(repo, None)
			self.assertEqual(repo.branch(), 'default')
			self.assertEqual(repo.status(), None)
			with open(os.path.join(HG_REPO, 'file'), 'w') as f:
				f.write('abc')
				f.flush()
				self.assertEqual(repo.status(), ' U')
				self.assertEqual(repo.status('file'), 'U')
				call(['hg', 'add', '.'], cwd=HG_REPO, stdout=PIPE)
				self.assertEqual(repo.status(), 'D ')
				self.assertEqual(repo.status('file'), 'A')
			os.remove(os.path.join(HG_REPO, 'file'))

	if use_bzr:
		def test_bzr(self):
			repo = guess(path=BZR_REPO)
			self.assertNotEqual(repo, None, 'No bzr repo found. Do you have bzr installed?')
			self.assertEqual(repo.branch(), 'test_powerline')
			self.assertEqual(repo.status(), None)
			with open(os.path.join(BZR_REPO, 'file'), 'w') as f:
				f.write('abc')
			self.assertEqual(repo.status(), ' U')
			self.assertEqual(repo.status('file'), '? ')
			call(['bzr', 'add', '-q', '.'], cwd=BZR_REPO, stdout=PIPE)
			self.assertEqual(repo.status(), 'D ')
			self.assertEqual(repo.status('file'), '+N')
			call(['bzr', 'commit', '-q', '-m', 'initial commit'], cwd=BZR_REPO)
			self.assertEqual(repo.status(), None)
			with open(os.path.join(BZR_REPO, 'file'), 'w') as f:
				f.write('def')
			self.assertEqual(repo.status(), 'D ')
			self.assertEqual(repo.status('file'), ' M')
			self.assertEqual(repo.status('notexist'), None)
			with open(os.path.join(BZR_REPO, 'ignored'), 'w') as f:
				f.write('abc')
			self.assertEqual(repo.status('ignored'), '? ')
			# Test changing the .bzrignore file should update status
			with open(os.path.join(BZR_REPO, '.bzrignore'), 'w') as f:
				f.write('ignored')
			self.assertEqual(repo.status('ignored'), None)
			# Test changing the dirstate file should invalidate the cache for
			# all files in the repo
			with open(os.path.join(BZR_REPO, 'file2'), 'w') as f:
				f.write('abc')
			call(['bzr', 'add', 'file2'], cwd=BZR_REPO, stdout=PIPE)
			call(['bzr', 'commit', '-q', '-m', 'file2 added'], cwd=BZR_REPO)
			with open(os.path.join(BZR_REPO, 'file'), 'a') as f:
				f.write('hello')
			with open(os.path.join(BZR_REPO, 'file2'), 'a') as f:
				f.write('hello')
			self.assertEqual(repo.status('file'), ' M')
			self.assertEqual(repo.status('file2'), ' M')
			call(['bzr', 'commit', '-q', '-m', 'multi'], cwd=BZR_REPO)
			self.assertEqual(repo.status('file'), None)
			self.assertEqual(repo.status('file2'), None)

			# Test changing branch
			call(['bzr', 'nick', 'branch1'], cwd=BZR_REPO, stdout=PIPE, stderr=PIPE)
			self.do_branch_rename_test(repo, 'branch1')

			# Test branch name/status changes when swapping repos
			for x in ('b1', 'b2'):
				d = os.path.join(BZR_REPO, x)
				os.mkdir(d)
				call(['bzr', 'init', '-q'], cwd=d)
				call(['bzr', 'nick', '-q', x], cwd=d)
				repo = guess(path=d)
				self.assertEqual(repo.branch(), x)
				self.assertFalse(repo.status())
				if x == 'b1':
					open(os.path.join(d, 'dirty'), 'w').close()
					self.assertTrue(repo.status())
			os.rename(os.path.join(BZR_REPO, 'b1'), os.path.join(BZR_REPO, 'b'))
			os.rename(os.path.join(BZR_REPO, 'b2'), os.path.join(BZR_REPO, 'b1'))
			os.rename(os.path.join(BZR_REPO, 'b'), os.path.join(BZR_REPO, 'b2'))
			for x, y in (('b1', 'b2'), ('b2', 'b1')):
				d = os.path.join(BZR_REPO, x)
				repo = guess(path=d)
				self.do_branch_rename_test(repo, y)
				if x == 'b1':
					self.assertFalse(repo.status())
				else:
					self.assertTrue(repo.status())

old_HGRCPATH = None
old_cwd = None


GIT_REPO = 'git_repo' + os.environ.get('PYTHON', '')
HG_REPO = 'hg_repo' + os.environ.get('PYTHON', '')
BZR_REPO = 'bzr_repo' + os.environ.get('PYTHON', '')
INOTIFY_DIR = 'inotify' + os.environ.get('PYTHON', '')


def setUpModule():
	global old_cwd
	global old_HGRCPATH
	old_cwd = os.getcwd()
	os.chdir(os.path.dirname(__file__))
	call(['git', 'init', '--quiet', GIT_REPO])
	assert os.path.isdir(GIT_REPO)
	call(['git', 'config', '--local', 'user.name', 'Foo'], cwd=GIT_REPO)
	call(['git', 'config', '--local', 'user.email', 'bar@example.org'], cwd=GIT_REPO)
	call(['git', 'commit', '--allow-empty', '--message', 'Initial commit', '--quiet'], cwd=GIT_REPO)
	if use_mercurial:
		old_HGRCPATH = os.environ.get('HGRCPATH')
		os.environ['HGRCPATH'] = ''
		call(['hg', 'init', HG_REPO])
		with open(os.path.join(HG_REPO, '.hg', 'hgrc'), 'w') as hgrc:
			hgrc.write('[ui]\n')
			hgrc.write('username = Foo <bar@example.org>\n')
	if use_bzr:
		call(['bzr', 'init', '--quiet', BZR_REPO])
		call(['bzr', 'config', 'email=Foo <bar@example.org>'], cwd=BZR_REPO)
		call(['bzr', 'config', 'nickname=test_powerline'], cwd=BZR_REPO)
		call(['bzr', 'config', 'create_signatures=0'], cwd=BZR_REPO)
	os.mkdir(INOTIFY_DIR)


def tearDownModule():
	global old_cwd
	global old_HGRCPATH
	for repo_dir in [INOTIFY_DIR, GIT_REPO] + ([HG_REPO] if use_mercurial else []) + ([BZR_REPO] if use_bzr else []):
		for root, dirs, files in list(os.walk(repo_dir, topdown=False)):
			for file in files:
				os.remove(os.path.join(root, file))
			for dir in dirs:
				os.rmdir(os.path.join(root, dir))
		os.rmdir(repo_dir)
	if use_mercurial:
		if old_HGRCPATH is None:
			os.environ.pop('HGRCPATH')
		else:
			os.environ['HGRCPATH'] = old_HGRCPATH
	os.chdir(old_cwd)


if __name__ == '__main__':
	from tests import main
	main()
