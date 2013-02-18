# -*- coding: utf-8 -*-

from powerline import Powerline
from powerline.lib import mergedicts


def mergeargs(argvalue):
	if not argvalue:
		return None
	l = argvalue
	r = dict([argvalue[0]])
	for subval in argvalue[1:]:
		mergedicts(r, dict([subval]))
	return r


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
