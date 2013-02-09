# -*- coding: utf-8 -*-

from powerline.renderers.shell import ShellRenderer


class IpythonRenderer(ShellRenderer):
	'''Powerline ipython segment renderer.'''
	def hlstyle(self, *args, **kwargs):
		return '\x01' + super(IpythonRenderer, self).hlstyle(*args, **kwargs) + '\x02'
