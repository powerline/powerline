# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.lib.watcher import create_file_watcher


def list_segment_key_values(segment, theme_configs, segment_data, key, function_name=None, name=None, module=None, default=None):
	try:
		yield segment[key]
	except KeyError:
		pass
	found_module_key = False
	for theme_config in theme_configs:
		try:
			segment_data = theme_config['segment_data']
		except KeyError:
			pass
		else:
			if function_name and not name:
				if module:
					try:
						yield segment_data[module + '.' + function_name][key]
						found_module_key = True
					except KeyError:
						pass
				if not found_module_key:
					try:
						yield segment_data[function_name][key]
					except KeyError:
						pass
			if name:
				try:
					yield segment_data[name][key]
				except KeyError:
					pass
	if segment_data is not None:
		try:
			yield segment_data[key]
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
	function_name = segment['function']
	if '.' in function_name:
		module, function_name = function_name.rpartition('.')[::2]
	else:
		module = data['default_module']
	function = data['get_module_attr'](module, function_name, prefix='segment_generator')
	if not function:
		raise ImportError('Failed to obtain segment function')
	return None, function, module, function_name, segment.get('name')


def get_string(data, segment):
	name = segment.get('name')
	return data['get_key'](False, segment, None, None, name, 'contents'), None, None, None, name


segment_getters = {
	'function': get_function,
	'string': get_string,
	'segment_list': get_function,
}


def get_attr_func(contents_func, key, args, is_space_func=False):
	try:
		func = getattr(contents_func, key)
	except AttributeError:
		return None
	else:
		if is_space_func:
			def expand_func(pl, amount, segment):
				try:
					return func(pl=pl, amount=amount, segment=segment, **args)
				except Exception as e:
					pl.exception('Exception while computing {0} function: {1}', key, str(e))
					return segment['contents'] + (' ' * amount)
			return expand_func
		else:
			return lambda pl, shutdown_event: func(pl=pl, shutdown_event=shutdown_event, **args)


def process_segment_lister(pl, segment_info, parsed_segments, side, mode, colorscheme,
	                       lister, subsegments, patcher_args):
	subsegments = [
		subsegment
		for subsegment in subsegments
		if subsegment['display_condition'](pl, segment_info, mode)
	]
	for subsegment_info, subsegment_update in lister(pl=pl, segment_info=segment_info, **patcher_args):
		draw_inner_divider = subsegment_update.pop('draw_inner_divider', False)
		old_pslen = len(parsed_segments)
		for subsegment in subsegments:
			if subsegment_update:
				subsegment = subsegment.copy()
				subsegment.update(subsegment_update)
				if 'priority_multiplier' in subsegment_update and subsegment['priority']:
					subsegment['priority'] *= subsegment_update['priority_multiplier']

			process_segment(
				pl,
				side,
				subsegment_info,
				parsed_segments,
				subsegment,
				mode,
				colorscheme,
			)
		new_pslen = len(parsed_segments)
		while parsed_segments[new_pslen - 1]['literal_contents'][1]:
			new_pslen -= 1
		if new_pslen > old_pslen + 1 and draw_inner_divider is not None:
			for i in range(old_pslen, new_pslen - 1) if side == 'left' else range(old_pslen + 1, new_pslen):
				parsed_segments[i]['draw_soft_divider'] = draw_inner_divider
	return None


def set_segment_highlighting(pl, colorscheme, segment, mode):
	if segment['literal_contents'][1]:
		return True
	try:
		highlight_group_prefix = segment['highlight_group_prefix']
	except KeyError:
		hl_groups = lambda hlgs: hlgs
	else:
		hl_groups = lambda hlgs: [highlight_group_prefix + ':' + hlg for hlg in hlgs] + hlgs
	try:
		segment['highlight'] = colorscheme.get_highlighting(
			hl_groups(segment['highlight_groups']),
			mode,
			segment.get('gradient_level')
		)
		if segment['divider_highlight_group']:
			segment['divider_highlight'] = colorscheme.get_highlighting(
				hl_groups([segment['divider_highlight_group']]),
				mode
			)
		else:
			segment['divider_highlight'] = None
	except Exception as e:
		pl.exception('Failed to set highlight group: {0}', str(e))
		return False
	else:
		return True


def process_segment(pl, side, segment_info, parsed_segments, segment, mode, colorscheme):
	segment = segment.copy()
	pl.prefix = segment['name']
	if segment['type'] in ('function', 'segment_list'):
		try:
			if segment['type'] == 'function':
				contents = segment['contents_func'](pl, segment_info)
			else:
				contents = segment['contents_func'](pl, segment_info, parsed_segments, side, mode, colorscheme)
		except Exception as e:
			pl.exception('Exception while computing segment: {0}', str(e))
			return

		if contents is None:
			return

		if isinstance(contents, list):
			# Needs copying here, but it was performed at the very start of the 
			# function
			segment_base = segment
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
				if set_segment_highlighting(pl, colorscheme, segment_copy, mode):
					append(segment_copy)
		else:
			segment['contents'] = contents
			if set_segment_highlighting(pl, colorscheme, segment, mode):
				parsed_segments.append(segment)
	elif segment['width'] == 'auto' or (segment['type'] == 'string' and segment['contents'] is not None):
		if set_segment_highlighting(pl, colorscheme, segment, mode):
			parsed_segments.append(segment)


always_true = lambda pl, segment_info, mode: True

get_fallback_segment = {
	'name': 'fallback',
	'type': 'string',
	'highlight_groups': ['background'],
	'divider_highlight_group': None,
	'before': None,
	'after': None,
	'contents': '',
	'literal_contents': (0, ''),
	'priority': None,
	'draw_soft_divider': True,
	'draw_hard_divider': True,
	'draw_inner_divider': True,
	'display_condition': always_true,
	'width': None,
	'align': None,
	'expand': None,
	'truncate': None,
	'startup': None,
	'shutdown': None,
	'_rendered_raw': '',
	'_rendered_hl': '',
	'_len': None,
	'_contents_len': None,
}.copy


