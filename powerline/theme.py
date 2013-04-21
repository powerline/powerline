# vim:fileencoding=utf-8:noet

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
	def __init__(self,
				ext,
				theme_config,
				common_config,
				pl,
				top_theme_config=None,
				run_once=False,
				shutdown_event=None):
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
		self.pl = pl
		theme_configs = [theme_config]
		if top_theme_config:
			theme_configs.append(top_theme_config)
		get_segment = gen_segment_getter(pl, ext, common_config['paths'], theme_configs, theme_config.get('default_module'))
		for side in ['left', 'right']:
			for segment in theme_config['segments'].get(side, []):
				segment = get_segment(segment, side)
				if not run_once:
					if segment['startup']:
						try:
							segment['startup'](pl=pl, shutdown_event=shutdown_event, **segment['args'])
						except Exception as e:
							pl.error('Exception during {0} startup: {1}', segment['name'], str(e))
							continue
				self.segments[side].append(segment)

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

	def get_segments(self, side=None, segment_info=None):
		'''Return all segments.

		Function segments are called, and all segments get their before/after
		and ljust/rjust properties applied.
		'''
		for side in [side] if side else ['left', 'right']:
			parsed_segments = []
			for segment in self.segments[side]:
				if segment['type'] == 'function':
					self.pl.prefix = segment['name']
					try:
						if (hasattr(segment['contents_func'], 'powerline_requires_segment_info')
								and segment['contents_func'].powerline_requires_segment_info):
							contents = segment['contents_func'](pl=self.pl, segment_info=segment_info, **segment['args'])
						else:
							contents = segment['contents_func'](pl=self.pl, **segment['args'])
					except Exception as e:
						self.pl.exception('Exception while computing segment: {0}', str(e))
						continue

					if contents is None:
						continue
					if isinstance(contents, list):
						segment_base = segment.copy()
						if contents:
							draw_divider_position = -1 if side == 'left' else 0
							for key, i, newval in (
								('before', 0, ''),
								('after', -1, ''),
								('draw_soft_divider', draw_divider_position, True),
								('draw_hard_divider', draw_divider_position, True),
							):
								try:
									contents[i][key] = segment_base.pop(key)
									segment_base[key] = newval
								except KeyError:
									pass

						draw_inner_divider = None
						if side == 'right':
							append = parsed_segments.append
						else:
							pslen = len(parsed_segments)
							append = lambda item: parsed_segments.insert(pslen, item)

						for subsegment in (contents if side == 'right' else reversed(contents)):
							segment_copy = segment_base.copy()
							segment_copy.update(subsegment)
							if draw_inner_divider is not None:
								segment_copy['draw_soft_divider'] = draw_inner_divider
							draw_inner_divider = segment_copy.pop('draw_inner_divider', None)
							append(segment_copy)
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
				yield segment.copy()
