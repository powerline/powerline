# vim:fileencoding=utf-8:noet

from powerline.renderers.ipython import IPythonRenderer


class IPythonPromptRenderer(IPythonRenderer):
	'''Powerline ipython prompt renderer'''
	escape_hl_start = '\x01'
	escape_hl_end = '\x02'


renderer = IPythonPromptRenderer
