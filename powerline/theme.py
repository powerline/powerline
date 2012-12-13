# -*- coding: utf-8 -*-

import importlib


class Theme(object):
	def __init__(self, ext, colorscheme, theme_config, common_config):
		self.colorscheme = colorscheme
		self.dividers = theme_config.get('dividers', common_config['dividers'])
		self.segments = []

		self.EMPTY_SEGMENT = {
			'contents': None,
			'highlight': {self.colorscheme.DEFAULT_MODE_KEY: {'fg': (False, False), 'bg': (False, False), 'attr': 0}}
		}

		for side in ['left', 'right']:
			for segment in theme_config['segments'].get(side, []):
				contents = None
				contents_func = None
				segment_type = segment.get('type', 'function')
				segment_module = segment.get('module', 'core')

				if segment_type == 'function':
					# Import segment function and assign it to the contents
					function_module = 'powerline.ext.{0}.segments.{1}'.format(ext, segment_module)
					function_name = segment['name']
					contents_func = getattr(importlib.import_module(function_module), function_name)
				elif segment_type == 'string':
					contents = segment.get('contents')
				elif segment_type == 'filler':
					pass
				else:
					raise TypeError('Unknown segment type: {0}'.format(segment_type))

				highlighting_group = segment.get('highlight', segment.get('name'))

				self.segments.append({
					'key': None if segment_type != 'function' else '{0}.{1}'.format(segment_module, function_name),
					'type': segment_type,
					'highlight': self.colorscheme.get_group_highlighting(highlighting_group),
					'before': segment.get('before', ''),
					'after': segment.get('after', ''),
					'contents_func': contents_func,
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

			if not segment['key'] in contents_override:
				# Only apply before/after/just to non-overridden segments
				segment['contents'] = unicode(segment['before'] + unicode(segment['contents']) + segment['after'])\
					.ljust(segment['ljust'])\
					.rjust(segment['rjust'])

			return_segments.append(segment)

		return return_segments
