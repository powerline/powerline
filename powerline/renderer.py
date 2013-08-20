# vim:fileencoding=utf-8:noet

from powerline.theme import Theme
from unicodedata import east_asian_width, combining
import os


try:
	NBSP = unicode(' ', 'utf-8')
except NameError:
	NBSP = ' '


def construct_returned_value(rendered_highlighted, segments, output_raw):
	if output_raw:
		return rendered_highlighted, ''.join((segment['_rendered_raw'] for segment in segments))
	else:
		return rendered_highlighted


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

	def get_segment_info(self, segment_info):
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
		if segment_info:
			r.update(segment_info)
		if 'PWD' in r['environ']:
			r['getcwd'] = lambda: r['environ']['PWD']
		return r

	def render(self, mode=None, width=None, side=None, output_raw=False, segment_info=None, matcher_info=None):
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
		:param bool output_raw:
			Changes the output: if this parameter is ``True`` then in place of 
			one string this method outputs a pair ``(colored_string, 
			colorless_string)``.
		:param dict segment_info:
			Segment information. See also ``.get_segment_info()`` method.
		:param matcher_info:
			Matcher information. Is processed in ``.get_theme()`` method.
		'''
		theme = self.get_theme(matcher_info)
		segments = theme.get_segments(side, self.get_segment_info(segment_info))

		# Handle excluded/included segments for the current mode
		segments = [self._get_highlighting(segment, mode) for segment in segments
			if mode not in segment['exclude_modes'] and (not segment['include_modes'] or mode in segment['include_modes'])]

		segments = [segment for segment in self._render_segments(theme, segments)]

		if not width:
			# No width specified, so we don't need to crop or pad anything
			return construct_returned_value(''.join([segment['_rendered_hl'] for segment in segments]) + self.hlstyle(), segments, output_raw)

		# Create an ordered list of segments that can be dropped
		segments_priority = sorted((segment for segment in segments if segment['priority'] is not None), key=lambda segment: segment['priority'], reverse=True)
		while sum([segment['_len'] for segment in segments]) > width and len(segments_priority):
			segments.remove(segments_priority[0])
			segments_priority.pop(0)

		# Distribute the remaining space on spacer segments
		segments_spacers = [segment for segment in segments if segment['width'] == 'auto']
		if segments_spacers:
			distribute_len, distribute_len_remainder = divmod(width - sum([segment['_len'] for segment in segments]), len(segments_spacers))
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

		rendered_highlighted = ''.join([segment['_rendered_hl'] for segment in self._render_segments(theme, segments)]) + self.hlstyle()

		return construct_returned_value(rendered_highlighted, segments, output_raw)

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

		for index, segment in enumerate(segments):
			segment['_rendered_raw'] = ''
			segment['_rendered_hl'] = ''

			prev_segment = segments[index - 1] if index > 0 else theme.EMPTY_SEGMENT
			next_segment = segments[index + 1] if index < segments_len - 1 else theme.EMPTY_SEGMENT
			compare_segment = next_segment if segment['side'] == 'left' else prev_segment
			outer_padding = ' ' if (index == 0 and segment['side'] == 'left') or (index == segments_len - 1 and segment['side'] == 'right') else ''
			divider_type = 'soft' if compare_segment['highlight']['bg'] == segment['highlight']['bg'] else 'hard'

			divider_raw = theme.get_divider(segment['side'], divider_type)
			divider_spaces = theme.get_spaces()
			divider_highlighted = ''
			contents_raw = segment['contents']
			contents_highlighted = ''
			draw_divider = segment['draw_' + divider_type + '_divider']

			# Pad segments first
			if draw_divider:
				if segment['side'] == 'left':
					contents_raw = outer_padding + (segment['_space_left'] * ' ') + contents_raw + ((divider_spaces + segment['_space_right']) * ' ')
				else:
					contents_raw = ((divider_spaces + segment['_space_left']) * ' ') + contents_raw + (segment['_space_right'] * ' ') + outer_padding
			else:
				if segment['side'] == 'left':
					contents_raw = outer_padding + (segment['_space_left'] * ' ') + contents_raw + (segment['_space_right'] * ' ')
				else:
					contents_raw = (segment['_space_left'] * ' ') + contents_raw + (segment['_space_right'] * ' ') + outer_padding

			# Replace spaces with no-break spaces
			contents_raw = contents_raw.replace(' ', NBSP)
			divider_raw = divider_raw.replace(' ', NBSP)

			# Apply highlighting to padded dividers and contents
			if render_highlighted:
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
				if segment['side'] == 'left':
					segment['_rendered_raw'] += contents_raw + divider_raw
					segment['_rendered_hl'] += contents_highlighted + divider_highlighted
				else:
					segment['_rendered_raw'] += divider_raw + contents_raw
					segment['_rendered_hl'] += divider_highlighted + contents_highlighted
			else:
				if segment['side'] == 'left':
					segment['_rendered_raw'] += contents_raw
					segment['_rendered_hl'] += contents_highlighted
				else:
					segment['_rendered_raw'] += contents_raw
					segment['_rendered_hl'] += contents_highlighted
			segment['_len'] = self.strwidth(segment['_rendered_raw'])
			yield segment

	@staticmethod
	def escape(string):
		'''Method that escapes segment contents.
		'''
		return string

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
