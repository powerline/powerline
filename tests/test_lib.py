from powerline.lib import mergedicts, underscore_to_camelcase, add_divider_highlight_group, humanize_bytes
from powerline.lib.vcs import guess
from subprocess import call, PIPE
import os
import sys
from tests import TestCase


class TestLib(TestCase):
	def test_underscore_to_camelcase(self):
		self.assertEqual(underscore_to_camelcase('abc_def_ghi'), 'AbcDefGhi')
		self.assertEqual(underscore_to_camelcase('abc_def__ghi'), 'AbcDef_Ghi')

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
		repo = guess(path='git_repo')
		self.assertNotEqual(repo, None)
		self.assertEqual(repo.branch(), 'master')
		self.assertEqual(repo.status(), '   ')
		self.assertEqual(repo.status('file'), None)
		with open(os.path.join('git_repo', 'file'), 'w') as f:
			f.write('abc')
			f.flush()
			self.assertEqual(repo.status(), '  U')
			self.assertEqual(repo.status('file'), '??')
			call(['git', 'add', '.'], cwd='git_repo')
			self.assertEqual(repo.status(), ' I ')
			self.assertEqual(repo.status('file'), 'A ')
			f.write('def')
			f.flush()
			self.assertEqual(repo.status(), 'DI ')
			self.assertEqual(repo.status('file'), 'AM')
		os.remove(os.path.join('git_repo', 'file'))

	if use_mercurial:
		def test_mercurial(self):
			repo = guess(path='hg_repo')
			self.assertNotEqual(repo, None)
			self.assertEqual(repo.branch(), 'default')
			with open(os.path.join('hg_repo', 'file'), 'w') as f:
				f.write('abc')
				f.flush()
				self.assertEqual(repo.status(), ' U')
				self.assertEqual(repo.status('file'), 'U')
				call(['hg', 'add', '.'], cwd='hg_repo', stdout=PIPE)
				self.assertEqual(repo.status(), 'D ')
				self.assertEqual(repo.status('file'), 'A')
			os.remove(os.path.join('hg_repo', 'file'))

	if use_bzr:
		def test_bzr(self):
			repo = guess(path='bzr_repo')
			self.assertNotEqual(repo, None, 'No bzr repo found. Do you have bzr installed?')
			self.assertEqual(repo.branch(), 'test_powerline')
			self.assertEqual(repo.status(), None)
			with open(os.path.join('bzr_repo', 'file'), 'w') as f:
				f.write('abc')
			self.assertEqual(repo.status(), ' U')
			self.assertEqual(repo.status('file'), '? ')
			call(['bzr', 'add', '.'], cwd='bzr_repo', stdout=PIPE)
			self.assertEqual(repo.status(), 'D ')
			self.assertEqual(repo.status('file'), '+N')
			call(['bzr', 'commit', '-m', 'initial commit'], cwd='bzr_repo', stdout=PIPE, stderr=PIPE)
			self.assertEqual(repo.status(), None)
			with open(os.path.join('bzr_repo', 'file'), 'w') as f:
				f.write('def')
			self.assertEqual(repo.status(), 'D ')
			self.assertEqual(repo.status('file'), ' M')
			self.assertEqual(repo.status('notexist'), None)
			os.remove(os.path.join('bzr_repo', 'file'))

old_HGRCPATH = None
old_cwd = None


def setUpModule():
	global old_cwd
	global old_HGRCPATH
	old_cwd = os.getcwd()
	os.chdir(os.path.dirname(__file__))
	call(['git', 'init', '--quiet', 'git_repo'])
	call(['git', 'config', '--local', 'user.name', 'Foo'], cwd='git_repo')
	call(['git', 'config', '--local', 'user.email', 'bar@example.org'], cwd='git_repo')
	call(['git', 'commit', '--allow-empty', '--message', 'Initial commit', '--quiet'], cwd='git_repo')
	if use_mercurial:
		old_HGRCPATH = os.environ.get('HGRCPATH')
		os.environ['HGRCPATH'] = ''
		call(['hg', 'init', 'hg_repo'])
		with open(os.path.join('hg_repo', '.hg', 'hgrc'), 'w') as hgrc:
			hgrc.write('[ui]\n')
			hgrc.write('username = Foo <bar@example.org>\n')
	if use_bzr:
		call(['bzr', 'init', '--quiet', 'bzr_repo'])
		call(['bzr', 'config', 'email=Foo <bar@example.org>'], cwd='bzr_repo')
		call(['bzr', 'config', 'nickname=test_powerline'], cwd='bzr_repo')
		call(['bzr', 'config', 'create_signatures=0'], cwd='bzr_repo')


def tearDownModule():
	global old_cwd
	global old_HGRCPATH
	for repo_dir in (['git_repo'] + (['hg_repo'] if use_mercurial else []) + (['bzr_repo'] if use_bzr else [])):
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
