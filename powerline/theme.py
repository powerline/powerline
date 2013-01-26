# -*- coding: utf-8 -*-

from collections import defaultdict
from copy import copy

from .segment import Segment

try:
	unicode()
except NameError:
	unicode = str


class Theme(object):
	def __init__(self, ext, colorscheme, theme_config, common_config):
		self.colorscheme = colorscheme
		self.dividers = theme_config.get('dividers', common_config['dividers'])
		self.segments = {
			'left': [],
			'right': [],
			}
		self.EMPTY_SEGMENT = {
			'contents': None,
			'highlight': defaultdict(lambda: {'fg': False, 'bg': False, 'attr': 0})
			}
		get_segment = Segment(ext, common_config['paths'], theme_config.get('default_module')).get
		for side in ['left', 'right']:
			self.segments[side].extend((get_segment(segment, side) for segment in theme_config['segments'].get(side, [])))

	def get_divider(self, side='left', type='soft'):
		'''Return segment divider.'''
		return self.dividers[side][type]

	def add_highlight(self, segment):
		segment['highlight'] = self.colorscheme.get_group_highlighting(segment['highlight_group'])
		if segment['divider_highlight_group']:
			segment['divider_highlight'] = self.colorscheme.get_group_highlighting(segment['divider_highlight_group'])
		else:
			segment['divider_highlight'] = None
		return segment

	def get_segments(self, side=None):
		'''Return all segments.

		Function segments are called, and all segments get their before/after
		and ljust/rjust properties applied.
		'''
		for side in [side] if side else ['left', 'right']:
			parsed_segments = []
			for segment in self.segments[side]:
				if segment['type'] == 'function':
					contents = segment['contents_func'](**segment['args'])
					if contents is None:
						continue
					if isinstance(contents, list):
						for subsegment in contents:
							segment_copy = copy(segment)
							segment_copy.update(subsegment)
							print segment_copy['highlight_group']
							parsed_segments.append(segment_copy)
					else:
						segment['contents'] = contents
						parsed_segments.append(segment)
				elif segment['type'] == 'filler' or (segment['type'] == 'string' and segment['contents'] is not None):
					parsed_segments.append(segment)
				else:
					continue
			for segment in parsed_segments:
				segment = self.add_highlight(segment)
				segment['contents'] = (segment['before'] + unicode(segment['contents']) + segment['after'])\
					.ljust(segment['ljust'])\
					.rjust(segment['rjust'])
				# We need to yield a copy of the segment, or else mode-dependent
				# segment contents can't be cached correctly e.g. when caching
				# non-current window contents for vim statuslines
				yield copy(segment)
