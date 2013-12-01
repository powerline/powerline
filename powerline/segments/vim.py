# vim:fileencoding=utf-8:noet

from __future__ import unicode_literals, absolute_import, division

import os
try:
	import vim
except ImportError:
	vim = {}  # NOQA

from powerline.bindings.vim import (vim_get_func, getbufvar, vim_getbufoption,
									buffer_name)
from powerline.theme import requires_segment_info
from powerline.lib import add_divider_highlight_group
from powerline.lib.vcs import guess, tree_status
from powerline.lib.humanize_bytes import humanize_bytes
from powerline.lib import wraps_saveargs as wraps
from collections import defaultdict

vim_funcs = {
	'virtcol': vim_get_func('virtcol', rettype=int),
	'getpos': vim_get_func('getpos'),
	'fnamemodify': vim_get_func('fnamemodify'),
	'expand': vim_get_func('expand'),
	'bufnr': vim_get_func('bufnr', rettype=int),
	'line2byte': vim_get_func('line2byte', rettype=int),
	'line': vim_get_func('line', rettype=int),
}

vim_modes = {
	'n': 'NORMAL',
	'no': 'N·OPER',
	'v': 'VISUAL',
	'V': 'V·LINE',
	'^V': 'V·BLCK',
	's': 'SELECT',
	'S': 'S·LINE',
	'^S': 'S·BLCK',
	'i': 'INSERT',
	'R': 'REPLACE',
	'Rv': 'V·RPLCE',
	'c': 'COMMND',
	'cv': 'VIM EX',
	'ce': 'EX',
	'r': 'PROMPT',
	'rm': 'MORE',
	'r?': 'CONFIRM',
	'!': 'SHELL',
}


eventfuncs = defaultdict(lambda: [])
bufeventfuncs = defaultdict(lambda: [])
defined_events = set()


# TODO Remove cache when needed
def window_cached(func):
	cache = {}

	@requires_segment_info
	@wraps(func)
	def ret(segment_info, **kwargs):
		window_id = segment_info['window_id']
		if segment_info['mode'] == 'nc':
			return cache.get(window_id)
		else:
			r = func(**kwargs)
			cache[window_id] = r
			return r

	return ret


@requires_segment_info
def mode(pl, segment_info, override=None):
	'''Return the current vim mode.

	:param dict override:
		dict for overriding default mode strings, e.g. ``{ 'n': 'NORM' }``
	'''
	mode = segment_info['mode']
	if mode == 'nc':
		return None
	if not override:
		return vim_modes[mode]
	try:
		return override[mode]
	except KeyError:
		return vim_modes[mode]


@requires_segment_info
def visual_range(pl, segment_info):
	'''Return the current visual selection range.

	Returns a value similar to `showcmd`.
	'''
	if segment_info['mode'] not in ('v', 'V', '^V'):
		return None
	pos_start = vim_funcs['getpos']('v')
	pos_end = vim_funcs['getpos']('.')
	# Workaround for vim's "excellent" handling of multibyte characters and display widths
	pos_start[2] = vim_funcs['virtcol']([pos_start[1], pos_start[2], pos_start[3]])
	pos_end[2] = vim_funcs['virtcol']([pos_end[1], pos_end[2], pos_end[3]])
	visual_start = (int(pos_start[1]), int(pos_start[2]))
	visual_end = (int(pos_end[1]), int(pos_end[2]))
	diff_rows = abs(visual_end[0] - visual_start[0]) + 1
	diff_cols = abs(visual_end[1] - visual_start[1]) + 1
	if segment_info['mode'] == '^V':
		return '{0} × {1}'.format(diff_rows, diff_cols)
	elif segment_info['mode'] == 'V' or diff_rows > 1:
		return '{0} rows'.format(diff_rows)
	else:
		return '{0} cols'.format(diff_cols)


@requires_segment_info
def modified_indicator(pl, segment_info, text='+'):
	'''Return a file modified indicator.

	:param string text:
		text to display if the current buffer is modified
	'''
	return text if int(vim_getbufoption(segment_info, 'modified')) else None


@requires_segment_info
def paste_indicator(pl, segment_info, text='PASTE'):
	'''Return a paste mode indicator.

	:param string text:
		text to display if paste mode is enabled
	'''
	return text if int(vim.eval('&paste')) else None


