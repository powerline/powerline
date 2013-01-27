# -*- coding: utf-8 -*-

from powerline.renderers.shell import ShellRenderer


class IpythonRenderer(ShellRenderer):
	'''Powerline ipython segment renderer.'''
	def hl(self, *args, **kwargs):
		return '\x01'+super(IpythonRenderer, self).hl(*args, **kwargs)+'\x02'
