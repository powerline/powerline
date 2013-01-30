# -*- coding: utf-8 -*-

from libqtile import bar
from libqtile.widget import base

from powerline.core import Powerline as PowerlineCore


class Powerline(base._TextBox):
	def __init__(self, timeout=2, text=" ", width=bar.CALCULATED, **config):
		base._TextBox.__init__(self, text, width, **config)
		self.timeout_add(timeout, self.update)
		self.powerline = PowerlineCore(ext='wm', renderer_module='pango_markup')

	def update(self):
		self.text = self.powerline.renderer.render(side='right')
		self.bar.draw()

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
