# vim:fileencoding=utf-8:noet

from powerline.renderers.shell import ShellRenderer


class FishPromptRenderer(ShellRenderer):
	'''Powerline fish prompt segment renderer.'''
	escape_hl_start = ''
	escape_hl_end = ''

	@staticmethod
	def escape(string):
		return string.replace('\\', '\\\\').replace('$', '\\$').replace('(', '\\(').replace(')', '\\)')


renderer = FishPromptRenderer
