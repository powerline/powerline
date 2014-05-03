# vim:fileencoding=utf-8:noet

from __future__ import absolute_import
import sys


class SegmentFactory(object):

	def __init__(self, pl, extension, path, theme_configs, default_module=None):
		self.pl = pl
		self.default_module = default_module or 'powerline.segments.' + extension
		self.path = path
		self.theme_configs = theme_configs

	def get_segment_key(self, segment, module, key=None, default=None):
		try:
			return segment[key]
		except KeyError:
			if 'name' in segment:
				name = segment['name']
				for theme_config in self.theme_configs:
					if 'segment_data' in theme_config:
						keys_to_try = [name]
						if module:
							keys_to_try.append('{0}.{1}'.format(module, name))
						for segment_key in keys_to_try:
							try:
								return theme_config['segment_data'][segment_key][key]
							except KeyError:
								pass
		return default

	def build(self, segment_config, side):
		return Segment(segment_config, side, self)

	__call__ = build


class memoized_property(object):

	def __init__(self, function):
		self.function = function

	def __get__(self, obj, objtype):
		if obj is None:
			return self
		return_value = self.function.__get__(obj, objtype)()
		setattr(obj, self.function.__name__, return_value)
		return return_value


class Segment(object):

	def __init__(self, segment_config, side, segment_factory):
		self._segment_config = segment_config
		self._segment_factory = segment_factory
		self._get_segment_key = segment_factory.get_segment_key
		self._path = segment_factory.path
		self._default_module = segment_factory.default_module

		# Used by renderer.
		self.divider_highlight_group = None
		self.side = side
		self._rendered_raw = ''
		self._rendered_hl = ''
		self._len = 0
		self._space_left = 0
		self._space_right = 0

	@memoized_property
	def before(self):
		return self._get_segment_key(self._segment_config, self.module, 'before', '')

	@memoized_property
	def after(self):
		return self._get_segment_key(self._segment_config, self.module, 'after', '')

	@memoized_property
	def highlight_group(self):
		if self.type == 'function':
			return [self.module + '.' + self.name, self.name]
		else:
			return self._segment_config.get('highlight_group') or self.name

	@memoized_property
	def contents(self):
		if self.type == 'string':
			return self._get_segment_key(self._segment_config, None, 'contents')

	@memoized_property
	def module(self):
		if self.type == 'function':
			return str(self._segment_config.get('module', self._default_module))

	@memoized_property
	def args(self):
		return {
			str(key): value
			for key, value in self._get_segment_key(
				self._segment_config,
				self.module,
				'args', {}
			).items()
		}

	@memoized_property
	def _contents_func(self):
		oldpath = sys.path
		sys.path = self._path + sys.path
		try:
			return getattr(__import__(self.module, fromlist=[self.name]), self.name)
		finally:
			sys.path = oldpath

	@memoized_property
	def contents_func(self):
		if hasattr(self._contents_func, 'powerline_requires_segment_info'):
			return lambda pl, segment_info: self._contents_func(
				pl=pl,
				segment_info=segment_info,
				**self.args
			)
		else:
			return lambda pl, segment_info: self._contents_func(
				pl=pl,
				**self.args
			)

	@memoized_property
	def shutdown(self):
		return getattr(self._contents_func, 'shutdown', None)

	@memoized_property
	def startup(self):
		if self.type == 'function':
			try:
				_startup_func = self._contents_func.startup
			except AttributeError:
				return None
			else:
				return lambda pl, shutdown_event: _startup_func(
					pl=pl,
					shutdown_event=shutdown_event,
					**self.args
				)

	def _segment_config_getter(key, default=None):
		def get_segment_config_value(self):
			return self._segment_config.get(key, default)

		return memoized_property(get_segment_config_value)

	name = _segment_config_getter('name')
	type = _segment_config_getter('type', 'function')
	priority = _segment_config_getter('priority')
	draw_hard_divider = _segment_config_getter('draw_hard_divider', True)
	draw_soft_divider = _segment_config_getter('draw_soft_divider', True)
	draw_inner_divider = _segment_config_getter('draw_inner_divider', False)
	exclude_modes = _segment_config_getter('exclude_modes', [])
	include_modes = _segment_config_getter('include_modes', [])
	width = _segment_config_getter('width')
	align = _segment_config_getter('align', 'l')
	del _segment_config_getter

	def __getitem__(self, key):
		return getattr(self, key)

	def __setitem__(self, key, value):
		return setattr(self, key, value)

	all_attributes = (
		'name',
		'type',
		'highlight_group',
		'divider_highlight_group',
		'before',
		'after',
		'contents_func',
		'contents',
		'args',
		'priority',
		'draw_hard_divider',
		'draw_soft_divider',
		'draw_inner_divider',
		'side',
		'exclude_modes',
		'include_modes',
		'width',
		'align',
		'shutdown',
		'startup',
		'_rendered_raw',
		'_rendered_hl',
		'_len',
		'_space_left',
		'_space_right',
	)

	def as_dict(self):
		return {
			attribute: getattr(self, attribute) for attribute in self.all_attributes
		}

	copy = as_dict


gen_segment_getter = SegmentFactory