# vim:fileencoding=utf-8:noet

from powerline import Powerline
from powerline.lib import mergedicts, parsedotval


def mergeargs(argvalue):
	if not argvalue:
		return None
	r = dict([argvalue[0]])
	for subval in argvalue[1:]:
		mergedicts(r, dict([subval]))
	return r


class ShellPowerline(Powerline):
	def __init__(self, args, **kwargs):
		self.args = args
		self.theme_option = mergeargs(args.theme_option) or {}
		super(ShellPowerline, self).__init__(args.ext[0], args.renderer_module, **kwargs)

	def load_main_config(self):
		r = super(ShellPowerline, self).load_main_config()
		if self.args.config:
			mergedicts(r, mergeargs(self.args.config))
		return r

	def load_theme_config(self, name):
		r = super(ShellPowerline, self).load_theme_config(name)
		if name in self.theme_option:
			mergedicts(r, self.theme_option[name])
		return r

	def get_config_paths(self):
		if self.args.config_path:
			return [self.args.config_path]
		else:
			return super(ShellPowerline, self).get_config_paths()


def get_argparser(parser=None, *args, **kwargs):
	if not parser:
		import argparse
		parser = argparse.ArgumentParser
	p = parser(*args, **kwargs)
	p.add_argument('ext', nargs=1)
	p.add_argument('side', nargs='?', choices=('left', 'right'))
	p.add_argument('-r', '--renderer_module', metavar='MODULE', type=str)
	p.add_argument('-w', '--width', type=int)
	p.add_argument('--last_exit_code', metavar='INT', type=int)
	p.add_argument('--last_pipe_status', metavar='LIST', default='', type=lambda s: [int(status) for status in s.split()])
	p.add_argument('-c', '--config', metavar='KEY.KEY=VALUE', type=parsedotval, action='append')
	p.add_argument('-t', '--theme_option', metavar='THEME.KEY.KEY=VALUE', type=parsedotval, action='append')
	p.add_argument('-p', '--config_path', metavar='PATH')
	return p
