# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import shutil
import os

from time import sleep
from functools import partial
from errno import ENOENT

from powerline.lib.watcher import create_file_watcher, create_tree_watcher, INotifyError
from powerline.lib.watcher.uv import UvNotFound
from powerline import get_fallback_logger
from powerline.lib.monotonic import monotonic

from tests.modules import TestCase, SkipTest


INOTIFY_DIR = 'inotify' + os.path.basename(os.environ.get('PYTHON', ''))


def clear_dir(dir):
	for root, dirs, files in list(os.walk(dir, topdown=False)):
		for f in files:
			os.remove(os.path.join(root, f))
		for d in dirs:
			os.rmdir(os.path.join(root, d))


def set_watcher_tests(l):
	byte_tests = (('bytes', True), ('unicode', False))

	for btn, use_bytes in byte_tests:
		def test_inotify_file_watcher(self, use_bytes=use_bytes):
			try:
				w = create_file_watcher(pl=get_fallback_logger(), watcher_type='inotify')
			except INotifyError:
				raise SkipTest('This test is not suitable for a stat based file watcher')
			self.do_test_file_watcher(w, use_bytes)

		def test_uv_file_watcher(self, use_bytes=use_bytes):
			raise SkipTest('Uv watcher tests are not stable')
			try:
				w = create_file_watcher(pl=get_fallback_logger(), watcher_type='uv')
			except UvNotFound:
				raise SkipTest('Pyuv is not available')
			self.do_test_file_watcher(w, use_bytes)

		def test_inotify_tree_watcher(self, use_bytes=use_bytes):
			try:
				tw = create_tree_watcher(get_fallback_logger(), watcher_type='inotify')
			except INotifyError:
				raise SkipTest('INotify is not available')
			self.do_test_tree_watcher(tw, use_bytes)

		def test_uv_tree_watcher(self, use_bytes=use_bytes):
			raise SkipTest('Uv watcher tests are not stable')
			try:
				tw = create_tree_watcher(get_fallback_logger(), 'uv')
			except UvNotFound:
				raise SkipTest('Pyuv is not available')
			self.do_test_tree_watcher(tw, use_bytes)

		def test_inotify_file_watcher_is_watching(self, use_bytes=use_bytes):
			try:
				w = create_file_watcher(pl=get_fallback_logger(), watcher_type='inotify')
			except INotifyError:
				raise SkipTest('INotify is not available')
			self.do_test_file_watcher_is_watching(w, use_bytes)

		def test_stat_file_watcher_is_watching(self, use_bytes=use_bytes):
			w = create_file_watcher(pl=get_fallback_logger(), watcher_type='stat')
			self.do_test_file_watcher_is_watching(w, use_bytes)

		def test_uv_file_watcher_is_watching(self, use_bytes=use_bytes):
			try:
				w = create_file_watcher(pl=get_fallback_logger(), watcher_type='uv')
			except UvNotFound:
				raise SkipTest('Pyuv is not available')
			self.do_test_file_watcher_is_watching(w, use_bytes)

		for wt in ('uv', 'inotify'):
			l['test_{0}_file_watcher_{1}'.format(wt, btn)] = locals()['test_{0}_file_watcher'.format(wt)]
			l['test_{0}_tree_watcher_{1}'.format(wt, btn)] = locals()['test_{0}_tree_watcher'.format(wt)]
			l['test_{0}_file_watcher_is_watching_{1}'.format(wt, btn)] = (
				locals()['test_{0}_file_watcher_is_watching'.format(wt)])
		l['test_{0}_file_watcher_is_watching_{1}'.format('stat', btn)] = (
			locals()['test_{0}_file_watcher_is_watching'.format('stat')])


