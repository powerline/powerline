# vim:fileencoding=utf-8:noet

from powerline.theme import Theme
from unicodedata import east_asian_width, combining
import os

try:
	NBSP = unicode(' ', 'utf-8')
except NameError:
	NBSP = ' '

try:
	from __builtin__ import unichr as chr
except ImportError:
	pass


def construct_returned_value(rendered_highlighted, segments, width, output_raw, output_width):
	if not (output_raw or output_width):
		return rendered_highlighted
	else:
		return (
			(rendered_highlighted,)
			+ ((''.join((segment['_rendered_raw'] for segment in segments)),) if output_raw else ())
			+ ((width,) if output_width else ())
		)


class Renderer(object):
	'''Object that is responsible for generating the highlighted string.

	:param dict theme_config:
		Main theme configuration.
	:param local_themes:
		Local themes. Is to be used by subclasses from ``.get_theme()`` method, 
		base class only records this parameter to a ``.local_themes`` attribute.
	:param dict theme_kwargs:
		Keyword arguments for ``Theme`` class constructor.
	:param Colorscheme colorscheme:
		Colorscheme object that holds colors configuration.
	:param PowerlineLogger pl:
		Object used for logging.
	:param int ambiwidth:
		Width of the characters with east asian width unicode attribute equal to 
		``A`` (Ambigious).
	:param dict options:
		Various options. Are normally not used by base renderer, but all options 
		are recorded as attributes.
	'''

	segment_info = {
		'environ': os.environ,
		'getcwd': getattr(os, 'getcwdu', os.getcwd),
		'home': os.environ.get('HOME'),
	}
	'''Basic segment info. Is merged with local segment information by 
	``.get_segment_info()`` method. Keys:

	``environ``
		Object containing environment variables. Must define at least the 
		following methods: ``.__getitem__(var)`` that raises ``KeyError`` in 
		case requested environment variable is not present, ``.get(var, 
		default=None)`` that works like ``dict.get`` and be able to be passed to 
		``Popen``.

	``getcwd``
		Function that returns current working directory. Will be called without 
		any arguments, should return ``unicode`` or (in python-2) regular 
		string.

	``home``
		String containing path to home directory. Should be ``unicode`` or (in 
		python-2) regular string or ``None``.
	'''

	character_translations = {ord(' '): NBSP}
	'''Character translations for use in escape() function.

	See documentation of ``unicode.translate`` for details.
	'''

	np_character_translations = dict(((i, '^' + chr(i + 0x40)) for i in range(0x20)))
	'''Non-printable character translations

	These are used to transform characters in range 0x00—0x1F into ``^@``, 
	``^A`` and so on. Unilke with ``.escape()`` method (and 
	``character_translations``) result is passed to ``.strwidth()`` method.

	Note: transforms tab into ``^I``.
	'''

	def __init__(self,
	             theme_config,
	             local_themes,
	             theme_kwargs,
	             colorscheme,
	             pl,
	             ambiwidth=1,
	             **options):
		self.__dict__.update(options)
		self.theme_config = theme_config
		theme_kwargs['pl'] = pl
		self.pl = pl
		self.theme = Theme(theme_config=theme_config, **theme_kwargs)
		self.local_themes = local_themes
		self.theme_kwargs = theme_kwargs
		self.colorscheme = colorscheme
		self.width_data = {
			'N': 1,          # Neutral
			'Na': 1,         # Narrow
			'A': ambiwidth,  # Ambigious
			'H': 1,          # Half-width
			'W': 2,          # Wide
			'F': 2,          # Fullwidth
		}

	def strwidth(self, string):
		'''Function that returns string width.

		Is used to calculate the place given string occupies when handling 
		``width`` argument to ``.render()`` method. Must take east asian width 
		into account.

		:param unicode string:
			String whose width will be calculated.

		:return: unsigned integer.
		'''
		return sum((0 if combining(symbol) else self.width_data[east_asian_width(symbol)] for symbol in string))

	def get_theme(self, matcher_info):
		'''Get Theme object.

		Is to be overridden by subclasses to support local themes, this variant 
		only returns ``.theme`` attribute.

		:param matcher_info:
			Parameter ``matcher_info`` that ``.render()`` method received. 
			Unused.
		'''
		return self.theme

	def shutdown(self):
		'''Prepare for interpreter shutdown. The only job it is supposed to do 
		is calling ``.shutdown()`` method for all theme objects. Should be 
		overridden by subclasses in case they support local themes.
		'''
		self.theme.shutdown()

	def _get_highlighting(self, segment, mode):
		segment['highlight'] = self.colorscheme.get_highlighting(segment['highlight_group'], mode, segment.get('gradient_level'))
		if segment['divider_highlight_group']:
			segment['divider_highlight'] = self.colorscheme.get_highlighting(segment['divider_highlight_group'], mode)
		else:
			segment['divider_highlight'] = None
		return segment

	def get_segment_info(self, segment_info, mode):
		'''Get segment information.

		Must return a dictionary containing at least ``home``, ``environ`` and 
		``getcwd`` keys (see documentation for ``segment_info`` attribute). This 
		implementation merges ``segment_info`` dictionary passed to 
		``.render()`` method with ``.segment_info`` attribute, preferring keys 
		from the former. It also replaces ``getcwd`` key with function returning 
		``segment_info['environ']['PWD']`` in case ``PWD`` variable is 
		available.

		:param dict segment_info:
			Segment information that was passed to ``.render()`` method.

		:return: dict with segment information.
		'''
		r = self.segment_info.copy()
		r['mode'] = mode
		if segment_info:
			r.update(segment_info)
		if 'PWD' in r['environ']:
			r['getcwd'] = lambda: r['environ']['PWD']
		return r

	def render_above_lines(self, **kwargs):
		'''Render all segments in the {theme}/segments/above list

		Rendering happens in the reversed order. Parameters are the same as in 
		.render() method.

		:yield: rendered line.
		'''

		theme = self.get_theme(kwargs.get('matcher_info', None))
		for line in range(theme.get_line_number() - 1, 0, -1):
			yield self.render(side=None, line=line, **kwargs)

	def render(self, mode=None, width=None, side=None, line=0, output_raw=False, output_width=False, segment_info=None, matcher_info=None):
		'''Render all segments.

		When a width is provided, low-priority segments are dropped one at
		a time until the line is shorter than the width, or only segments
		with a negative priority are left. If one or more filler segments are
		provided they will fill the remaining space until the desired width is
		reached.

		:param str mode:
			Mode string. Affects contents (colors and the set of segments) of 
			rendered string.
		:param int width:
			Maximum width text can occupy. May be exceeded if there are too much 
			non-removable segments.
		:param str side:
			One of ``left``, ``right``. Determines which side will be rendered. 
			If not present all sides are rendered.
		:param int line:
			Line number for which segments should be obtained. Is counted from 
			zero (botmost line).
		:param bool output_raw:
			Changes the output: if this parameter is ``True`` then in place of 
			one string this method outputs a pair ``(colored_string, 
			colorless_string)``.
		:param bool output_width:
			Changes the output: if this parameter is ``True`` then in place of 
			one string this method outputs a pair ``(colored_string, 
			string_width)``. Returns a three-tuple if ``output_raw`` is also 
			``True``: ``(colored_string, colorless_string, string_width)``.
		:param dict segment_info:
			Segment information. See also ``.get_segment_info()`` method.
		:param matcher_info:
			Matcher information. Is processed in ``.get_theme()`` method.
		'''
		theme = self.get_theme(matcher_info)
		return self.do_render(
			mode=mode,
			width=width,
			side=side,
			line=line,
			output_raw=output_raw,
			output_width=output_width,
			segment_info=segment_info,
			theme=theme,
		)

	def compute_divider_widths(self, theme):
		return {
			'left': {
				'hard': self.strwidth(theme.get_divider('left', 'hard')),
				'soft': self.strwidth(theme.get_divider('left', 'soft')),
			},
			'right': {
				'hard': self.strwidth(theme.get_divider('right', 'hard')),
				'soft': self.strwidth(theme.get_divider('right', 'soft')),
			},
		}

	def do_render(self, mode, width, side, line, output_raw, output_width, segment_info, theme):
		'''Like Renderer.render(), but accept theme in place of matcher_info
		'''
		segments = theme.get_segments(side, line, self.get_segment_info(segment_info, mode))
		# Handle excluded/included segments for the current mode
		segments = [
			self._get_highlighting(segment, segment['mode'] or mode)
			for segment, segment_mode in (
				(segment, segment['mode'])
				for segment in segments
			) if (
				segment_mode not in segment['exclude_modes']
				and (
					not segment['include_modes']
					or segment_mode in segment['include_modes']
				)
			)
		]

		current_width = 0

		if not width:
			# No width specified, so we don't need to crop or pad anything
			if output_width:
				current_width = self._render_length(theme, segments, self.compute_divider_widths(theme))
			return construct_returned_value(''.join([
				segment['_rendered_hl']
				for segment in self._render_segments(theme, segments)
			]) + self.hlstyle(), segments, current_width, output_raw, output_width)

		divider_widths = self.compute_divider_widths(theme)

		# Create an ordered list of segments that can be dropped
		segments_priority = sorted((segment for segment in segments if segment['priority'] is not None), key=lambda segment: segment['priority'], reverse=True)
		for segment in segments_priority:
			current_width = self._render_length(theme, segments, divider_widths)
			if current_width <= width:
				break
			segments.remove(segment)

		# Distribute the remaining space on spacer segments
		segments_spacers = [segment for segment in segments if segment['width'] == 'auto']
		if segments_spacers:
			if not segments_priority:
				# Update segment['_len'] and current_width if not already done 
				# (is not done in shells where there is nothing to remove 
				# because “priority” key is not specified)
				current_width = self._render_length(theme, segments, divider_widths)
			distribute_len, distribute_len_remainder = divmod(width - current_width, len(segments_spacers))
			for segment in segments_spacers:
				if segment['align'] == 'l':
					segment['_space_right'] += distribute_len
				elif segment['align'] == 'r':
					segment['_space_left'] += distribute_len
				elif segment['align'] == 'c':
					space_side, space_side_remainder = divmod(distribute_len, 2)
					segment['_space_left'] += space_side + space_side_remainder
					segment['_space_right'] += space_side
			segments_spacers[0]['_space_right'] += distribute_len_remainder
			# `_len` key is not needed anymore, but current_width should have an 
			# actual value for various bindings.
			current_width = width
		elif output_width:
			current_width = self._render_length(theme, segments, divider_widths)

		rendered_highlighted = ''.join([segment['_rendered_hl'] for segment in self._render_segments(theme, segments)]) + self.hlstyle()

		return construct_returned_value(rendered_highlighted, segments, current_width, output_raw, output_width)

	def _render_length(self, theme, segments, divider_widths):
		'''Update segments lengths and return them
		'''
		segments_len = len(segments)
		ret = 0
		divider_spaces = theme.get_spaces()
		for index, segment in enumerate(segments):
			side = segment['side']
			if segment['_contents_len'] is None:
				segment_len = segment['_contents_len'] = self.strwidth(segment['contents'])
			else:
				segment_len = segment['_contents_len']

			prev_segment = segments[index - 1] if index > 0 else theme.EMPTY_SEGMENT
			next_segment = segments[index + 1] if index < segments_len - 1 else theme.EMPTY_SEGMENT
			compare_segment = next_segment if side == 'left' else prev_segment
			divider_type = 'soft' if compare_segment['highlight']['bg'] == segment['highlight']['bg'] else 'hard'

			outer_padding = int(bool(
				(index == 0 and side == 'left') or
				(index == segments_len - 1 and side == 'right')
			))

			draw_divider = segment['draw_' + divider_type + '_divider']
			segment_len += segment['_space_left'] + segment['_space_right'] + outer_padding
			if draw_divider:
				segment_len += divider_widths[side][divider_type] + divider_spaces

			segment['_len'] = segment_len
			ret += segment_len
		return ret

	def _render_segments(self, theme, segments, render_highlighted=True):
		'''Internal segment rendering method.

		This method loops through the segment array and compares the
		foreground/background colors and divider properties and returns the
		rendered statusline as a string.

		The method always renders the raw segment contents (i.e. without
		highlighting strings added), and only renders the highlighted
		statusline if render_highlighted is True.
		'''
		segments_len = len(segments)
		divider_spaces = theme.get_spaces()

		for index, segment in enumerate(segments):
			side = segment['side']
			prev_segment = segments[index - 1] if index > 0 else theme.EMPTY_SEGMENT
			next_segment = segments[index + 1] if index < segments_len - 1 else theme.EMPTY_SEGMENT
			compare_segment = next_segment if side == 'left' else prev_segment
			outer_padding = int(bool(
				(index == 0 and side == 'left') or
				(index == segments_len - 1 and side == 'right')
			)) * ' '
			divider_type = 'soft' if compare_segment['highlight']['bg'] == segment['highlight']['bg'] else 'hard'

			divider_highlighted = ''
			contents_raw = segment['contents']
			contents_highlighted = ''
			draw_divider = segment['draw_' + divider_type + '_divider']

			# Pad segments first
			if draw_divider:
				divider_raw = theme.get_divider(side, divider_type).replace(' ', NBSP)
				if side == 'left':
					contents_raw = (
						outer_padding + (segment['_space_left'] * ' ')
						+ contents_raw
						+ ((divider_spaces + segment['_space_right']) * ' ')
					)
				else:
					contents_raw = (
						((divider_spaces + segment['_space_left']) * ' ')
						+ contents_raw
						+ (segment['_space_right'] * ' ') + outer_padding
					)
			else:
				if side == 'left':
					contents_raw = (
						outer_padding + (segment['_space_left'] * ' ')
						+ contents_raw
						+ (segment['_space_right'] * ' ')
					)
				else:
					contents_raw = (
						(segment['_space_left'] * ' ')
						+ contents_raw
						+ (segment['_space_right'] * ' ') + outer_padding
					)

			# Replace spaces with no-break spaces
			contents_raw = contents_raw.translate(self.np_character_translations)

			# Apply highlighting to padded dividers and contents
			if render_highlighted:
				if draw_divider:
					if divider_type == 'soft':
						divider_highlight_group_key = 'highlight' if segment['divider_highlight_group'] is None else 'divider_highlight'
						divider_fg = segment[divider_highlight_group_key]['fg']
						divider_bg = segment[divider_highlight_group_key]['bg']
					else:
						divider_fg = segment['highlight']['bg']
						divider_bg = compare_segment['highlight']['bg']
					divider_highlighted = self.hl(divider_raw, divider_fg, divider_bg, False)
				contents_highlighted = self.hl(self.escape(contents_raw), **segment['highlight'])

			# Append padded raw and highlighted segments to the rendered segment variables
			if draw_divider:
				if side == 'left':
					segment['_rendered_raw'] = contents_raw + divider_raw
					segment['_rendered_hl'] = contents_highlighted + divider_highlighted
				else:
					segment['_rendered_raw'] = divider_raw + contents_raw
					segment['_rendered_hl'] = divider_highlighted + contents_highlighted
			else:
				if side == 'left':
					segment['_rendered_raw'] = contents_raw
					segment['_rendered_hl'] = contents_highlighted
				else:
					segment['_rendered_raw'] = contents_raw
					segment['_rendered_hl'] = contents_highlighted
			yield segment

	@classmethod
	def escape(cls, string):
		'''Method that escapes segment contents.
		'''
		return string.translate(cls.character_translations)

	def hlstyle(fg=None, bg=None, attr=None):
		'''Output highlight style string.

		Assuming highlighted string looks like ``{style}{contents}`` this method 
		should output ``{style}``. If it is called without arguments this method 
		is supposed to reset style to its default.
		'''
		raise NotImplementedError

	def hl(self, contents, fg=None, bg=None, attr=None):
		'''Output highlighted chunk.

		This implementation just outputs ``.hlstyle()`` joined with 
		``contents``.
		'''
		return self.hlstyle(fg, bg, attr) + (contents or '')
