# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.renderer import Renderer
from powerline.colorscheme import ATTR_BOLD, ATTR_ITALIC, ATTR_UNDERLINE


def attr_to_tmux_attr(attr):
	if attr is False:
		return ['nobold', 'noitalics', 'nounderscore']
	else:
		ret = []
		if attr & ATTR_BOLD:
			ret += ['bold']
		else:
			ret += ['nobold']
		if attr & ATTR_ITALIC:
			ret += ['italics']
		else:
			ret += ['noitalics']
		if attr & ATTR_UNDERLINE:
			ret += ['underscore']
		else:
			ret += ['nounderscore']
		return ret


class TmuxRenderer(Renderer):
	'''Powerline tmux segment renderer.'''

	character_translations = Renderer.character_translations.copy()
	character_translations[ord('#')] = '##[]'

	def hlstyle(self, fg=None, bg=None, attr=None):
		'''Highlight a segment.'''
		# We don’t need to explicitly reset attributes, so skip those calls
		if not attr and not bg and not fg:
			return ''
		tmux_attr = []
		if fg is not None:
			if fg is False or fg[0] is False:
				tmux_attr += ['fg=default']
			else:
				tmux_attr += ['fg=colour' + str(fg[0])]
		if bg is not None:
			if bg is False or bg[0] is False:
				tmux_attr += ['bg=default']
			else:
				tmux_attr += ['bg=colour' + str(bg[0])]
		if attr is not None:
			tmux_attr += attr_to_tmux_attr(attr)
		return '#[' + ','.join(tmux_attr) + ']'

	def get_segment_info(self, segment_info, mode):
		r = self.segment_info.copy()
		if segment_info:
			r.update(segment_info)
		if 'pane_id' in r:
			varname = 'TMUX_PWD_' + r['pane_id'].lstrip('%')
			if varname in r['environ']:
				r['getcwd'] = lambda: r['environ'][varname]
		r['mode'] = mode
		return r


renderer = TmuxRenderer
