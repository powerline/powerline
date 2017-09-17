# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import threading
import os
import sys
import re
import shutil
import unicodedata

from time import sleep
from subprocess import call, PIPE

from powerline.lib import add_divider_highlight_group
from powerline.lib.dict import mergedicts, REMOVE_THIS_KEY
from powerline.lib.humanize_bytes import humanize_bytes
from powerline.lib.vcs import guess, get_fallback_create_watcher
from powerline.lib.threaded import ThreadedSegment, KwThreadedSegment
from powerline.lib.monotonic import monotonic
from powerline.lib.vcs.git import git_directory
from powerline.lib.shell import run_cmd

import powerline.lib.unicode as plu

from tests.modules.lib import Pl, replace_attr
from tests.modules import TestCase, SkipTest


try:
	__import__('bzrlib')
except ImportError:
	use_bzr = False
else:
	use_bzr = True

try:
	__import__('hglib')
except ImportError:
	use_mercurial = False
else:
	use_mercurial = True


GIT_REPO = 'git_repo'
HG_REPO = 'hg_repo'
BZR_REPO = 'bzr_repo'


def thread_number():
	return len(threading.enumerate())


class TestShell(TestCase):
	def test_run_cmd(self):
		pl = Pl()
		self.assertEqual(run_cmd(pl, ['xxx_nonexistent_command_xxx']), None)
		self.assertEqual(len(pl.exceptions), 1)
		pl = Pl()
		self.assertEqual(run_cmd(pl, ['echo', '  test  ']), 'test')
		self.assertFalse(pl)
		self.assertEqual(run_cmd(pl, ['echo', '  test  '], strip=True), 'test')
		self.assertFalse(pl)
		self.assertEqual(run_cmd(pl, ['echo', '  test  '], strip=False), '  test  \n')
		self.assertFalse(pl)
		self.assertEqual(run_cmd(pl, ['cat'], stdin='test'), 'test')
		self.assertFalse(pl)
		self.assertEqual(run_cmd(pl, ['sh', '-c', 'cat >&2'], stdin='test'), '')
		self.assertFalse(pl)


