# -*- coding: utf-8 -*-

import os
import vim

from powerline.ext.vim.bindings import vim_get_func

vim_funcs = {
	'col': vim_get_func('col', rettype=int),
	'expand': vim_get_func('expand'),
	'line': vim_get_func('line', rettype=int),
	'mode': vim_get_func('mode'),
	'vcs': {
		'fugitive': vim_get_func('fugitive#head'),
	},
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
	'''Return a file modified indicator.
	'''
	return text if int(vim.eval('&modified')) else None


def paste_indicator(text='PASTE'):
	'''Return a paste mode indicator.
	'''
	return text if int(vim.eval('&paste')) else None


def readonly_indicator(text=u'⭤'):
	'''Return a read-only indicator.
	'''
	return text if int(vim.eval('&readonly')) else None


def branch():
	'''Return VCS branch.

	TODO: Expand this function to handle several VCS plugins.
	'''
	branch = None
	try:
		branch = vim_funcs['vcs']['fugitive'](5)
	except vim.error:
		vim_funcs['vcs']['fugitive'] = None
	except TypeError:
		pass

	return branch if branch else None


def file_directory():
	'''Return file directory (head component of the file path).
	'''
	return vim_funcs['expand']('%:~:.:h') + os.sep


def file_name():
	'''Return file name (tail component of the file path).
	'''
	return vim_funcs['expand']('%:~:.:t')


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
	'''Return the cursor position in the file as a percentage.
	'''
	line_current = vim_funcs['line']('.')
	line_last = vim_funcs['line']('$')
	percentage = int(line_current * 100 // line_last)

	if not gradient:
		return percentage

	return {
		'contents': percentage,
		'highlight': 'line_percent_gradient' + str(int(5 * percentage // 100) + 1),
	}


def line_current():
	'''Return the current cursor line.
	'''
	return vim_funcs['line']('.')


def col_current():
	'''Return the current cursor column.
	'''
	return vim_funcs['col']('.')
