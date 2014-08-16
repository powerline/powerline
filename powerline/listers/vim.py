# vim:fileencoding=utf-8:noet

from __future__ import unicode_literals, absolute_import, division

try:
	import vim
except ImportError:
	vim = {}  # NOQA

from powerline.theme import requires_segment_info
from powerline.bindings.vim import (current_tabpage, list_tabpages)


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

	Sets segment ``mode`` to either ``tab`` (for current tab page) or ``nc`` 
	(for all other tab pages).

	Works best with vim-7.4 or later: earlier versions miss tabpage object and 
	thus window objects are not available as well.
	'''
	cur_tabpage = current_tabpage()
	cur_tabnr = cur_tabpage.number

	def add_multiplier(tabpage, dct):
		dct['priority_multiplier'] = 1 + (0.001 * abs(tabpage.number - cur_tabnr))
		return dct

	return [
		(
			tabpage_updated_segment_info(segment_info, tabpage),
			add_multiplier(tabpage, {'mode': ('tab' if tabpage == cur_tabpage else 'nc')})
		)
		for tabpage in list_tabpages()
	]


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
def bufferlister(pl, segment_info, **kwargs):
	'''List all buffers in segment_info format

	Specifically generates a list of segment info dictionaries with ``buffer`` 
	and ``bufnr`` keys set to buffer-specific ones, ``window``, ``winnr`` and 
	``window_id`` keys unset.

	Sets segment ``mode`` to either ``buf`` (for current buffer) or ``nc`` 
	(for all other buffers).
	'''
	cur_buffer = vim.current.buffer
	cur_bufnr = cur_buffer.number

	def add_multiplier(buffer, dct):
		dct['priority_multiplier'] = 1 + (0.001 * abs(buffer.number - cur_bufnr))
		return dct

	return [
		(
			buffer_updated_segment_info(segment_info, buffer),
			add_multiplier(buffer, {'mode': ('tab' if buffer == cur_buffer else 'nc')})
		)
		for buffer in vim.buffers
	]


@requires_segment_info
def tabbuflister(**kwargs):
	if len(list_tabpages()) == 1:
		return bufferlister(**kwargs)
	else:
		return tablister(**kwargs)