@requires_segment_info
def readonly_indicator(pl, segment_info, text=''):
	'''Return a read-only indicator.

	:param string text:
		text to display if the current buffer is read-only
	'''
	return text if int(vim_getbufoption(segment_info, 'readonly')) else None


@requires_segment_info
def file_directory(pl, segment_info, shorten_user=True, shorten_cwd=True, shorten_home=False):
	'''Return file directory (head component of the file path).

	:param bool shorten_user:
		shorten ``$HOME`` directory to :file:`~/`

	:param bool shorten_cwd:
		shorten current directory to :file:`./`

	:param bool shorten_home:
		shorten all directories in :file:`/home/` to :file:`~user/` instead of :file:`/home/user/`.
	'''
	name = buffer_name(segment_info['buffer'])
	if not name:
		return None
	import sys
	file_directory = vim_funcs['fnamemodify'](name, (':~' if shorten_user else '')
												+ (':.' if shorten_cwd else '') + ':h')
	if not file_directory:
		return None
	if shorten_home and file_directory.startswith('/home/'):
		file_directory = b'~' + file_directory[6:]
	file_directory = file_directory.decode('utf-8', 'powerline_vim_strtrans_error')
	return file_directory + os.sep


@requires_segment_info
def file_name(pl, segment_info, display_no_file=False, no_file_text='[No file]'):
	'''Return file name (tail component of the file path).

	:param bool display_no_file:
		display a string if the buffer is missing a file name
	:param str no_file_text:
		the string to display if the buffer is missing a file name

	Highlight groups used: ``file_name_no_file`` or ``file_name``, ``file_name``.
	'''
	name = buffer_name(segment_info['buffer'])
	if not name:
		if display_no_file:
			return [{
				'contents': no_file_text,
				'highlight_group': ['file_name_no_file', 'file_name'],
			}]
		else:
			return None
	return os.path.basename(name).decode('utf-8', 'powerline_vim_strtrans_error')


@window_cached
def file_size(pl, suffix='B', si_prefix=False):
	'''Return file size in &encoding.

	:param str suffix:
		string appended to the file size
	:param bool si_prefix:
		use SI prefix, e.g. MB instead of MiB
	:return: file size or None if the file isn't saved or if the size is too big to fit in a number
	'''
	# Note: returns file size in &encoding, not in &fileencoding. But returned 
	# size is updated immediately; and it is valid for any buffer
	file_size = vim_funcs['line2byte'](len(vim.current.buffer) + 1) - 1
	if file_size < 0:
		file_size = 0
	return humanize_bytes(file_size, suffix, si_prefix)


@requires_segment_info
@add_divider_highlight_group('background:divider')
def file_format(pl, segment_info):
	'''Return file format (i.e. line ending type).

	:return: file format or None if unknown or missing file format

	Divider highlight group used: ``background:divider``.
	'''
	return vim_getbufoption(segment_info, 'fileformat') or None


@requires_segment_info
@add_divider_highlight_group('background:divider')
def file_encoding(pl, segment_info):
	'''Return file encoding/character set.

	:return: file encoding/character set or None if unknown or missing file encoding

	Divider highlight group used: ``background:divider``.
	'''
	return vim_getbufoption(segment_info, 'fileencoding') or None


@requires_segment_info
@add_divider_highlight_group('background:divider')
def file_type(pl, segment_info):
	'''Return file type.

	:return: file type or None if unknown file type

	Divider highlight group used: ``background:divider``.
	'''
	return vim_getbufoption(segment_info, 'filetype') or None


@requires_segment_info
def line_percent(pl, segment_info, gradient=False):
	'''Return the cursor position in the file as a percentage.

	:param bool gradient:
		highlight the percentage with a color gradient (by default a green to red gradient)

	Highlight groups used: ``line_percent_gradient`` (gradient), ``line_percent``.
	'''
	line_current = segment_info['window'].cursor[0]
	line_last = len(segment_info['buffer'])
	percentage = line_current * 100.0 / line_last
	if not gradient:
		return str(int(round(percentage)))
	return [{
		'contents': str(int(round(percentage))),
		'highlight_group': ['line_percent_gradient', 'line_percent'],
		'gradient_level': percentage,
	}]


