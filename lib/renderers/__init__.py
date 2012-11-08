class SegmentRenderer:
	def fg(col):
		raise NotImplementedError

	def bg(col):
		raise NotImplementedError

from lib.renderers.terminal import TerminalSegmentRenderer