class TestThreaded(TestCase):
	def test_threaded_segment(self):
		log = []
		pl = Pl()
		updates = [(None,)]
		lock = threading.Lock()
		event = threading.Event()
		block_event = threading.Event()

		class TestSegment(ThreadedSegment):
			interval = 10

			def set_state(self, **kwargs):
				event.clear()
				log.append(('set_state', kwargs))
				return super(TestSegment, self).set_state(**kwargs)

			def update(self, update_value):
				block_event.wait()
				event.set()
				# Make sleep first to prevent some race conditions
				log.append(('update', update_value))
				with lock:
					ret = updates[0]
				if isinstance(ret, Exception):
					raise ret
				else:
					return ret[0]

			def render(self, update, **kwargs):
				log.append(('render', update, kwargs))
				if isinstance(update, Exception):
					raise update
				else:
					return update

		# Non-threaded tests
		segment = TestSegment()
		block_event.set()
		updates[0] = (None,)
		self.assertEqual(segment(pl=pl), None)
		self.assertEqual(thread_number(), 1)
		self.assertEqual(log, [
			('set_state', {}),
			('update', None),
			('render', None, {'pl': pl, 'update_first': True}),
		])
		log[:] = ()

		segment = TestSegment()
		block_event.set()
		updates[0] = ('abc',)
		self.assertEqual(segment(pl=pl), 'abc')
		self.assertEqual(thread_number(), 1)
		self.assertEqual(log, [
			('set_state', {}),
			('update', None),
			('render', 'abc', {'pl': pl, 'update_first': True}),
		])
		log[:] = ()

		segment = TestSegment()
		block_event.set()
		updates[0] = ('abc',)
		self.assertEqual(segment(pl=pl, update_first=False), 'abc')
		self.assertEqual(thread_number(), 1)
		self.assertEqual(log, [
			('set_state', {}),
			('update', None),
			('render', 'abc', {'pl': pl, 'update_first': False}),
		])
		log[:] = ()

		segment = TestSegment()
		block_event.set()
		updates[0] = ValueError('abc')
		self.assertEqual(segment(pl=pl), None)
		self.assertEqual(thread_number(), 1)
		self.assertEqual(len(pl.exceptions), 1)
		self.assertEqual(log, [
			('set_state', {}),
			('update', None),
		])
		log[:] = ()
		pl.exceptions[:] = ()

		segment = TestSegment()
		block_event.set()
		updates[0] = (TypeError('def'),)
		self.assertRaises(TypeError, segment, pl=pl)
		self.assertEqual(thread_number(), 1)
		self.assertEqual(log, [
			('set_state', {}),
			('update', None),
			('render', updates[0][0], {'pl': pl, 'update_first': True}),
		])
		log[:] = ()

		# Threaded tests
		segment = TestSegment()
		block_event.clear()
		kwargs = {'pl': pl, 'update_first': False, 'other': 1}
		with lock:
			updates[0] = ('abc',)
		segment.startup(**kwargs)
		ret = segment(**kwargs)
		self.assertEqual(thread_number(), 2)
		block_event.set()
		event.wait()
		segment.shutdown_event.set()
		segment.thread.join()
		self.assertEqual(ret, None)
		self.assertEqual(log, [
			('set_state', {'update_first': False, 'other': 1}),
			('render', None, {'pl': pl, 'update_first': False, 'other': 1}),
			('update', None),
		])
		log[:] = ()

		segment = TestSegment()
		block_event.set()
		kwargs = {'pl': pl, 'update_first': True, 'other': 1}
		with lock:
			updates[0] = ('def',)
		segment.startup(**kwargs)
		ret = segment(**kwargs)
		self.assertEqual(thread_number(), 2)
		segment.shutdown_event.set()
		segment.thread.join()
		self.assertEqual(ret, 'def')
		self.assertEqual(log, [
			('set_state', {'update_first': True, 'other': 1}),
			('update', None),
			('render', 'def', {'pl': pl, 'update_first': True, 'other': 1}),
		])
		log[:] = ()

		segment = TestSegment()
		block_event.set()
		kwargs = {'pl': pl, 'update_first': True, 'interval': 0.2}
		with lock:
			updates[0] = ('abc',)
		segment.startup(**kwargs)
		start = monotonic()
		ret1 = segment(**kwargs)
		with lock:
			updates[0] = ('def',)
		self.assertEqual(thread_number(), 2)
		sleep(0.5)
		ret2 = segment(**kwargs)
		segment.shutdown_event.set()
		segment.thread.join()
		end = monotonic()
		duration = end - start
		self.assertEqual(ret1, 'abc')
		self.assertEqual(ret2, 'def')
		self.assertEqual(log[:5], [
			('set_state', {'update_first': True, 'interval': 0.2}),
			('update', None),
			('render', 'abc', {'pl': pl, 'update_first': True, 'interval': 0.2}),
			('update', 'abc'),
			('update', 'def'),
		])
		num_runs = len([e for e in log if e[0] == 'update'])
		self.assertAlmostEqual(duration / 0.2, num_runs, delta=1)
		log[:] = ()

		segment = TestSegment()
		block_event.set()
		kwargs = {'pl': pl, 'update_first': True, 'interval': 0.2}
		with lock:
			updates[0] = ('ghi',)
		segment.startup(**kwargs)
		start = monotonic()
		ret1 = segment(**kwargs)
		with lock:
			updates[0] = TypeError('jkl')
		self.assertEqual(thread_number(), 2)
		sleep(0.5)
		ret2 = segment(**kwargs)
		segment.shutdown_event.set()
		segment.thread.join()
		end = monotonic()
		duration = end - start
		self.assertEqual(ret1, 'ghi')
		self.assertEqual(ret2, None)
		self.assertEqual(log[:5], [
			('set_state', {'update_first': True, 'interval': 0.2}),
			('update', None),
			('render', 'ghi', {'pl': pl, 'update_first': True, 'interval': 0.2}),
			('update', 'ghi'),
			('update', 'ghi'),
		])
		num_runs = len([e for e in log if e[0] == 'update'])
		self.assertAlmostEqual(duration / 0.2, num_runs, delta=1)
		self.assertEqual(num_runs - 1, len(pl.exceptions))
		log[:] = ()

	def test_kw_threaded_segment(self):
		log = []
		pl = Pl()
		event = threading.Event()

		class TestSegment(KwThreadedSegment):
			interval = 10

			@staticmethod
			def key(_key=(None,), **kwargs):
				log.append(('key', _key, kwargs))
				return _key

			def compute_state(self, key):
				event.set()
				sleep(0.1)
				log.append(('compute_state', key))
				ret = key
				if isinstance(ret, Exception):
					raise ret
				else:
					return ret[0]

			def render_one(self, state, **kwargs):
				log.append(('render_one', state, kwargs))
				if isinstance(state, Exception):
					raise state
				else:
					return state

		# Non-threaded tests
		segment = TestSegment()
		event.clear()
		self.assertEqual(segment(pl=pl), None)
		self.assertEqual(thread_number(), 1)
		self.assertEqual(log, [
			('key', (None,), {'pl': pl}),
			('compute_state', (None,)),
			('render_one', None, {'pl': pl}),
		])
		log[:] = ()

		segment = TestSegment()
		kwargs = {'pl': pl, '_key': ('abc',), 'update_first': False}
		event.clear()
		self.assertEqual(segment(**kwargs), 'abc')
		kwargs.update(_key=('def',))
		self.assertEqual(segment(**kwargs), 'def')
		self.assertEqual(thread_number(), 1)
		self.assertEqual(log, [
			('key', ('abc',), {'pl': pl}),
			('compute_state', ('abc',)),
			('render_one', 'abc', {'pl': pl, '_key': ('abc',)}),
			('key', ('def',), {'pl': pl}),
			('compute_state', ('def',)),
			('render_one', 'def', {'pl': pl, '_key': ('def',)}),
		])
		log[:] = ()

		segment = TestSegment()
		kwargs = {'pl': pl, '_key': ValueError('xyz'), 'update_first': False}
		event.clear()
		self.assertEqual(segment(**kwargs), None)
		self.assertEqual(thread_number(), 1)
		self.assertEqual(log, [
			('key', kwargs['_key'], {'pl': pl}),
			('compute_state', kwargs['_key']),
		])
		log[:] = ()

		segment = TestSegment()
		kwargs = {'pl': pl, '_key': (ValueError('abc'),), 'update_first': False}
		event.clear()
		self.assertRaises(ValueError, segment, **kwargs)
		self.assertEqual(thread_number(), 1)
		self.assertEqual(log, [
			('key', kwargs['_key'], {'pl': pl}),
			('compute_state', kwargs['_key']),
			('render_one', kwargs['_key'][0], {'pl': pl, '_key': kwargs['_key']}),
		])
		log[:] = ()

		# Threaded tests
		segment = TestSegment()
		kwargs = {'pl': pl, 'update_first': False, '_key': ('_abc',)}
		event.clear()
		segment.startup(**kwargs)
		ret = segment(**kwargs)
		self.assertEqual(thread_number(), 2)
		segment.shutdown_event.set()
		segment.thread.join()
		self.assertEqual(ret, None)
		self.assertEqual(log[:2], [
			('key', kwargs['_key'], {'pl': pl}),
			('render_one', None, {'pl': pl, '_key': kwargs['_key']}),
		])
		self.assertLessEqual(len(log), 3)
		if len(log) > 2:
			self.assertEqual(log[2], ('compute_state', kwargs['_key']))
		log[:] = ()

		segment = TestSegment()
		kwargs = {'pl': pl, 'update_first': True, '_key': ('_abc',)}
		event.clear()
		segment.startup(**kwargs)
		ret1 = segment(**kwargs)
		kwargs.update(_key=('_def',))
		ret2 = segment(**kwargs)
		self.assertEqual(thread_number(), 2)
		segment.shutdown_event.set()
		segment.thread.join()
		self.assertEqual(ret1, '_abc')
		self.assertEqual(ret2, '_def')
		self.assertEqual(log, [
			('key', ('_abc',), {'pl': pl}),
			('compute_state', ('_abc',)),
			('render_one', '_abc', {'pl': pl, '_key': ('_abc',)}),
			('key', ('_def',), {'pl': pl}),
			('compute_state', ('_def',)),
			('render_one', '_def', {'pl': pl, '_key': ('_def',)}),
		])
		log[:] = ()


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
		mergedicts(d, {'abc': {'def': REMOVE_THIS_KEY}})
		self.assertEqual(d, {'abc': {'mno': 'pqr'}})

	def test_add_divider_highlight_group(self):
		def decorated_function_name(**kwargs):
			return str(kwargs)
		func = add_divider_highlight_group('hl_group')(decorated_function_name)
		self.assertEqual(func.__name__, 'decorated_function_name')
		self.assertEqual(func(kw={}), [{'contents': repr({str('kw'): {}}), 'divider_highlight_group': 'hl_group'}])

	def test_humanize_bytes(self):
		self.assertEqual(humanize_bytes(0), '0 B')
		self.assertEqual(humanize_bytes(1), '1 B')
		self.assertEqual(humanize_bytes(1, suffix='bit'), '1 bit')
		self.assertEqual(humanize_bytes(1000, si_prefix=True), '1 kB')
		self.assertEqual(humanize_bytes(1024, si_prefix=True), '1 kB')
		self.assertEqual(humanize_bytes(1000000000, si_prefix=True), '1.00 GB')
		self.assertEqual(humanize_bytes(1000000000, si_prefix=False), '953.7 MiB')


