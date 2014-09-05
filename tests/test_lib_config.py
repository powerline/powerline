# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os

from powerline.lib.config import ConfigLoader

from tests import TestCase
from tests.lib.fsconfig import FSTree


FILE_ROOT = os.path.join(os.path.dirname(__file__), 'cfglib')


class LoadedList(list):
	def pop_all(self):
		try:
			return self[:]
		finally:
			self[:] = ()


loaded = LoadedList()


def on_load(key):
	loaded.append(key)


def check_file(path):
	if os.path.exists(path):
		return path
	else:
		raise IOError


class TestLoaderCondition(TestCase):
	def test_update_missing(self):
		loader = ConfigLoader(run_once=True)
		fpath = os.path.join(FILE_ROOT, 'file.json')
		self.assertRaises(IOError, loader.load, fpath)
		loader.register_missing(check_file, on_load, fpath)
		loader.update()  # This line must not raise IOError
		with FSTree({'file': {'test': 1}}, root=FILE_ROOT):
			loader.update()
			self.assertEqual(loader.load(fpath), {'test': 1})
			self.assertEqual(loaded.pop_all(), [fpath])


if __name__ == '__main__':
	from tests import main
	main()
