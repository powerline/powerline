# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.renderers.shell import ShellRenderer


class ReadlineRenderer(ShellRenderer):
	'''Renderer useful for some applications that use readline
	'''
	escape_hl_start = '\x01'
	escape_hl_end = '\x02'


renderer = ReadlineRenderer
