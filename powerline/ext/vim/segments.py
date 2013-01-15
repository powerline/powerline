# -*- coding: utf-8 -*-

import os
import vim

from powerline.ext.vim.bindings import vim_get_func
from powerline.lib.memoize import memoize
from powerline.lib.vcs import guess

vim_funcs = {
	'col': vim_get_func('col', rettype=int),
	'virtcol': vim_get_func('virtcol', rettype=int),
	'expand': vim_get_func('expand'),
	'line': vim_get_func('line', rettype=int),
	'mode': vim_get_func('mode'),
}

vim_modes = {
	'n': u'NORMAL',
	'no': u'N·OPER',
	'v': u'VISUAL',
	'V': u'V·LINE',
	'': u'V·BLCK',
	's': u'SELECT',
	'S': u'S·LINE',
	'': u'S·BLCK',
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


def mode(override=None):
	'''Return the current vim mode.

	This function returns a tuple with the shorthand mode and the mode expanded
	into a descriptive string. The longer string can be overridden by providing
	a dict with the mode and the new string::

		mode = mode({ 'n': 'NORM' })
	'''
	mode = vim_funcs['mode']()
	if not override:
		return vim_modes[mode]
	try:
		return override[mode]
	except IndexError:
		return vim_modes[mode]


def modified_indicator(text=u'+'):
	'''Return a file modified indicator.'''
	return text if int(vim.eval('&modified')) else None


def paste_indicator(text='PASTE'):
	'''Return a paste mode indicator.'''
	return text if int(vim.eval('&paste')) else None


def readonly_indicator(text=u''):
	'''Return a read-only indicator.'''
	return text if int(vim.eval('&readonly')) else None


def file_directory():
	'''Return file directory (head component of the file path).'''
	file_directory = vim_funcs['expand']('%:~:.:h')
	return file_directory + os.sep if file_directory else None


def file_name(display_no_file=False, no_file_text='[No file]'):
	'''Return file name (tail component of the file path).'''
	file_name = vim_funcs['expand']('%:~:.:t')
	if not file_name and not display_no_file:
		return None
	if not file_name:
		return {
			'contents': no_file_text,
			'highlight': ['file_name_no_file', 'file_name'],
			}
	return file_name


def file_format():
	'''Return file format (i.e. line ending type).

	Returns None for unknown or missing file format.
	'''
	return vim.eval('&fileformat') or None


def file_encoding():
	'''Return file encoding/character set.

	Returns None for unknown or missing file encoding.
	'''
	return vim.eval('&fileencoding') or None


def file_type():
	'''Return file type.

	Returns None for unknown file types.
	'''
	return vim.eval('&filetype') or None


def line_percent(gradient=False):
	'''Return the cursor position in the file as a percentage.'''
	line_current = vim_funcs['line']('.')
	line_last = vim_funcs['line']('$')
	percentage = int(line_current * 100 // line_last)
	if not gradient:
		return percentage
	return {
		'contents': percentage,
		'highlight': ['line_percent_gradient' + str(int(5 * percentage // 100) + 1), 'line_percent'],
		}


def line_current():
	'''Return the current cursor line.'''
	return vim_funcs['line']('.')


def col_current(virtcol=True):
	'''Return the current cursor column.

	If the optional argument is True then returns visual column with concealed
	characters ignored (default), else returns byte offset.
	'''
	return vim_funcs['virtcol' if virtcol else 'col']('.')


@memoize(2)
def branch():
	repo = guess(os.path.abspath(vim.current.buffer.name or os.getcwd()))
	if repo:
		return repo.branch()
	return None


# TODO Drop cache on BufWrite event
@memoize(2, additional_key=lambda: vim.current.buffer.number)
def file_vcs_status():
	if vim.current.buffer.name and not vim.eval('&buftype'):
		repo = guess(os.path.abspath(vim.current.buffer.name))
		if repo:
			status = repo.status(os.path.relpath(vim.current.buffer.name, repo.directory))
			if not status:
				return None
			status = status.strip()
			return {
				'contents': status,
				'highlight': ['file_vcs_status_' + status, 'file_vcs_status'],
				}
	return None
