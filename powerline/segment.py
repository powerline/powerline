# -*- coding: utf-8 -*-

from importlib import import_module
import sys


def get_segment_key(segment, theme_configs, key, module=None, default=None):
	try:
		return segment[key]
	except KeyError:
		if 'name' in segment:
			name = segment['name']
			for theme_config in theme_configs:
				if 'segment_data' in theme_config:
					for segment_key in ((module + '.' + name, name) if module else (name,)):
						try:
							return theme_config['segment_data'][segment_key][key]
						except KeyError:
							pass
	return default


def get_function(data, segment):
	oldpath = sys.path
	sys.path = data['path'] + sys.path
	segment_module = str(segment.get('module', data['default_module']))
	try:
		return None, getattr(import_module(segment_module), segment['name']), segment_module
	finally:
		sys.path = oldpath


def get_string(data, segment):
	return data['get_key'](segment, None, 'contents'), None, None


def get_filler(data, segment):
	return None, None, None


segment_getters = {
		"function": get_function,
		"string": get_string,
		"filler": get_filler,
		}


def gen_segment_getter(ext, path, theme_configs, default_module=None):
	data = {
			'default_module': default_module or 'powerline.segments.' + ext,
			'path': path,
			}

	def get_key(segment, module, key, default=None):
		return get_segment_key(segment, theme_configs, key, module, default)
	data['get_key'] = get_key

	def get(segment, side):
		segment_type = segment.get('type', 'function')
		try:
			get_segment_info = segment_getters[segment_type]
		except KeyError:
			raise TypeError('Unknown segment type: {0}'.format(segment_type))
		contents, contents_func, module = get_segment_info(data, segment)
		highlight_group = segment.get('highlight_group', segment.get('name'))
		divider_highlight_group = segment.get('divider_highlight_group')
		return {
			'type': segment_type,
			'highlight_group': highlight_group,
			'divider_highlight_group': divider_highlight_group,
			'before': get_key(segment, module, 'before', ''),
			'after': get_key(segment, module, 'after', ''),
			'contents_func': contents_func,
			'contents': contents,
			'args': get_key(segment, module, 'args', {}) if segment_type == 'function' else {},
			'priority': segment.get('priority', -1),
			'draw_divider': segment.get('draw_divider', True),
			'side': side,
			'exclude_modes': segment.get('exclude_modes', []),
			'include_modes': segment.get('include_modes', []),
			'width': segment.get('width'),
			'align': segment.get('align', 'l'),
			'_rendered_raw': u'',
			'_rendered_hl': u'',
			'_len': 0,
			'_space_left': 0,
			'_space_right': 0,
			}

	return get
