# -*- coding: utf-8 -*-

import copy


class Theme(object):
	def __init__(self, ext, colorscheme, theme_config, common_config, get_segment):
		self.colorscheme = colorscheme
		self.dividers = theme_config.get('dividers', common_config['dividers'])
		self.segments = []
		self.EMPTY_SEGMENT = {
			'contents': None,
			'highlight': {self.colorscheme.DEFAULT_MODE_KEY: {'fg': (False, False), 'bg': (False, False), 'attr': 0}}
			}
		for side in ['left', 'right']:
			self.segments.extend((get_segment(segment, side) for segment in theme_config['segments'].get(side, [])))

	def get_divider(self, side='left', type='soft'):
		'''Return segment divider.'''
		return self.dividers[side][type]

	def get_segments(self):
		'''Return all segments.

		Function segments are called, and all segments get their before/after
		and ljust/rjust properties applied.
		'''
		for segment in self.segments:
			if segment['type'] == 'function':
				contents = segment['contents_func'](**segment['args'])
				if contents is None:
					continue
				try:
					segment['highlight'] = self.colorscheme.get_group_highlighting(contents['highlight'])
					segment['contents'] = contents['contents']
				except TypeError:
					segment['contents'] = contents
			elif segment['type'] == 'filler' or (segment['type'] == 'string' and segment['contents'] is not None):
				pass
			else:
				continue
			segment['contents'] = unicode(segment['before'] + unicode(segment['contents']) + segment['after'])\
				.ljust(segment['ljust'])\
				.rjust(segment['rjust'])
			# We need to yield a copy of the segment, or else mode-dependent
			# segment contents can't be cached correctly e.g. when caching
			# non-current window contents for vim statuslines
			yield copy.copy(segment)
