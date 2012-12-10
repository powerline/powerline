# -*- coding: utf-8 -*-

import importlib


class Theme(object):
	def __init__(self, ext, theme_config, common_config):
		self.dividers = theme_config.get('dividers', common_config['dividers'])
		self.segments = []

		for side in ['left', 'right']:
			for segment in theme_config['segments'].get(side, []):
				contents = None
				segment_type = segment.get('type', 'function')

				if segment_type == 'function':
					# Import segment function and assign it to the contents
					function_module = 'powerline.ext.{0}.segments'.format(ext)
					function_name = segment['name']
					contents = getattr(importlib.import_module(function_module), function_name)
				elif segment_type == 'string':
					contents = segment.get('contents')
				elif segment_type == 'filler':
					pass
				else:
					raise TypeError('Unknown segment type: {0}'.format(segment_type))

				self.segments.append({
					'type': segment_type,
					'highlight': segment.get('highlight', segment.get('name')),
					'before': segment.get('before'),
					'after': segment.get('after'),
					'contents': contents,
					'args': segment.get('args', {}),
					'ljust': segment.get('ljust', False),
					'rjust': segment.get('rjust', False),
					'priority': segment.get('priority', -1),
					'draw_divider': segment.get('draw_divider', True),
					'side': side,
					'exclude_modes': segment.get('exclude_modes', []),
					'include_modes': segment.get('include_modes', []),
				})

	def get_divider(self, side='left', type='soft'):
		return self.dividers[side][type]

	def get_segments(self):
		return self.segments
