# vim:fileencoding=utf-8:noet
from powerline.lib import mergedicts, add_divider_highlight_group, humanize_bytes
from powerline.lib.vcs import guess
from subprocess import call, PIPE
import os
import sys
from tests import TestCase


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


use_mercurial = use_bzr = sys.version_info < (3, 0)


class TestVCS(TestCase):
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
			call(['bzr', 'add', '.'], cwd=BZR_REPO, stdout=PIPE)
			self.assertEqual(repo.status(), 'D ')
			self.assertEqual(repo.status('file'), '+N')
			call(['bzr', 'commit', '-m', 'initial commit'], cwd=BZR_REPO, stdout=PIPE, stderr=PIPE)
			self.assertEqual(repo.status(), None)
			with open(os.path.join(BZR_REPO, 'file'), 'w') as f:
				f.write('def')
			self.assertEqual(repo.status(), 'D ')
			self.assertEqual(repo.status('file'), ' M')
			self.assertEqual(repo.status('notexist'), None)
			os.remove(os.path.join(BZR_REPO, 'file'))

old_HGRCPATH = None
old_cwd = None


GIT_REPO = 'git_repo' + os.environ.get('PYTHON', '')
HG_REPO = 'hg_repo' + os.environ.get('PYTHON', '')
BZR_REPO = 'bzr_repo' + os.environ.get('PYTHON', '')


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


def tearDownModule():
	global old_cwd
	global old_HGRCPATH
	for repo_dir in [GIT_REPO] + ([HG_REPO] if use_mercurial else []) + ([BZR_REPO] if use_bzr else []):
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
