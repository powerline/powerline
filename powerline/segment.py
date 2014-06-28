# vim:fileencoding=utf-8:noet

from __future__ import absolute_import, unicode_literals, division, print_function

from powerline.lib.file_watcher import create_file_watcher
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


def get_attr_func(contents_func, key, args):
	try:
		func = getattr(contents_func, key)
	except AttributeError:
		return None
	else:
		if args is None:
			return lambda: func()
		else:
			return lambda pl, shutdown_event: func(pl=pl, shutdown_event=shutdown_event, **args)


def gen_segment_getter(pl, ext, common_config, theme_configs, default_module=None):
	data = {
		'default_module': default_module or 'powerline.segments.' + ext,
		'path': common_config['paths'],
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
			contents, _contents_func, module = get_segment_info(data, segment)
		except Exception as e:
			pl.exception('Failed to generate segment from {0!r}: {1}', segment, str(e), prefix='segment_generator')
			return None

		if segment_type == 'function':
			highlight_group = [module + '.' + segment['name'], segment['name']]
		else:
			highlight_group = segment.get('highlight_group') or segment.get('name')

		if segment_type == 'function':
			args = dict(((str(k), v) for k, v in get_key(segment, module, 'args', {}).items()))
			startup_func = get_attr_func(_contents_func, 'startup', args)
			shutdown_func = get_attr_func(_contents_func, 'shutdown', None)

			if hasattr(_contents_func, 'powerline_requires_filesystem_watcher'):
				create_watcher = lambda: create_file_watcher(pl, common_config['watcher'])
				args['create_watcher'] = create_watcher

			if hasattr(_contents_func, 'powerline_requires_segment_info'):
				contents_func = lambda pl, segment_info: _contents_func(pl=pl, segment_info=segment_info, **args)
			else:
				contents_func = lambda pl, segment_info: _contents_func(pl=pl, **args)
		else:
			startup_func = None
			shutdown_func = None
			contents_func = None

		return {
			'name': segment.get('name'),
			'type': segment_type,
			'highlight_group': highlight_group,
			'divider_highlight_group': None,
			'before': get_key(segment, module, 'before', ''),
			'after': get_key(segment, module, 'after', ''),
			'contents_func': contents_func,
			'contents': contents,
			'args': args if segment_type == 'function' else {},
			'priority': segment.get('priority', None),
			'draw_hard_divider': segment.get('draw_hard_divider', True),
			'draw_soft_divider': segment.get('draw_soft_divider', True),
			'draw_inner_divider': segment.get('draw_inner_divider', False),
			'side': side,
			'exclude_modes': segment.get('exclude_modes', []),
			'include_modes': segment.get('include_modes', []),
			'width': segment.get('width'),
			'align': segment.get('align', 'l'),
			'startup': startup_func,
			'shutdown': shutdown_func,
			'_rendered_raw': '',
			'_rendered_hl': '',
			'_len': 0,
			'_space_left': 0,
			'_space_right': 0,
		}

	return get
