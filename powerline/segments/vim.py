# -*- coding: utf-8 -*-

from __future__ import absolute_import

import os
try:
	import vim
except ImportError:
	vim = {}

from powerline.bindings.vim import vim_get_func, getbufvar
from powerline.theme import requires_segment_info
from powerline.lib import memoize, humanize_bytes
from powerline.lib.vcs import guess
from collections import defaultdict

vim_funcs = {
	'virtcol': vim_get_func('virtcol', rettype=int),
	'fnamemodify': vim_get_func('fnamemodify'),
	'expand': vim_get_func('expand'),
	'getfsize': vim_get_func('getfsize', rettype=int),
	'bufnr': vim_get_func('bufnr', rettype=int),
}

vim_modes = {
	'n': u'NORMAL',
	'no': u'N·OPER',
	'v': u'VISUAL',
	'V': u'V·LINE',
	'^V': u'V·BLCK',
	's': u'SELECT',
	'S': u'S·LINE',
	'^S': u'S·BLCK',
	'i': u'INSERT',
	'R': u'REPLACE',
	'Rv': u'V·RPLCE',
	'c': u'COMMND',
	'cv': u'VIM EX',
	'ce': u'EX',
	'r': u'PROMPT',
	'rm': u'MORE',
	'r?': u'CONFIRM',
	'!': u'SHELL',
}

mode_translations = {
	chr(ord('V') - 0x40): '^V',
	chr(ord('S') - 0x40): '^S',
}


eventcaches = defaultdict(lambda : [])
bufeventcaches = defaultdict(lambda : [])
def purgeonevents_reg(events, eventcaches=bufeventcaches):
	def cache_reg_func(cache):
		for event in events:
			if event not in eventcaches:
				vim.eval('PowerlineRegisterCachePurgerEvent("' + event + '")')
			eventcaches[event].append(cache)

	return cache_reg_func

purgeall_on_shell = purgeonevents_reg(('ShellCmdPost', 'ShellFilterPost', 'FocusGained'), eventcaches=eventcaches)
purgebuf_on_shell_and_write = purgeonevents_reg(('BufWritePost', 'ShellCmdPost', 'ShellFilterPost', 'FocusGained'))


def launchevent(event):
	global eventcaches
	global bufeventcaches
	for cache in eventcaches[event]:
		cache.clear()
	if bufeventcaches[event]:
		buf = int(vim_funcs['expand']('<abuf>'))
		for cache in bufeventcaches[event]:
			try:
				cache.pop(buf)
			except KeyError:
				pass


def bufnr(segment_info, **kwargs):
	'''Used for cache key, returns current buffer number'''
	return segment_info['bufnr']


# TODO Remove cache when needed
def window_cached(func):
	cache = {}

	def ret(segment_info, *args, **kwargs):
		window_id = segment_info['window_id']
		if segment_info['mode'] == 'nc':
			return cache.get(window_id)
		else:
			r = func(*args, **kwargs)
			cache[window_id] = r
			return r
	ret = requires_segment_info(ret)
	ret.__name__ = func.__name__
	return ret


@requires_segment_info
def mode(segment_info, override=None):
	'''Return the current vim mode.

	:param dict override:
		dict for overriding default mode strings, e.g. ``{ 'n': 'NORM' }``
	'''
	mode = segment_info['mode']
	if mode == 'nc':
		return None
	mode = mode_translations.get(mode, mode)
	if not override:
		return vim_modes[mode]
	try:
		return override[mode]
	except KeyError:
		return vim_modes[mode]


@requires_segment_info
def modified_indicator(segment_info, text=u'+'):
	'''Return a file modified indicator.

	:param string text:
		text to display if the current buffer is modified
	'''
	return text if int(getbufvar(segment_info['bufnr'], '&modified')) else None


@requires_segment_info
def paste_indicator(segment_info, text='PASTE'):
	'''Return a paste mode indicator.

	:param string text:
		text to display if paste mode is enabled
	'''
	return text if int(getbufvar(segment_info['bufnr'], '&paste')) else None


@requires_segment_info
def readonly_indicator(segment_info, text=u''):
	'''Return a read-only indicator.

	:param string text:
		text to display if the current buffer is read-only
	'''
	return text if int(getbufvar(segment_info['bufnr'], '&readonly')) else None


@requires_segment_info
def file_directory(segment_info, shorten_home=False):
	'''Return file directory (head component of the file path).

	:param bool shorten_home:
		shorten all directories in :file:`/home/` to :file:`~user/` instead of :file:`/home/user/`.
	'''
	name = segment_info['buffer'].name
	if not name:
		return None
	file_directory = vim_funcs['fnamemodify'](name, ':~:.:h')
	if shorten_home and file_directory.startswith('/home/'):
		file_directory = '~' + file_directory[6:]
	return file_directory.decode('utf-8') + os.sep if file_directory else None


