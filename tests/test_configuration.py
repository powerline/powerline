# vim:fileencoding=utf-8:noet

'''Dynamic configuration files tests.'''


import tests.vim as vim_module
import sys
import os
import json
from tests.lib import Args, urllib_read, replace_attr
from tests import TestCase


VBLOCK = chr(ord('V') - 0x40)
SBLOCK = chr(ord('S') - 0x40)


class TestConfig(TestCase):
	def test_vim(self):
		from powerline.vim import VimPowerline
		cfg_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'powerline', 'config_files')
		buffers = ((('bufoptions',), {'buftype': 'help'}), (('buffer', '[Command Line]'), {}), (('bufoptions',), {'buftype': 'quickfix'}))
		with open(os.path.join(cfg_path, 'config.json'), 'r') as f:
			self.assertEqual(len(buffers), len(json.load(f)['ext']['vim']['local_themes']))
		outputs = {}
		i = 0
		mode = None

		with VimPowerline() as powerline:
			def check_output(*args):
				out = powerline.render(*args + (0 if mode == 'nc' else 1,))
				if out in outputs:
					self.fail('Duplicate in set #{0} for mode {1!r} (previously defined in set #{2} for mode {3!r})'.format(i, mode, *outputs[out]))
				outputs[out] = (i, mode)

			with vim_module._with('buffer', 'foo.txt'):
				with vim_module._with('globals', powerline_config_path=cfg_path):
					exclude = set(('no', 'v', 'V', VBLOCK, 's', 'S', SBLOCK, 'R', 'Rv', 'c', 'cv', 'ce', 'r', 'rm', 'r?', '!'))
					try:
						for mode in ['n', 'nc', 'no', 'v', 'V', VBLOCK, 's', 'S', SBLOCK, 'i', 'R', 'Rv', 'c', 'cv', 'ce', 'r', 'rm', 'r?', '!']:
							if mode != 'nc':
								vim_module._start_mode(mode)
							check_output(1, 0)
							for args, kwargs in buffers:
								i += 1
								if mode in exclude:
									continue
								with vim_module._with(*args, **kwargs):
									check_output(1, 0)
					finally:
						vim_module._start_mode('n')

	def test_tmux(self):
		from powerline.segments import common
		from imp import reload
		reload(common)
		from powerline.shell import ShellPowerline
		with replace_attr(common, 'urllib_read', urllib_read):
			with ShellPowerline(Args(ext=['tmux']), run_once=False) as powerline:
				powerline.render()
			with ShellPowerline(Args(ext=['tmux']), run_once=False) as powerline:
				powerline.render()

	def test_zsh(self):
		from powerline.shell import ShellPowerline
		args = Args(last_pipe_status=[1, 0], ext=['shell'], renderer_module='zsh_prompt')
		with ShellPowerline(args, run_once=False) as powerline:
			powerline.render(segment_info={'args': args})
		with ShellPowerline(args, run_once=False) as powerline:
			powerline.render(segment_info={'args': args})

	def test_bash(self):
		from powerline.shell import ShellPowerline
		args = Args(last_exit_code=1, ext=['shell'], renderer_module='bash_prompt', config={'ext': {'shell': {'theme': 'default_leftonly'}}})
		with ShellPowerline(args, run_once=False) as powerline:
			powerline.render(segment_info={'args': args})
		with ShellPowerline(args, run_once=False) as powerline:
			powerline.render(segment_info={'args': args})

	def test_ipython(self):
		from powerline.ipython import IpythonPowerline

		class IpyPowerline(IpythonPowerline):
			path = None
			config_overrides = None
			theme_overrides = {}

		with IpyPowerline() as powerline:
			segment_info = Args(prompt_count=1)
			for prompt_type in ['in', 'in2', 'out', 'rewrite']:
				powerline.render(matcher_info=prompt_type, segment_info=segment_info)
				powerline.render(matcher_info=prompt_type, segment_info=segment_info)

	def test_wm(self):
		from powerline.segments import common
		from imp import reload
		reload(common)
		from powerline import Powerline
		with replace_attr(common, 'urllib_read', urllib_read):
			Powerline(ext='wm', renderer_module='pango_markup', run_once=True).render()
		reload(common)


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


if __name__ == '__main__':
	from tests import main
	main()