width_data = {
	'N': 1,          # Neutral
	'Na': 1,         # Narrow
	'A': 1,          # Ambigious
	'H': 1,          # Half-width
	'W': 2,          # Wide
	'F': 2,          # Fullwidth
}


class TestUnicode(TestCase):
	def assertStringsIdentical(self, s1, s2):
		self.assertTrue(type(s1) is type(s2), msg='string types differ')
		self.assertEqual(s1, s2)

	def test_unicode(self):
		self.assertTrue(type('abc') is plu.unicode)

	def test_unichr(self):
		self.assertStringsIdentical('\U0010FFFF', plu.unichr(0x10FFFF))
		self.assertStringsIdentical('\uFFFF', plu.unichr(0xFFFF))
		self.assertStringsIdentical('\x20', plu.unichr(0x20))

	def test_u(self):
		self.assertStringsIdentical('Test', plu.u('Test'))
		self.assertStringsIdentical('Test', plu.u(b'Test'))
		self.assertStringsIdentical('«»', plu.u(b'\xC2\xAB\xC2\xBB'))
		self.assertRaises(UnicodeDecodeError, plu.u, b'\xFF')

	def test_tointiter(self):
		self.assertEqual([1, 2, 3], list(plu.tointiter(b'\x01\x02\x03')))

	def test_decode_error(self):
		self.assertStringsIdentical('<FF>', b'\xFF'.decode('utf-8', 'powerline_decode_error'))
		self.assertStringsIdentical('abc', b'abc'.decode('utf-8', 'powerline_decode_error'))

	def test_register_strwidth_error(self):
		ename = plu.register_strwidth_error(lambda s: 3)
		self.assertStringsIdentical(b'???', 'Ａ'.encode('latin1', ename))
		self.assertStringsIdentical(b'abc', 'abc'.encode('latin1', ename))

	def test_out_u(self):
		self.assertStringsIdentical('abc', plu.out_u('abc'))
		self.assertStringsIdentical('abc', plu.out_u(b'abc'))
		self.assertRaises(TypeError, plu.out_u, None)

	def test_safe_unicode(self):
		self.assertStringsIdentical('abc', plu.safe_unicode('abc'))
		self.assertStringsIdentical('abc', plu.safe_unicode(b'abc'))
		self.assertStringsIdentical('«»', plu.safe_unicode(b'\xc2\xab\xc2\xbb'))
		with replace_attr(plu, 'get_preferred_output_encoding', lambda: 'latin1'):
			self.assertStringsIdentical('ÿ', plu.safe_unicode(b'\xFF'))
		self.assertStringsIdentical('None', plu.safe_unicode(None))

		class FailingStr(object):
			def __str__(self):
				raise NotImplementedError('Fail!')

		self.assertStringsIdentical('Fail!', plu.safe_unicode(FailingStr()))

	def test_FailedUnicode(self):
		self.assertTrue(isinstance(plu.FailedUnicode('abc'), plu.unicode))
		self.assertEqual('abc', plu.FailedUnicode('abc'))

	def test_string(self):
		self.assertStringsIdentical(str('abc'), plu.string('abc'))
		self.assertStringsIdentical(str('abc'), plu.string(b'abc'))

	def test_surrogate_pair_to_character(self):
		self.assertEqual(0x1F48E, plu.surrogate_pair_to_character(0xD83D, 0xDC8E))

	def test_strwidth_ucs_4(self):
		self.assertEqual(4, plu.strwidth_ucs_4(width_data, 'abcd'))
		self.assertEqual(4, plu.strwidth_ucs_4(width_data, 'ＡＢ'))
		if sys.maxunicode < 0x10FFFF:
			raise SkipTest('Can only test strwidth_ucs_4 in UCS-4 Pythons')

		self.assertEqual(1, plu.strwidth_ucs_4(width_data, '\U0001F063'))

	def test_strwidth_ucs_2(self):
		self.assertEqual(4, plu.strwidth_ucs_2(width_data, 'abcd'))
		self.assertEqual(4, plu.strwidth_ucs_2(width_data, 'ＡＢ'))
		if not sys.maxunicode < 0x10FFFF:
			raise SkipTest('Can only test strwidth_ucs_2 in UCS-2 Pythons')
		self.assertEqual(1, plu.strwidth_ucs_2(width_data, '\ud83c\udc30'))


