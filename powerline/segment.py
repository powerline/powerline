# vim:fileencoding=utf-8:noet

from __future__ import absolute_import
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
		return None, getattr(__import__(segment_module, fromlist=[segment['name']]), segment['name']), segment_module
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


def gen_segment_getter(pl, ext, path, theme_configs, default_module=None):
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

		try:
			contents, contents_func, module = get_segment_info(data, segment)
		except Exception as e:
			pl.exception('Failed to generate segment from {0!r}: {1}', segment, str(e), prefix='segment_generator')
			return None

		if segment_type == 'function':
			highlight_group = [module + '.' + segment['name'], segment['name']]
		else:
			highlight_group = segment.get('highlight_group') or segment.get('name')

		return {
			'name': segment.get('name'),
			'type': segment_type,
			'highlight_group': highlight_group,
			'divider_highlight_group': None,
			'before': get_key(segment, module, 'before', ''),
			'after': get_key(segment, module, 'after', ''),
			'contents_func': contents_func,
			'contents': contents,
			'args': get_key(segment, module, 'args', {}) if segment_type == 'function' else {},
			'priority': segment.get('priority', None),
			'draw_hard_divider': segment.get('draw_hard_divider', True),
			'draw_soft_divider': segment.get('draw_soft_divider', True),
			'draw_inner_divider': segment.get('draw_inner_divider', False),
			'side': side,
			'exclude_modes': segment.get('exclude_modes', []),
			'include_modes': segment.get('include_modes', []),
			'width': segment.get('width'),
			'align': segment.get('align', 'l'),
			'shutdown': getattr(contents_func, 'shutdown', None),
			'startup': getattr(contents_func, 'startup', None),
			'_rendered_raw': '',
			'_rendered_hl': '',
			'_len': 0,
			'_space_left': 0,
			'_space_right': 0,
		}

	return get
