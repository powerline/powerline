# -*- coding: utf-8 -*-

from powerline.renderers.shell import ShellRenderer


class IpythonRenderer(ShellRenderer):
	'''Powerline ipython segment renderer.'''
	def render(self, color=True, *args, **kwargs):
		self.color = color
		return super(IpythonRenderer, self).render(*args, **kwargs)

	def hl(self, *args, **kwargs):
		if not self.color:
			return ''
		else:
			return '\x01' + super(IpythonRenderer, self).hl(*args, **kwargs) + '\x02'
