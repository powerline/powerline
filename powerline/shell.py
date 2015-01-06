# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline import Powerline
from powerline.lib.dict import mergedicts


class ShellPowerline(Powerline):
	def init(self, args, **kwargs):
		self.args = args
		super(ShellPowerline, self).init(args.ext[0], args.renderer_module, **kwargs)

	def load_main_config(self):
		r = super(ShellPowerline, self).load_main_config()
		if self.args.config_override:
			mergedicts(r, self.args.config_override)
		return r

	def load_theme_config(self, name):
		r = super(ShellPowerline, self).load_theme_config(name)
		if self.args.theme_override and name in self.args.theme_override:
			mergedicts(r, self.args.theme_override[name])
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
