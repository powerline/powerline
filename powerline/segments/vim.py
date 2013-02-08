# -*- coding: utf-8 -*-

from __future__ import absolute_import

import os
try:
	import vim
except ImportError:
	vim = {}

from powerline.bindings.vim import vim_get_func
from powerline.lib import memoize, humanize_bytes
from powerline.lib.vcs import guess

vim_funcs = {
	'col': vim_get_func('col', rettype=int),
	'virtcol': vim_get_func('virtcol', rettype=int),
	'expand': vim_get_func('expand'),
	'line': vim_get_func('line', rettype=int),
	'mode': vim_get_func('mode'),
	'getfsize': vim_get_func('getfsize', rettype=int),
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


def mode(override=None):
	'''Return the current vim mode.

	:param dict override:
		dict for overriding default mode strings, e.g. ``{ 'n': 'NORM' }``
	'''
	mode = vim_funcs['mode']().decode('utf-8')
	mode = mode_translations.get(mode, mode)
	if not override:
		return vim_modes[mode]
	try:
		return override[mode]
	except KeyError:
		return vim_modes[mode]


def modified_indicator(text=u'+'):
	'''Return a file modified indicator.

	:param string text:
		text to display if the current buffer is modified
	'''
	return text if int(vim.eval('&modified')) else None


def paste_indicator(text='PASTE'):
	'''Return a paste mode indicator.

	:param string text:
		text to display if paste mode is enabled
	'''
	return text if int(vim.eval('&paste')) else None


def readonly_indicator(text=u''):
	'''Return a read-only indicator.

	:param string text:
		text to display if the current buffer is read-only
	'''
	return text if int(vim.eval('&readonly')) else None


def file_directory(shorten_home=False):
	'''Return file directory (head component of the file path).

	:param bool shorten_home:
		shorten all directories in :file:`/home/` to :file:`~user/` instead of :file:`/home/user/`.
	'''
	file_directory = vim_funcs['expand']('%:~:.:h')
	if file_directory is None:
		return None
	if shorten_home and file_directory.startswith('/home/'):
		file_directory = '~' + file_directory[6:]
	return file_directory.decode('utf-8') + os.sep if file_directory else None


def file_name(display_no_file=False, no_file_text='[No file]'):
	'''Return file name (tail component of the file path).

	:param bool display_no_file:
		display a string if the buffer is missing a file name
	:param str no_file_text:
		the string to display if the buffer is missing a file name
	'''
	file_name = vim_funcs['expand']('%:~:.:t')
	if not file_name and not display_no_file:
		return None
	if not file_name:
		return [{
			'contents': no_file_text,
			'highlight_group': ['file_name_no_file', 'file_name'],
			}]
	return file_name.decode('utf-8')


@memoize(2)
def file_size(suffix='B', binary_prefix=False):
	'''Return file size.

	:param str suffix:
		string appended to the file size
	:param bool binary_prefix:
		use binary prefix, e.g. MiB instead of MB
	:return: file size or None if the file isn't saved or if the size is too big to fit in a number
	'''
	file_name = vim_funcs['expand']('%')
	file_size = vim_funcs['getfsize'](file_name)
	if file_size < 0:
		return None
	return humanize_bytes(file_size, suffix, binary_prefix)


def file_format():
	'''Return file format (i.e. line ending type).

	:return: file format or None if unknown or missing file format
	'''
	return vim.eval('&fileformat') or None


def file_encoding():
	'''Return file encoding/character set.

	:return: file encoding/character set or None if unknown or missing file encoding
	'''
	return vim.eval('&fileencoding') or None


def file_type():
	'''Return file type.

	:return: file type or None if unknown file type
	'''
	return vim.eval('&filetype') or None


def line_percent(gradient=False):
	'''Return the cursor position in the file as a percentage.

	:param bool gradient:
		highlight the percentage with a color gradient (by default a green to red gradient)
	'''
	line_current = vim_funcs['line']('.')
	line_last = vim_funcs['line']('$')
	percentage = int(line_current * 100 // line_last)
	if not gradient:
		return percentage
	return [{
		'contents': percentage,
		'highlight_group': ['line_percent_gradient' + str(int(5 * percentage // 100) + 1), 'line_percent'],
		}]


def line_current():
	'''Return the current cursor line.'''
	return vim_funcs['line']('.')


def col_current(virtcol=True):
	'''Return the current cursor column.

	:param bool virtcol:
		return visual column with concealed characters ingored
	'''
	return vim_funcs['virtcol' if virtcol else 'col']('.')


def modified_buffers(text=u'+', join_str=','):
	'''Return a comma-separated list of modified buffers.

	:param str text:
		text to display before the modified buffer list
	:param str join_str:
		string to use for joining the modified buffer list
	'''
	buffer_len = int(vim.eval('bufnr("$")'))
	buffer_mod = [str(bufnr) for bufnr in range(1, buffer_len + 1) if vim.eval('getbufvar({0}, "&mod")'.format(bufnr)) == '1']
	if buffer_mod:
		return u'{0} {1}'.format(text, join_str.join(buffer_mod))
	return None


@memoize(2)
def branch():
	'''Return the current working branch.'''
	repo = guess(os.path.abspath(vim.current.buffer.name or os.getcwd()))
	if repo:
		return repo.branch()
	return None


# TODO Drop cache on BufWrite event
@memoize(2, additional_key=lambda: vim.current.buffer.number)
def file_vcs_status():
	'''Return the VCS status for this buffer.'''
	if vim.current.buffer.name and not vim.eval('&buftype'):
		repo = guess(os.path.abspath(vim.current.buffer.name))
		if repo:
			status = repo.status(os.path.relpath(vim.current.buffer.name, repo.directory))
			if not status:
				return None
			status = status.strip()
			ret = []
			for status in status:
				ret.append({
					'contents': status,
					'highlight_group': ['file_vcs_status_' + status, 'file_vcs_status'],
					})
			ret[0]['before'] = ' '
			return ret
	return None


@memoize(2)
def repository_status():
	'''Return the status for the current repo.'''
	repo = guess(os.path.abspath(vim.current.buffer.name or os.getcwd()))
	if repo:
		return repo.status()
	return None
