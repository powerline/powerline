# vim:fileencoding=utf-8:noet

from __future__ import absolute_import, unicode_literals, division, print_function

from powerline.lib.file_watcher import create_file_watcher
import sys


def list_segment_key_values(segment, theme_configs, key, module=None, default=None):
	try:
		yield segment[key]
	except KeyError:
		pass
	try:
		name = segment['name']
	except KeyError:
		pass
	else:
		found_module_key = False
		for theme_config in theme_configs:
			try:
				segment_data = theme_config['segment_data']
			except KeyError:
				pass
			else:
				if module:
					try:
						yield segment_data[module + '.' + name][key]
						found_module_key = True
					except KeyError:
						pass
				if not found_module_key:
					try:
						yield segment_data[name][key]
					except KeyError:
						pass
	yield default


def get_segment_key(merge, *args, **kwargs):
	if merge:
		ret = None
		for value in list_segment_key_values(*args, **kwargs):
			if ret is None:
				ret = value
			elif isinstance(ret, dict) and isinstance(value, dict):
				old_ret = ret
				ret = value.copy()
				ret.update(old_ret)
			else:
				return ret
		return ret
	else:
		return next(list_segment_key_values(*args, **kwargs))


def get_function(data, segment):
	oldpath = sys.path
	sys.path = data['path'] + sys.path
	segment_module = str(segment.get('module', data['default_module']))
	try:
		return None, getattr(__import__(segment_module, fromlist=[segment['name']]), segment['name']), segment_module
	finally:
		sys.path = oldpath


def get_string(data, segment):
	return data['get_key'](False, segment, None, 'contents'), None, None


def get_filler(data, segment):
	return None, None, None


segment_getters = {
	"function": get_function,
	"string": get_string,
	"filler": get_filler,
	"segment_list": get_function,
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


def process_segment_lister(pl, segment_info, parsed_segments, side, lister, subsegments, patcher_args):
	for subsegment_info, subsegment_update in lister(pl=pl, segment_info=segment_info, **patcher_args):
		for subsegment in subsegments:
			if subsegment_update:
				subsegment = subsegment.copy()
				subsegment.update(subsegment_update)
				if subsegment_update['priority_multiplier'] and subsegment['priority']:
					subsegment['priority'] *= subsegment_update['priority_multiplier']
			process_segment(pl, side, subsegment_info, parsed_segments, subsegment)
	return None


def process_segment(pl, side, segment_info, parsed_segments, segment):
	if segment['type'] in ('function', 'segment_list'):
		pl.prefix = segment['name']
		try:
			if segment['type'] == 'function':
				contents = segment['contents_func'](pl, segment_info)
			else:
				contents = segment['contents_func'](pl, segment_info, parsed_segments, side)
		except Exception as e:
			pl.exception('Exception while computing segment: {0}', str(e))
			return

		if contents is None:
			return
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


def gen_segment_getter(pl, ext, common_config, theme_configs, default_module=None):
	data = {
		'default_module': default_module or 'powerline.segments.' + ext,
		'path': common_config['paths'],
	}

	def get_key(merge, segment, module, key, default=None):
		return get_segment_key(merge, segment, theme_configs, key, module, default)
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

		if not get_key(False, segment, module, 'display', True):
			return None

		if segment_type == 'function':
			highlight_group = [module + '.' + segment['name'], segment['name']]
		else:
			highlight_group = segment.get('highlight_group') or segment.get('name')

		if segment_type in ('function', 'segment_list'):
			args = dict(((str(k), v) for k, v in get_key(True, segment, module, 'args', {}).items()))

		if segment_type == 'segment_list':
			# Handle startup and shutdown of _contents_func?
			subsegments = [
				get(subsegment, side)
				for subsegment in segment['segments']
			]
			return {
				'name': segment.get('name'),
				'type': segment_type,
				'highlight_group': None,
				'divider_highlight_group': None,
				'before': None,
				'after': None,
				'contents_func': lambda pl, segment_info, parsed_segments, side: process_segment_lister(
					pl, segment_info, parsed_segments, side,
					patcher_args=args,
					subsegments=subsegments,
					lister=_contents_func,
				),
				'contents': None,
				'priority': None,
				'draw_soft_divider': None,
				'draw_hard_divider': None,
				'draw_inner_divider': None,
				'side': side,
				'exclude_modes': segment.get('exclude_modes', []),
				'include_modes': segment.get('include_modes', []),
				'width': None,
				'align': None,
				'startup': None,
				'shutdown': None,
				'mode': None,
				'_rendered_raw': '',
				'_rendered_hl': '',
				'_len': None,
				'_contents_len': None,
				'_space_left': 0,
				'_space_right': 0,
			}

		if segment_type == 'function':
			startup_func = get_attr_func(_contents_func, 'startup', args)
			shutdown_func = get_attr_func(_contents_func, 'shutdown', None)

			if hasattr(_contents_func, 'powerline_requires_filesystem_watcher'):
				create_watcher = lambda: create_file_watcher(pl, common_config['watcher'])
				args[str('create_watcher')] = create_watcher

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
			'before': get_key(False, segment, module, 'before', ''),
			'after': get_key(False, segment, module, 'after', ''),
			'contents_func': contents_func,
			'contents': contents,
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
			'mode': None,
			'_rendered_raw': '',
			'_rendered_hl': '',
			'_len': None,
			'_contents_len': None,
			'_space_left': 0,
			'_space_right': 0,
		}

	return get
