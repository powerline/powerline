# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.theme import requires_segment_info
from powerline.bindings.vim import (current_tabpage, list_tabpages, vim_getbufoption)

try:
	import vim
except ImportError:
	vim = {}


def tabpage_updated_segment_info(segment_info, tabpage):
	segment_info = segment_info.copy()
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
	)
	return segment_info


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
	cur_tabpage = current_tabpage()
	cur_tabnr = cur_tabpage.number

	def add_multiplier(tabpage, dct):
		dct['priority_multiplier'] = 1 + (0.001 * abs(tabpage.number - cur_tabnr))
		return dct

	return (
		(lambda tabpage, prefix: (
			tabpage_updated_segment_info(segment_info, tabpage),
			add_multiplier(tabpage, {'highlight_group_prefix': prefix})
		))(tabpage, 'tab' if tabpage == cur_tabpage else 'tab_nc')
		for tabpage in list_tabpages()
	)


def buffer_updated_segment_info(segment_info, buffer):
	segment_info = segment_info.copy()
	segment_info.update(
		window=None,
		winnr=None,
		window_id=None,
		buffer=buffer,
		bufnr=buffer.number,
	)
	return segment_info


@requires_segment_info
def bufferlister(pl, segment_info, show_unlisted=False, **kwargs):
	'''List all buffers in segment_info format

	Specifically generates a list of segment info dictionaries with ``buffer`` 
	and ``bufnr`` keys set to buffer-specific ones, ``window``, ``winnr`` and 
	``window_id`` keys set to None.

	Adds either ``buf:`` or ``buf_nc:`` prefix to all segment highlight groups.

	:param bool show_unlisted:
		True if unlisted buffers should be shown as well. Current buffer is 
		always shown.
	'''
	cur_buffer = vim.current.buffer
	cur_bufnr = cur_buffer.number

	def add_multiplier(buffer, dct):
		dct['priority_multiplier'] = 1 + (0.001 * abs(buffer.number - cur_bufnr))
		return dct

	return (
		(
			buf_segment_info,
			add_multiplier(buf_segment_info['buffer'], {'highlight_group_prefix': prefix})
		)
		for buf_segment_info, prefix in (
			(
				buffer_updated_segment_info(
					segment_info,
					buffer
				),
				('buf' if buffer is cur_buffer else 'buf_nc')
			)
			for buffer in vim.buffers
		) if (
			buf_segment_info['buffer'] is cur_buffer
			or show_unlisted
			or int(vim_getbufoption(buf_segment_info, 'buflisted'))
		)
	)
