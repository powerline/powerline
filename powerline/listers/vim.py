# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.theme import requires_segment_info
from powerline.editors import with_input, with_list


def tabpage_updated_segment_info(segment_info, tab_input):
	segment_info = segment_info.copy()
	tabnr = tab_input['tab_number']
	tabpage = segment_info['vim'].tabpages[tabnr - 1]
	window = tabpage.window
	buffer = window.buffer
	segment_info.update(
		tabpage=tabpage,
		tabnr=tabpage.number,
		window=window,
		winnr=window.number,
		window_id=int(window.vars.get('powerline_window_id', -1)),
		buffer=buffer,
		bufnr=buffer.number,
		input=segment_info['input'].copy(),
	)
	segment_info['input'].update(tab_input)
	return segment_info


@with_list(('list_tabs', ('tab_number',)))
@with_input('current_tab_number')
@requires_segment_info
def tablister(pl, segment_info, **kwargs):
	'''List all tab pages in segment_info format

	Specifically generates a list of segment info dictionaries with ``window``, 
	``winnr``, ``window_id``, ``buffer`` and ``bufnr`` keys set to tab-local 
	ones and additional ``tabpage`` and ``tabnr`` keys.

	Adds either ``tab:`` or ``tab_nc:`` prefix to all segment highlight groups.

	Works best with vim-7.4 or later: earlier versions miss tabpage object and 
	thus window objects are not available as well.
	'''
	cur_tabnr = segment_info['input']['current_tab_number']

	def add_multiplier(tab_input, dct):
		dct['priority_multiplier'] = 1 + (0.001 * abs(tab_input['tab_number'] - cur_tabnr))
		return dct

	return (
		(lambda tab_input, prefix: (
			tabpage_updated_segment_info(segment_info, tab_input),
			add_multiplier(tab_input, {
				'highlight_group_prefix': prefix,
				'divider_highlight_group': 'tab:divider'
			})
		))(tab_input, 'tab' if tab_input['tab_number'] == cur_tabnr else 'tab_nc')
		for tab_input in segment_info['inputs']['list_tabs_inputs']
	)


def buffer_updated_segment_info(segment_info, buffer_input):
	segment_info = segment_info.copy()
	segment_info['input'] = segment_info['input'].copy()
	segment_info['input'].update(buffer_input)
	segment_info.update(
		window=None,
		winnr=None,
		window_id=None,
		buffer=segment_info['vim'].buffers[buffer_input['buffer_number']],
		bufnr=buffer_input['buffer_number'],
	)
	return segment_info


@with_list(('list_buffers', ('modified_indicator', 'listed_indicator', 'buffer_number')))
@with_input('current_buffer_number')
@requires_segment_info
def bufferlister(pl, segment_info, show_unlisted=False, **kwargs):
	'''List all buffers in segment_info format

	Specifically generates a list of segment info dictionaries with ``buffer`` 
	and ``bufnr`` keys set to buffer-specific ones, ``window``, ``winnr`` and 
	``window_id`` keys set to None.

	Adds one of ``buf:``, ``buf_nc:``, ``buf_mod:``, or ``buf_nc_mod`` 
	prefix to all segment highlight groups.

	:param bool show_unlisted:
		True if unlisted buffers should be shown as well. Current buffer is 
		always shown.
	'''
	cur_buffer = segment_info['input']['current_buffer_number']
	cur_buffer_idx = -1
	for cur_buffer_idx, i in enumerate(segment_info['input']['list_buffers_inputs']):
		if i['buffer_number'] == cur_buffer:
			break

	def add_multiplier(idx, dct):
		dct['priority_multiplier'] = 1 + (0.001 * abs(idx - cur_buffer_idx))
		return dct

	return (
		(lambda i, idx, current, modified: (
			buffer_updated_segment_info(segment_info, i),
			add_multiplier(idx, {
				'highlight_group_prefix': '{0}{1}'.format(current, modified),
				'divider_highlight_group': 'tab:divider'
			})
		))(
			i,
			idx,
			'buf' if idx == cur_buffer_idx else 'buf_nc',
			'_mod' if i['modified_indicator'] else ''
		)
		for idx, i in enumerate(segment_info['input']['list_buffers_inputs']) if (
			idx == cur_buffer_idx
			or show_unlisted
			or i['listed_indicator']
		)
	)