class TestVCS(TestCase):
	def do_branch_rename_test(self, repo, q):
		st = monotonic()
		while monotonic() - st < 1:
			# Give inotify time to deliver events
			ans = repo.branch()
			if hasattr(q, '__call__'):
				if q(ans):
					break
			else:
				if ans == q:
					break
			sleep(0.01)
		if hasattr(q, '__call__'):
			self.assertTrue(q(ans))
		else:
			self.assertEqual(ans, q)

	def test_git(self):
		create_watcher = get_fallback_create_watcher()
		repo = guess(path=GIT_REPO, create_watcher=create_watcher)
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
		try:
			call(['git', 'branch', 'branch1'], cwd=GIT_REPO)
			call(['git', 'checkout', '-q', 'branch1'], cwd=GIT_REPO)
			self.do_branch_rename_test(repo, 'branch1')
			call(['git', 'branch', 'branch2'], cwd=GIT_REPO)
			call(['git', 'checkout', '-q', 'branch2'], cwd=GIT_REPO)
			self.do_branch_rename_test(repo, 'branch2')
			call(['git', 'checkout', '-q', '--detach', 'branch1'], cwd=GIT_REPO)
			self.do_branch_rename_test(repo, lambda b: re.match(r'^[a-f0-9]+$', b))
		finally:
			call(['git', 'checkout', '-q', 'master'], cwd=GIT_REPO)
		# Test stashing
		self.assertEqual(repo.stash(), 0)

		def stash_save():
			with open(os.path.join(GIT_REPO, 'file'), 'w') as f:
				f.write('abc')
			return call(['git', 'stash', '-u'], cwd=GIT_REPO, stdout=PIPE)

		def stash_drop():
			return call(['git', 'stash', 'drop'], cwd=GIT_REPO, stdout=PIPE)

		def stash_list():
			return call(['git', 'stash', 'list'], cwd=GIT_REPO, stdout=PIPE)

		try:
			stash_save()
			self.assertEqual(repo.stash(), 1)
			stash_save()
			self.assertEqual(repo.stash(), 2)
			stash_drop()
			self.assertEqual(repo.stash(), 1)
			stash_drop()
			self.assertEqual(repo.stash(), 0)
		finally:
			while stash_list():
			    stash_drop()

	def test_git_sym(self):
		create_watcher = get_fallback_create_watcher()
		dotgit = os.path.join(GIT_REPO, '.git')
		spacegit = os.path.join(GIT_REPO, ' .git ')
		os.rename(dotgit, spacegit)
		try:
			with open(dotgit, 'w') as F:
				F.write('gitdir:  .git \n')
			gitdir = git_directory(GIT_REPO)
			self.assertTrue(os.path.isdir(gitdir))
			self.assertEqual(gitdir, os.path.abspath(spacegit))
			repo = guess(path=GIT_REPO, create_watcher=create_watcher)
			self.assertEqual(repo.branch(), 'master')
		finally:
			os.remove(dotgit)
			os.rename(spacegit, dotgit)

	def test_mercurial(self):
		if not use_mercurial:
			raise SkipTest('Mercurial is not available')
		create_watcher = get_fallback_create_watcher()
		repo = guess(path=HG_REPO, create_watcher=create_watcher)
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

	def test_bzr(self):
		if not use_bzr:
			raise SkipTest('Bazaar is not available')
		create_watcher = get_fallback_create_watcher()
		repo = guess(path=BZR_REPO, create_watcher=create_watcher)
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
			repo = guess(path=d, create_watcher=create_watcher)
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
			repo = guess(path=d, create_watcher=create_watcher)
			self.do_branch_rename_test(repo, y)
			if x == 'b1':
				self.assertFalse(repo.status())
			else:
				self.assertTrue(repo.status())

	@classmethod
	def setUpClass(cls):
		cls.powerline_old_cwd = os.getcwd()
		os.chdir(os.path.dirname(os.path.dirname(__file__)))
		call(['git', 'init', '--quiet', GIT_REPO])
		assert os.path.isdir(GIT_REPO)
		call(['git', 'config', '--local', 'user.name', 'Foo'], cwd=GIT_REPO)
		call(['git', 'config', '--local', 'user.email', 'bar@example.org'], cwd=GIT_REPO)
		call(['git', 'commit', '--allow-empty', '--message', 'Initial commit', '--quiet'], cwd=GIT_REPO)
		if use_mercurial:
			cls.powerline_old_HGRCPATH = os.environ.get('HGRCPATH')
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

	@classmethod
	def tearDownClass(cls):
		for repo_dir in [GIT_REPO] + ([HG_REPO] if use_mercurial else []) + ([BZR_REPO] if use_bzr else []):
			shutil.rmtree(repo_dir)
		if use_mercurial:
			if cls.powerline_old_HGRCPATH is None:
				os.environ.pop('HGRCPATH')
			else:
				os.environ['HGRCPATH'] = cls.powerline_old_HGRCPATH
		os.chdir(cls.powerline_old_cwd)


if __name__ == '__main__':
	from tests.modules import main
	main()
