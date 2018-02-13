# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.renderer import Renderer
from powerline.colorscheme import ATTR_BOLD, ATTR_ITALIC, ATTR_UNDERLINE


def attrs_to_tmux_attrs(attrs):
	if attrs is False:
		return ['nobold', 'noitalics', 'nounderscore']
	else:
		ret = []
		if attrs & ATTR_BOLD:
			ret += ['bold']
		else:
			ret += ['nobold']
		if attrs & ATTR_ITALIC:
			ret += ['italics']
		else:
			ret += ['noitalics']
		if attrs & ATTR_UNDERLINE:
			ret += ['underscore']
		else:
			ret += ['nounderscore']
		return ret


class TmuxRenderer(Renderer):
	'''Powerline tmux segment renderer.'''

	character_translations = Renderer.character_translations.copy()
	character_translations[ord('#')] = '##[]'

	def render(self, width=None, segment_info={}, **kwargs):
		if width and segment_info:
			width -= segment_info.get('width_adjust', 0)
			if width < 10:
				width = 10
		return super(TmuxRenderer, self).render(width=width, segment_info=segment_info, **kwargs)

	def hlstyle(self, fg=None, bg=None, attrs=None):
		'''Highlight a segment.'''
		# We don’t need to explicitly reset attributes, so skip those calls
		if not attrs and not bg and not fg:
			return ''
		tmux_attrs = []
		if fg is not None:
			if fg is False or fg[0] is False:
				tmux_attrs += ['fg=default']
			else:
				if self.term_truecolor and fg[1]:
					tmux_attrs += ['fg=#{0:06x}'.format(int(fg[1]))]
				else:
					tmux_attrs += ['fg=colour' + str(fg[0])]
		if bg is not None:
			if bg is False or bg[0] is False:
				tmux_attrs += ['bg=default']
			else:
				if self.term_truecolor and bg[1]:
					tmux_attrs += ['bg=#{0:06x}'.format(int(bg[1]))]
				else:
					tmux_attrs += ['bg=colour' + str(bg[0])]
		if attrs is not None:
			tmux_attrs += attrs_to_tmux_attrs(attrs)
		return '#[' + ','.join(tmux_attrs) + ']'

	def get_segment_info(self, segment_info, mode):
		r = self.segment_info.copy()
		if segment_info:
			r.update(segment_info)
		if 'pane_id' in r:
			varname = 'TMUX_PWD_' + str(r['pane_id'])
			if varname in r['environ']:
				r['getcwd'] = lambda: r['environ'][varname]
		r['mode'] = mode
		return r


renderer = TmuxRenderer
