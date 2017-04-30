# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os
import sys

from functools import partial

import tests.modules.vim as vim_module

from tests.modules.lib import Pl
from tests.modules import TestCase


class TestVim(TestCase):
	def test_single_tab(self):
		pl = Pl()
		single_tab = partial(self.vim.single_tab, pl=pl, segment_info=None, mode=None)
		with vim_module._with('tabpage'):
			self.assertEqual(single_tab(), False)
		self.assertEqual(single_tab(), True)

	@classmethod
	def setUpClass(cls):
		sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'vim_sys_path')))
		from powerline.selectors import vim
		cls.vim = vim

	@classmethod
	def tearDownClass(cls):
		sys.path.pop(0)


if __name__ == '__main__':
	from tests.modules import main
	main()
