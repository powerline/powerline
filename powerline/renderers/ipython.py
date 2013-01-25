# -*- coding: utf-8 -*-

from powerline.renderers.shell import ShellRenderer


# class IpythonRenderer(ShellRenderer):
	# '''Powerline ipython segment renderer.'''
	# def __init__(self, *args, **kwargs):
		# super(IpythonRenderer, self).__init__(*args, **kwargs)

	# def render(self, *args, **kwargs):
		# self.last_colors_str = ''
		# r = super(IpythonRenderer, self).render(*args, **kwargs)
		# return r.encode('utf-8'), self.last_colors_str

	# def hl(self, *args, **kwargs):
		# r = super(IpythonRenderer, self).hl(*args, **kwargs)
		# self.last_colors_str += r
		# return r

class IpythonRenderer(ShellRenderer):
	'''Powerline ipython segment renderer.'''
	def render(self, color=True, *args, **kwargs):
		self.color = color
		return super(IpythonRenderer, self).render(*args, **kwargs)

	def hl(self, *args, **kwargs):
		if not self.color:
			return ''
		else:
			return super(IpythonRenderer, self).hl(*args, **kwargs)
