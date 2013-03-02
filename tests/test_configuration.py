# -*- coding: utf-8 -*-

'''Dynamic configuration files tests.'''


from unittest import TestCase
import tests.vim as vim_module
import sys
import os
import json
from .lib import Args, urllib_read
import tests.lib as lib


VBLOCK = chr(ord('V') - 0x40)
SBLOCK = chr(ord('S') - 0x40)


class TestConfig(TestCase):
	def test_vim(self):
		from powerline.vim import VimPowerline
		cfg_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'powerline', 'config_files')
		vim_module._g['powerline_config_path'] = cfg_path
		buffers = ((lambda: vim_module._set_bufoption('buftype', 'help'), lambda: vim_module._set_bufoption('buftype', '')),
			 (lambda: vim_module._edit('[Command Line]'), lambda: vim_module._bw()))
		with open(os.path.join(cfg_path, 'config.json'), 'r') as f:
			self.assertEqual(len(buffers), len(json.load(f)['ext']['vim']['local_themes']))
		outputs = {}
		i = 0
		mode = None
		powerline = VimPowerline()

		def check_output(*args):
			out = powerline.renderer.render(*args + (0 if mode == 'nc' else 1,))
			if out in outputs:
				self.fail('Duplicate in set #{0} for mode {1!r} (previously defined in set #{2} for mode {3!r})'.format(i, mode, *outputs[out]))
			outputs[out] = (i, mode)

		try:
			exclude = set(('no', 'v', 'V', VBLOCK, 's', 'S', SBLOCK, 'R', 'Rv', 'c', 'cv', 'ce', 'r', 'rm', 'r?', '!'))
			try:
				for mode in ['n', 'nc', 'no', 'v', 'V', VBLOCK, 's', 'S', SBLOCK, 'i', 'R', 'Rv', 'c', 'cv', 'ce', 'r', 'rm', 'r?', '!']:
					if mode != 'nc':
						vim_module._start_mode(mode)
					check_output(1, 0)
					for setup, teardown in buffers:
						i += 1
						if mode in exclude:
							continue
						setup()
						try:
							check_output(1, 0)
						finally:
							teardown()
			finally:
				vim_module._start_mode('n')
		finally:
			vim_module._g.pop('powerline_config_path')

	def test_tmux(self):
		import powerline.segments.common
		from imp import reload
		reload(powerline.segments.common)
		old_urllib_read = powerline.segments.common.urllib_read 
		powerline.segments.common.urllib_read = urllib_read
		from powerline.shell import ShellPowerline
		try:
			ShellPowerline(Args(ext=['tmux'])).renderer.render()
		finally:
			powerline.segments.common.urllib_read = old_urllib_read


old_cwd = None


def setUpModule():
	global old_cwd
	sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'path')))
	old_cwd = os.getcwd()
	from powerline.segments import vim
	globals()['vim'] = vim


def tearDownModule():
	global old_cwd
	os.chdir(old_cwd)
	old_cwd = None
	sys.path.pop(0)
