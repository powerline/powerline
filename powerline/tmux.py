# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline import Powerline


class TmuxPowerline(Powerline):
	def init(self, config_paths):
		self.paths = config_paths
		return super(TmuxPowerline, self).init('tmux')

	def get_config_paths(self):
		if self.paths:
			return self.paths
		else:
			return super(TmuxPowerline, self).get_config_paths()
