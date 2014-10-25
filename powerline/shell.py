# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline import Powerline
from powerline.lib import mergedicts


class ShellPowerline(Powerline):
	def init(self, args, **kwargs):
		self.args = args
		self.theme_option = args.theme_option
		super(ShellPowerline, self).init(args.ext[0], args.renderer_module, **kwargs)

	def load_main_config(self):
		r = super(ShellPowerline, self).load_main_config()
		if self.args.config:
			mergedicts(r, self.args.config)
		return r

	def load_theme_config(self, name):
		r = super(ShellPowerline, self).load_theme_config(name)
		if self.theme_option and name in self.theme_option:
			mergedicts(r, self.theme_option[name])
		return r

	def get_config_paths(self):
		return self.args.config_path or super(ShellPowerline, self).get_config_paths()

	def get_local_themes(self, local_themes):
		if not local_themes:
			return {}

		return dict((
			(key, {'config': self.load_theme_config(val)})
			for key, val in local_themes.items()
		))

	def do_setup(self, obj):
		obj.powerline = self
