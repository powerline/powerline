# vim:fileencoding=utf-8:noet

from copy import copy

from .segment import gen_segment_getter


try:
	from __builtin__ import unicode
except ImportError:
	unicode = str  # NOQA


def u(s):
	if type(s) is unicode:
		return s
	else:
		return unicode(s, 'utf-8')


def requires_segment_info(func):
	func.powerline_requires_segment_info = True
	return func


class Theme(object):
	def __init__(self, ext, theme_config, common_config, top_theme_config=None, segment_info=None, run_once=False):
		self.dividers = theme_config.get('dividers', common_config['dividers'])
		self.spaces = theme_config.get('spaces', common_config['spaces'])
		self.segments = {
			'left': [],
			'right': [],
			}
		self.EMPTY_SEGMENT = {
			'contents': None,
			'highlight': {'fg': False, 'bg': False, 'attr': 0}
			}
		self.segment_info = segment_info
		theme_configs = [theme_config]
		if top_theme_config:
			theme_configs.append(top_theme_config)
		get_segment = gen_segment_getter(ext, common_config['paths'], theme_configs, theme_config.get('default_module'))
		for side in ['left', 'right']:
			self.segments[side].extend((get_segment(segment, side) for segment in theme_config['segments'].get(side, [])))
			if not run_once:
				for segment in self.segments[side]:
					if segment['startup']:
						segment['startup'](**segment['args'])

	def shutdown(self):
		for segments in self.segments.values():
			for segment in segments:
				try:
					segment['shutdown']()
				except TypeError:
					pass

	def get_divider(self, side='left', type='soft'):
		'''Return segment divider.'''
		return self.dividers[side][type]

	def get_spaces(self):
		return self.spaces

	def get_segments(self, side=None):
		'''Return all segments.

		Function segments are called, and all segments get their before/after
		and ljust/rjust properties applied.
		'''
		for side in [side] if side else ['left', 'right']:
			parsed_segments = []
			for segment in self.segments[side]:
				if segment['type'] == 'function':
					if (hasattr(segment['contents_func'], 'powerline_requires_segment_info')
							and segment['contents_func'].powerline_requires_segment_info):
						contents = segment['contents_func'](segment_info=self.segment_info, **segment['args'])
					else:
						contents = segment['contents_func'](**segment['args'])
					if contents is None:
						continue
					if isinstance(contents, list):
						segment_base = copy(segment)
						if contents:
							for key in ('before', 'after'):
								try:
									contents[0][key] = segment_base.pop(key)
									segment_base[key] = ''
								except KeyError:
									pass

						for subsegment in contents:
							segment_copy = copy(segment_base)
							segment_copy.update(subsegment)
							parsed_segments.append(segment_copy)
					else:
						segment['contents'] = contents
						parsed_segments.append(segment)
				elif segment['width'] == 'auto' or (segment['type'] == 'string' and segment['contents'] is not None):
					parsed_segments.append(segment)
				else:
					continue
			for segment in parsed_segments:
				segment['contents'] = segment['before'] + u(segment['contents'] if segment['contents'] is not None else '') + segment['after']
				# Align segment contents
				if segment['width'] and segment['width'] != 'auto':
					if segment['align'] == 'l':
						segment['contents'] = segment['contents'].ljust(segment['width'])
					elif segment['align'] == 'r':
						segment['contents'] = segment['contents'].rjust(segment['width'])
					elif segment['align'] == 'c':
						segment['contents'] = segment['contents'].center(segment['width'])
				# We need to yield a copy of the segment, or else mode-dependent
				# segment contents can't be cached correctly e.g. when caching
				# non-current window contents for vim statuslines
				yield copy(segment)
