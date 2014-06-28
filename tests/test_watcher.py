# vim:fileencoding=utf-8:noet
from __future__ import absolute_import, unicode_literals, print_function, division

from powerline.lib.watcher import create_file_watcher, create_tree_watcher, INotifyError
from powerline import get_fallback_logger
from powerline.lib.monotonic import monotonic

import shutil
from time import sleep
from functools import partial
import os

from tests import TestCase, SkipTest


INOTIFY_DIR = 'inotify' + os.environ.get('PYTHON', '')


class TestFilesystemWatchers(TestCase):
	def do_test_for_change(self, watcher, path):
		st = monotonic()
		while monotonic() - st < 1:
			if watcher(path):
				return
			sleep(0.1)
		self.fail('The change to {0} was not detected'.format(path))

	def test_file_watcher(self):
		try:
			w = create_file_watcher(pl=get_fallback_logger(), watcher_type='inotify')
		except INotifyError:
			raise SkipTest('This test is not suitable for a stat based file watcher')
		f1, f2, f3 = map(lambda x: os.path.join(INOTIFY_DIR, 'file%d' % x), (1, 2, 3))
		with open(f1, 'wb'):
			with open(f2, 'wb'):
				with open(f3, 'wb'):
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
		# Test that changing the inode of a file does not cause it to stop
		# being watched
		os.rename(f3, f2)
		self.do_test_for_change(w, f2)
		self.assertFalse(w(f2), 'Spurious change detected')
		os.utime(f2, None)
		self.do_test_for_change(w, f2)

	def test_tree_watcher(self):
		tw = create_tree_watcher(get_fallback_logger())
		subdir = os.path.join(INOTIFY_DIR, 'subdir')
		os.mkdir(subdir)
		if tw.watch(INOTIFY_DIR).is_dummy:
			raise SkipTest('No tree watcher available')
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


old_cwd = None


def setUpModule():
	global old_cwd
	old_cwd = os.getcwd()
	os.chdir(os.path.dirname(__file__))
	os.mkdir(INOTIFY_DIR)


def tearDownModule():
	for d in [INOTIFY_DIR]:
		for root, dirs, files in list(os.walk(d, topdown=False)):
			for file in files:
				os.remove(os.path.join(root, file))
			for dir in dirs:
				os.rmdir(os.path.join(root, dir))
		os.rmdir(d)
	os.chdir(old_cwd)


if __name__ == '__main__':
	from tests import main
	main()