@window_cached
def position(pl, position_strings={'top':'Top', 'bottom':'Bot', 'all':'All'}, gradient=False):
	'''Return the position of the current view in the file as a percentage.

	:param dict position_strings:
		dict for translation of the position strings, e.g. ``{"top":"Oben", "bottom":"Unten", "all":"Alles"}``

	:param bool gradient:
		highlight the percentage with a color gradient (by default a green to red gradient)

	Highlight groups used: ``position_gradient`` (gradient), ``position``.
	'''
	line_last = len(vim.current.buffer)

	winline_first = vim_funcs['line']('w0')
	winline_last = vim_funcs['line']('w$')
	if winline_first == 1 and winline_last == line_last:
		percentage = 0.0
		content = position_strings['all']
	elif winline_first == 1:
		percentage = 0.0
		content = position_strings['top']
	elif winline_last == line_last:
		percentage = 100.0
		content = position_strings['bottom']
	else:
		percentage = winline_first * 100.0 / (line_last - winline_last + winline_first)
		content = str(int(round(percentage))) + '%'

	if not gradient:
		return content
	return [{
		'contents': content,
		'highlight_group': ['position_gradient', 'position'],
		'gradient_level': percentage,
	}]


@requires_segment_info
def line_current(pl, segment_info):
	'''Return the current cursor line.'''
	return str(segment_info['window'].cursor[0])


@requires_segment_info
def col_current(pl, segment_info):
	'''Return the current cursor column.
	'''
	return str(segment_info['window'].cursor[1] + 1)


# TODO Add &textwidth-based gradient
@window_cached
def virtcol_current(pl, gradient=True):
	'''Return current visual column with concealed characters ingored

	:param bool gradient:
		Determines whether it should show textwidth-based gradient (gradient level is ``virtcol * 100 / textwidth``).

	Highlight groups used: ``virtcol_current_gradient`` (gradient), ``virtcol_current`` or ``col_current``.
	'''
	col = vim_funcs['virtcol']('.')
	r = [{'contents': str(col), 'highlight_group': ['virtcol_current', 'col_current']}]
	if gradient:
		textwidth = int(getbufvar('%', '&textwidth'))
		r[-1]['gradient_level'] = min(col * 100 / textwidth, 100) if textwidth else 0
		r[-1]['highlight_group'].insert(0, 'virtcol_current_gradient')
	return r


def modified_buffers(pl, text='+ ', join_str=','):
	'''Return a comma-separated list of modified buffers.

	:param str text:
		text to display before the modified buffer list
	:param str join_str:
		string to use for joining the modified buffer list
	'''
	buffer_len = vim_funcs['bufnr']('$')
	buffer_mod = [str(bufnr) for bufnr in range(1, buffer_len + 1) if int(getbufvar(bufnr, '&modified') or 0)]
	if buffer_mod:
		return text + join_str.join(buffer_mod)
	return None

@requires_segment_info
def branch(pl, segment_info, status_colors=False):
	'''Return the current working branch.

	:param bool status_colors:
		determines whether repository status will be used to determine highlighting. Default: False.

	Highlight groups used: ``branch_clean``, ``branch_dirty``, ``branch``.

	Divider highlight group used: ``branch:divider``.
	'''
	name = segment_info['buffer'].name
	skip = not (name and (not vim_getbufoption(segment_info, 'buftype')))
	if not skip:
		repo = guess(path=name)
		if repo is not None:
			branch = repo.branch()
			scol = ['branch']
			if status_colors:
				status = tree_status(repo, pl)
				scol.insert(0, 'branch_dirty' if status and status.strip() else 'branch_clean')
			return [{
				'contents': branch,
				'highlight_group': scol,
				'divider_highlight_group': 'branch:divider',
			}]

@requires_segment_info
def file_vcs_status(pl, segment_info):
	'''Return the VCS status for this buffer.

	Highlight groups used: ``file_vcs_status``.
	'''
	name = segment_info['buffer'].name
	skip = not (name and (not vim_getbufoption(segment_info, 'buftype')))
	if not skip:
		repo = guess(path=name)
		if repo is not None:
			status = repo.status(os.path.relpath(name, repo.directory))
			if not status:
				return None
			status = status.strip()
			ret = []
			for status in status:
				ret.append({
					'contents': status,
					'highlight_group': ['file_vcs_status_' + status, 'file_vcs_status'],
					})
			return ret
