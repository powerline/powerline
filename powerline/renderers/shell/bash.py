# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.renderers.shell import ShellRenderer


class BashPromptRenderer(ShellRenderer):
	'''Powerline bash prompt segment renderer.'''
	escape_hl_start = '\\['
	escape_hl_end = '\\]'

	character_translations = ShellRenderer.character_translations.copy()
	character_translations[ord('$')] = '\\$'
	character_translations[ord('`')] = '\\`'
	character_translations[ord('\\')] = '\\\\'

	def do_render(self, side, line, width, output_width, output_raw, hl_args, **kwargs):

		# we are rendering the normal left prompt
		if side == 'left' and line == 0 and width is not None:

			# we need left prompt's width to render the raw spacer
			output_width = output_width or output_raw

			left = super(BashPromptRenderer, self).do_render(
				side=side,
				line=line,
				output_width=output_width,
				width=width,
				output_raw=output_raw,
				hl_args=hl_args,
				**kwargs
			)
			left_rendered = left[0] if output_width else left

			# we don't escape color sequences in the right prompt so we can do escaping as a whole
			if hl_args:
				hl_args = hl_args.copy()
				hl_args.update({'escape': False})
			else:
				hl_args = {'escape': False}

			right = super(BashPromptRenderer, self).do_render(
				side='right',
				line=line,
				output_width=True,
				width=width,
				output_raw=output_raw,
				hl_args=hl_args,
				**kwargs
			)

			ret = []
			if right[-1] > 0:
				# if the right prompt is not empty we embed it in the left prompt
				# it must be escaped as a whole so readline doesn't see it
				ret.append(''.join((
					left_rendered,
					self.escape_hl_start,
					'\033[s',                           # save the cursor position
					'\033[{0}C'.format(width),          # move to the right edge of the terminal
					'\033[{0}D'.format(right[-1] - 1),  # move back to the right prompt position
					right[0],
					'\033[u',                           # restore the cursor position
					self.escape_hl_end
				)))
				if output_raw:
					ret.append(''.join((
						left[1],
						' ' * (width - left[-1] - right[-1]),
						right[1]
					)))
			else:
				ret.append(left_rendered)
				if output_raw:
					ret.append(left[1])
			if output_width:
				ret.append(left[-1])
			if len(ret) == 1:
				return ret[0]
			else:
				return ret

		else:
			return super(BashPromptRenderer, self).do_render(
				side=side,
				line=line,
				width=width,
				output_width=output_width,
				output_raw=output_raw,
				hl_args=hl_args,
				**kwargs
			)


renderer = BashPromptRenderer
