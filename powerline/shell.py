# vim:fileencoding=UTF-8:ts=4:sw=4:sta:noet:sts=4:fdm=marker:ai
import argparse

from powerline import Powerline
from powerline.lib import mergedicts, parsedotval


def mergeargs(argvalue):
	if not argvalue:
		return None
	r = dict([argvalue[0]])
	for subval in argvalue[1:]:
		mergedicts(r, dict([subval]))
	return r


def get_argparser(description, parser=argparse.ArgumentParser):
	p = parser(description=description)
	a = p.add_argument
	a('ext', nargs=1)
	a('side', nargs='?', choices=('left', 'right'))
	a('-r', '--renderer_module', metavar='MODULE', type=str)
	a('-w', '--width', type=int)
	a('--last_exit_code', metavar='INT', type=int)
	a('--last_pipe_status', metavar='LIST', default='', type=lambda s: [int(status) for status in s.split()])
	a('-c', '--config', metavar='KEY.KEY=VALUE', type=parsedotval, action='append')
	a('-t', '--theme_option', metavar='THEME.KEY.KEY=VALUE', type=parsedotval, action='append')
	a('-p', '--config_path', metavar='PATH')
	return p


class ShellPowerline(Powerline):
	def __init__(self, args):
		self.args = args
		self.theme_option = mergeargs(args.theme_option) or {}
		super(ShellPowerline, self).__init__(args.ext[0], args.renderer_module)

	def get_segment_info(self):
		return self.args

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
