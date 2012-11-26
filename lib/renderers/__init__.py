class SegmentRenderer:
	def hl(self, fg=None, bg=None, attr=None):
		raise NotImplementedError

from lib.renderers.terminal import TerminalSegmentRenderer
from lib.renderers.tmux import TmuxSegmentRenderer
from lib.renderers.vim import VimSegmentRenderer