@requires_segment_info
def file_name(segment_info, display_no_file=False, no_file_text='[No file]'):
	'''Return file name (tail component of the file path).

	:param bool display_no_file:
		display a string if the buffer is missing a file name
	:param str no_file_text:
		the string to display if the buffer is missing a file name
	'''
	name = segment_info['buffer'].name
	if not name:
		if display_no_file:
			return [{
				'contents': no_file_text,
				'highlight_group': ['file_name_no_file', 'file_name'],
				}]
		else:
			return None
	file_name = vim_funcs['fnamemodify'](name, ':~:.:t')
	return file_name.decode('utf-8')


@requires_segment_info
@memoize(2, cache_key=bufnr, cache_reg_func=purgebuf_on_shell_and_write)
def file_size(segment_info, suffix='B', binary_prefix=False):
	'''Return file size.

	:param str suffix:
		string appended to the file size
	:param bool binary_prefix:
		use binary prefix, e.g. MiB instead of MB
	:return: file size or None if the file isn't saved or if the size is too big to fit in a number
	'''
	file_name = segment_info['buffer'].name
	file_size = vim_funcs['getfsize'](file_name)
	if file_size < 0:
		return None
	return humanize_bytes(file_size, suffix, binary_prefix)


@requires_segment_info
def file_format(segment_info):
	'''Return file format (i.e. line ending type).

	:return: file format or None if unknown or missing file format
	'''
	return getbufvar(segment_info['bufnr'], '&fileformat') or None


@requires_segment_info
def file_encoding(segment_info):
	'''Return file encoding/character set.

	:return: file encoding/character set or None if unknown or missing file encoding
	'''
	return getbufvar(segment_info['bufnr'], '&fileencoding') or None


@requires_segment_info
def file_type(segment_info):
	'''Return file type.

	:return: file type or None if unknown file type
	'''
	return getbufvar(segment_info['bufnr'], '&filetype') or None


@requires_segment_info
def line_percent(segment_info, gradient=False):
	'''Return the cursor position in the file as a percentage.

	:param bool gradient:
		highlight the percentage with a color gradient (by default a green to red gradient)
	'''
	line_current = segment_info['window'].cursor[0]
	line_last = len(segment_info['buffer'])
	percentage = int(line_current * 100 // line_last)
	if not gradient:
		return percentage
	return [{
		'contents': percentage,
		'highlight_group': ['line_percent_gradient' + str(int(5 * percentage // 100) + 1), 'line_percent'],
		}]


@requires_segment_info
def line_current(segment_info):
	'''Return the current cursor line.'''
	return segment_info['window'].cursor[0]


@requires_segment_info
def col_current(segment_info):
	'''Return the current cursor column.
	'''
	return segment_info['window'].cursor[1] + 1


@window_cached
def virtcol_current():
	'''Return current visual column with concealed characters ingored'''
	return vim_funcs['virtcol']('.')


def modified_buffers(text=u'+', join_str=','):
	'''Return a comma-separated list of modified buffers.

	:param str text:
		text to display before the modified buffer list
	:param str join_str:
		string to use for joining the modified buffer list
	'''
	buffer_len = vim_funcs['bufnr']('$')
	buffer_mod = [str(bufnr) for bufnr in range(1, buffer_len + 1) if int(getbufvar(bufnr, '&modified'))]
	if buffer_mod:
		return u'{0} {1}'.format(text, join_str.join(buffer_mod))
	return None


@requires_segment_info
@memoize(2, cache_key=bufnr, cache_reg_func=purgeall_on_shell)
def branch(segment_info):
	'''Return the current working branch.'''
	repo = guess(path=os.path.abspath(segment_info['buffer'].name or os.getcwd()))
	if repo:
		return repo.branch()
	return None


@requires_segment_info
@memoize(2, cache_key=bufnr, cache_reg_func=purgebuf_on_shell_and_write)
def file_vcs_status(segment_info):
	'''Return the VCS status for this buffer.'''
	name = segment_info['buffer'].name
	if name and not getbufvar(segment_info['bufnr'], '&buftype'):
		repo = guess(path=os.path.abspath(name))
		if repo:
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
	return None


@requires_segment_info
@memoize(2, cache_key=bufnr, cache_reg_func=purgeall_on_shell)
def repository_status(segment_info):
	'''Return the status for the current repo.'''
	repo = guess(path=os.path.abspath(segment_info['buffer'].name or os.getcwd()))
	if repo:
		return repo.status()
	return None
