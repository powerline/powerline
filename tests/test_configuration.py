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
		buffers = (
			(('bufoptions',), {'buftype': 'help'}),
			(('bufname', '[Command Line]'), {}),
			(('bufoptions',), {'buftype': 'quickfix'}),
		)
		with open(os.path.join(cfg_path, 'config.json'), 'r') as f:
			local_themes_raw = json.load(f)['ext']['vim']['local_themes']
			# Don't run tests on external/plugin segments
			local_themes = dict((k, v) for (k, v) in local_themes_raw.items() if not '.' in k)
			self.assertEqual(len(buffers), len(local_themes))
		outputs = {}
		i = 0

		with vim_module._with('split'):
			with VimPowerline() as powerline:
				def check_output(mode, args, kwargs):
					if mode == 'nc':
						window = vim_module.windows[0]
						window_id = 2
					else:
						vim_module._start_mode(mode)
						window = vim_module.current.window
						window_id = 1
					winnr = window.number
					out = powerline.render(window, window_id, winnr)
					if out in outputs:
						self.fail('Duplicate in set #{0} ({1}) for mode {2!r} (previously defined in set #{3} ({4!r}) for mode {5!r})'.format(i, (args, kwargs), mode, *outputs[out]))
					outputs[out] = (i, (args, kwargs), mode)

				with vim_module._with('bufname', '/tmp/foo.txt'):
					with vim_module._with('globals', powerline_config_path=cfg_path):
						exclude = set(('no', 'v', 'V', VBLOCK, 's', 'S', SBLOCK, 'R', 'Rv', 'c', 'cv', 'ce', 'r', 'rm', 'r?', '!'))
						try:
							for mode in ['n', 'nc', 'no', 'v', 'V', VBLOCK, 's', 'S', SBLOCK, 'i', 'R', 'Rv', 'c', 'cv', 'ce', 'r', 'rm', 'r?', '!']:
								check_output(mode, None, None)
								for args, kwargs in buffers:
									i += 1
									if mode in exclude:
										continue
									with vim_module._with(*args, **kwargs):
										check_output(mode, args, kwargs)
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
