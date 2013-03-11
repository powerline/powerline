# vim:fileencoding=utf-8:noet

from powerline.renderers.shell import ShellRenderer


class IpythonRenderer(ShellRenderer):
	'''Powerline ipython segment renderer.'''
	escape_hl_start = '\x01'
	escape_hl_end = '\x02'


renderer = IpythonRenderer