class TestFilesystemWatchers(TestCase):
	def do_test_for_change(self, watcher, path):
		st = monotonic()
		while monotonic() - st < 1:
			if watcher(path):
				return
			sleep(0.1)
		self.fail('The change to {0} was not detected'.format(path))

	def do_test_file_watcher(self, w, use_bytes=False):
		try:
			f1, f2, f3 = map(lambda x: os.path.join(INOTIFY_DIR, 'file%d' % x), (1, 2, 3))
			ne = os.path.join(INOTIFY_DIR, 'notexists')
			if use_bytes:
				f1 = f1.encode('utf-8')
				f2 = f2.encode('utf-8')
				f3 = f3.encode('utf-8')
				ne = ne.encode('utf-8')
			with open(f1, 'wb'):
				with open(f2, 'wb'):
					with open(f3, 'wb'):
						pass
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
			# Test that changing the inode of a file does not cause it to stop
			# being watched
			os.rename(f3, f2)
			self.do_test_for_change(w, f2)
			self.assertFalse(w(f2), 'Spurious change detected')
			os.utime(f2, None)
			self.do_test_for_change(w, f2)
		finally:
			clear_dir(INOTIFY_DIR)

	def do_test_tree_watcher(self, tw, use_bytes=False):
		try:
			inotify_dir = INOTIFY_DIR
			subdir = os.path.join(inotify_dir, 'subdir')
			t1 = os.path.join(inotify_dir, 'tree1')
			ts1 = os.path.join(subdir, 'tree1')
			suffix = '1'
			f = os.path.join(subdir, 'f')
			if use_bytes:
				inotify_dir = inotify_dir.encode('utf-8')
				subdir = subdir.encode('utf-8')
				t1 = t1.encode('utf-8')
				ts1 = ts1.encode('utf-8')
				suffix = suffix.encode('utf-8')
				f = f.encode('utf-8')
			os.mkdir(subdir)
			try:
				if tw.watch(inotify_dir).is_dummy:
					raise SkipTest('No tree watcher available')
			except UvNotFound:
				raise SkipTest('Pyuv is not available')
			except INotifyError:
				raise SkipTest('INotify is not available')
			self.assertTrue(tw(inotify_dir))
			self.assertFalse(tw(inotify_dir))
			changed = partial(self.do_test_for_change, tw, inotify_dir)
			open(t1, 'w').close()
			changed()
			open(ts1, 'w').close()
			changed()
			os.unlink(ts1)
			changed()
			os.rmdir(subdir)
			changed()
			os.mkdir(subdir)
			changed()
			os.rename(subdir, subdir + suffix)
			changed()
			shutil.rmtree(subdir + suffix)
			changed()
			os.mkdir(subdir)
			open(f, 'w').close()
			changed()
			with open(f, 'a') as s:
				s.write(' ')
			changed()
			os.rename(f, f + suffix)
			changed()
		finally:
			clear_dir(inotify_dir)

	def do_test_file_watcher_is_watching(self, w, use_bytes=False):
		try:
			f1, f2, f3 = map(lambda x: os.path.join(INOTIFY_DIR, 'file%d' % x), (1, 2, 3))
			ne = os.path.join(INOTIFY_DIR, 'notexists')
			if use_bytes:
				f1 = f1.encode('utf-8')
				f2 = f2.encode('utf-8')
				f3 = f3.encode('utf-8')
				ne = ne.encode('utf-8')
			with open(f1, 'wb'):
				with open(f2, 'wb'):
					with open(f3, 'wb'):
						pass
			self.assertRaises(OSError, w, ne)
			try:
				w(ne)
			except OSError as e:
				self.assertEqual(e.errno, ENOENT)
			self.assertTrue(w(f1))
			self.assertFalse(w.is_watching(ne))
			self.assertTrue(w.is_watching(f1))
			self.assertFalse(w.is_watching(f2))
		finally:
			clear_dir(INOTIFY_DIR)

	set_watcher_tests(locals())


old_cwd = None


def setUpModule():
	global old_cwd
	old_cwd = os.getcwd()
	os.chdir(os.path.dirname(os.path.dirname(__file__)))
	os.mkdir(INOTIFY_DIR)


def tearDownModule():
	shutil.rmtree(INOTIFY_DIR)
	os.chdir(old_cwd)


if __name__ == '__main__':
	from tests.modules import main
	main()
