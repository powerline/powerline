# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from libqtile import bar
from libqtile.widget import base

from powerline import Powerline as PowerlineCore


class Powerline(base._TextBox):
	def __init__(self, timeout=2, text=' ', width=bar.CALCULATED, **config):
		base._TextBox.__init__(self, text, width, **config)
		self.timeout_add(timeout, self.update)
		self.powerline = PowerlineCore(ext='wm', renderer_module='pango_markup')

	def update(self):
		if not self.configured:
			return True
		self.text = self.powerline.render(side='right')
		self.bar.draw()
		return True

	def cmd_update(self, text):
		self.update(text)

	def cmd_get(self):
		return self.text

	def _configure(self, qtile, bar):
		base._TextBox._configure(self, qtile, bar)
		self.layout = self.drawer.textlayout(
			self.text,
			self.foreground,
			self.font,
			self.fontsize,
			self.fontshadow,
			markup=True)