def gen_segment_getter(pl, ext, common_config, theme_configs, default_module, get_module_attr, top_theme):
	data = {
		'default_module': default_module or 'powerline.segments.' + ext,
		'get_module_attr': get_module_attr,
		'segment_data': None,
	}

	def get_key(merge, segment, module, function_name, name, key, default=None):
		return get_segment_key(merge, segment, theme_configs, data['segment_data'], key, function_name, name, module, default)
	data['get_key'] = get_key

	def get_selector(function_name):
		if '.' in function_name:
			module, function_name = function_name.rpartition('.')[::2]
		else:
			module = 'powerline.selectors.' + ext
		function = get_module_attr(module, function_name, prefix='segment_generator/selector_function')
		if not function:
			pl.error('Failed to get segment selector, ignoring it')
		return function

	def get_segment_selector(segment, selector_type):
		try:
			function_name = segment[selector_type + '_function']
		except KeyError:
			function = None
		else:
			function = get_selector(function_name)
		try:
			modes = segment[selector_type + '_modes']
		except KeyError:
			modes = None

		if modes:
			if function:
				return lambda pl, segment_info, mode: (
					mode in modes
					or function(pl=pl, segment_info=segment_info, mode=mode)
				)
			else:
				return lambda pl, segment_info, mode: mode in modes
		else:
			if function:
				return lambda pl, segment_info, mode: (
					function(pl=pl, segment_info=segment_info, mode=mode)
				)
			else:
				return None

	def gen_display_condition(segment):
		include_function = get_segment_selector(segment, 'include')
		exclude_function = get_segment_selector(segment, 'exclude')
		if include_function:
			if exclude_function:
				return lambda *args: (
					include_function(*args)
					and not exclude_function(*args))
			else:
				return include_function
		else:
			if exclude_function:
				return lambda *args: not exclude_function(*args)
			else:
				return always_true

	def get(segment, side):
		segment_type = segment.get('type', 'function')
		try:
			get_segment_info = segment_getters[segment_type]
		except KeyError:
			pl.error('Unknown segment type: {0}', segment_type)
			return None

		try:
			contents, _contents_func, module, function_name, name = get_segment_info(data, segment)
		except Exception as e:
			pl.exception('Failed to generate segment from {0!r}: {1}', segment, str(e), prefix='segment_generator')
			return None

		if not get_key(False, segment, module, function_name, name, 'display', True):
			return None

		segment_datas = getattr(_contents_func, 'powerline_segment_datas', None)
		if segment_datas:
			try:
				data['segment_data'] = segment_datas[top_theme]
			except KeyError:
				pass

		if segment_type == 'function':
			highlight_groups = [function_name]
		else:
			highlight_groups = segment.get('highlight_groups') or [name]

		if segment_type in ('function', 'segment_list'):
			args = dict((
				(str(k), v)
				for k, v in
				get_key(True, segment, module, function_name, name, 'args', {}).items()
			))

		display_condition = gen_display_condition(segment)

		if segment_type == 'segment_list':
			# Handle startup and shutdown of _contents_func?
			subsegments = [
				subsegment
				for subsegment in (
					get(subsegment, side)
					for subsegment in segment['segments']
				) if subsegment
			]
			return {
				'name': name or function_name,
				'type': segment_type,
				'highlight_groups': None,
				'divider_highlight_group': None,
				'before': None,
				'after': None,
				'contents_func': lambda pl, segment_info, parsed_segments, side, mode, colorscheme: (
					process_segment_lister(
						pl, segment_info, parsed_segments, side, mode, colorscheme,
						patcher_args=args,
						subsegments=subsegments,
						lister=_contents_func,
					)
				),
				'contents': None,
				'literal_contents': None,
				'priority': None,
				'draw_soft_divider': None,
				'draw_hard_divider': None,
				'draw_inner_divider': None,
				'side': side,
				'display_condition': display_condition,
				'width': None,
				'align': None,
				'expand': None,
				'truncate': None,
				'startup': None,
				'shutdown': None,
				'_rendered_raw': '',
				'_rendered_hl': '',
				'_len': None,
				'_contents_len': None,
			}

		if segment_type == 'function':
			startup_func = get_attr_func(_contents_func, 'startup', args)
			shutdown_func = getattr(_contents_func, 'shutdown', None)
			expand_func = get_attr_func(_contents_func, 'expand', args, True)
			truncate_func = get_attr_func(_contents_func, 'truncate', args, True)

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
			expand_func = None
			truncate_func = None

		return {
			'name': name or function_name,
			'type': segment_type,
			'highlight_groups': highlight_groups,
			'divider_highlight_group': None,
			'before': get_key(False, segment, module, function_name, name, 'before', ''),
			'after': get_key(False, segment, module, function_name, name, 'after', ''),
			'contents_func': contents_func,
			'contents': contents,
			'literal_contents': (0, ''),
			'priority': segment.get('priority', None),
			'draw_hard_divider': segment.get('draw_hard_divider', True),
			'draw_soft_divider': segment.get('draw_soft_divider', True),
			'draw_inner_divider': segment.get('draw_inner_divider', False),
			'side': side,
			'display_condition': display_condition,
			'width': segment.get('width'),
			'align': segment.get('align', 'l'),
			'expand': expand_func,
			'truncate': truncate_func,
			'startup': startup_func,
			'shutdown': shutdown_func,
			'_rendered_raw': '',
			'_rendered_hl': '',
			'_len': None,
			'_contents_len': None,
		}

	return get
