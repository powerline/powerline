# -*- coding: utf-8 -*-

from powerline.renderers.shell import ShellRenderer


class IpythonRenderer(ShellRenderer):
	'''Powerline ipython segment renderer.'''
	def render(self, *args, **kwargs):
		r = super(IpythonRenderer, self).render(*args, **kwargs)
		return r.encode('utf-8')
