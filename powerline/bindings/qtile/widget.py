# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from libqtile.bar import CALCULATED
from libqtile.widget import TextBox

from powerline import Powerline


class QTilePowerline(Powerline):
	def do_setup(self, obj):
		obj.powerline = self


class PowerlineTextBox(TextBox):
	def __init__(self, timeout=2, text=' ', width=CALCULATED, side='right', **config):
		super(PowerlineTextBox, self).__init__(text, width, **config)
		self.side = side
		self.update_interval = timeout
		self.did_run_timer_setup = False
		powerline = QTilePowerline(ext='wm', renderer_module='pango_markup')
		powerline.setup(self)

	def update(self):
		if not self.configured:
			return True
		self.text = self.powerline.render(side=self.side).encode('utf-8')
		self.bar.draw()
		return True

	def cmd_update(self, text):
		self.update(text)

	def cmd_get(self):
		return self.text

	def timer_setup(self):
		if not self.did_run_timer_setup:
			self.did_run_timer_setup = True
			self.timeout_add(self.update_interval, self.update)

	def _configure(self, qtile, bar):
		super(PowerlineTextBox, self)._configure(qtile, bar)
		self.layout = self.drawer.textlayout(
			self.text,
			self.foreground,
			self.font,
			self.fontsize,
			self.fontshadow,
			markup=True,
		)
		self.timer_setup()


# TODO: Remove this at next major release
Powerline = PowerlineTextBox
