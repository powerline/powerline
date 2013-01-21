# -*- coding: utf-8 -*-

import vim


def source_plugin():
	import sys
	import os
	if sys.version_info[:2] == (3, 3):
		vim.command('let g:powerline_pycmd = "python3"')
		vim.command('let g:powerline_pyeval = "py3eval"')
	else:
		vim.command('let g:powerline_pycmd = "python"')
		vim.command('let g:powerline_pyeval = "pyeval"')
	fnameescape = vim_get_func('fnameescape')
	vim.command('source ' + fnameescape(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'powerline.vim')).decode('utf-8'))

try:
	_vim_globals = vim.bindeval('g:')

	def vim_set_global_var(var, val):
		'''Set a global var in vim using bindeval().'''
		_vim_globals[var] = val

	def vim_get_func(f, rettype=None):
		'''Return a vim function binding.'''
		try:
			return vim.bindeval('function("' + f + '")')
		except vim.error:
			return None
except AttributeError:
	import json

	def vim_set_global_var(var, val):  # NOQA
		'''Set a global var in vim using vim.command().

		This is a fallback function for older vim versions.
		'''
		vim.command('let g:{0}={1}'.format(var, json.dumps(val)))

	class VimFunc(object):
		'''Evaluate a vim function using vim.eval().

		This is a fallback class for older vim versions.
		'''
		__slots__ = ('f', 'rettype')

		def __init__(self, f, rettype=None):
			self.f = f
			self.rettype = rettype

		def __call__(self, *args):
			r = vim.eval(self.f + '(' + json.dumps(args)[1:-1] + ')')
			if self.rettype:
				return self.rettype(r)
			return r

	vim_get_func = VimFunc
