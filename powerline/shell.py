# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline import Powerline
from powerline.lib.overrides import override_theme_config, override_main_config


class ShellPowerline(Powerline):
	def init(self, args, **kwargs):
		self.args = args
		super(ShellPowerline, self).init(args.ext[0], args.renderer_module, **kwargs)

	def load_main_config(self):
		return override_main_config(
			config=super(ShellPowerline, self).load_main_config(),
			override=self.args.config_override,
		)

	def load_theme_config(self, name):
		return override_theme_config(
			theme=super(ShellPowerline, self).load_theme_config(name),
			name=name,
			override=self.args.theme_override,
		)

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
