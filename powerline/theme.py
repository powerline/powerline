# -*- coding: utf-8 -*-


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
		'''Return segment divider.
		'''
		return self.dividers[side][type]

	def get_segments(self, mode, contents_override=None):
		'''Return all segments.

		Function segments are called, and all segments get their before/after
		and ljust/rjust properties applied.
		'''
		contents_override = contents_override or {}
		return_segments = []
		for segment in self.segments:
			if mode in segment['exclude_modes'] or (segment['include_modes'] and segment not in segment['include_modes']):
				continue

			if segment['type'] == 'function':
				contents = contents_override.get(segment['key'])
				if contents is None:
					if contents_override:
						continue
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

			if segment['key'] not in contents_override:
				# Only apply before/after/just to non-overridden segments
				segment['contents'] = unicode(segment['before'] + unicode(segment['contents']) + segment['after'])\
					.ljust(segment['ljust'])\
					.rjust(segment['rjust'])

			return_segments.append(segment)

		return return_segments
