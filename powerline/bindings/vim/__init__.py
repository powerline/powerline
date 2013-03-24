# vim:fileencoding=utf-8:noet

import sys

try:
	import vim
except ImportError:
	vim = {}

try:
	_vim_globals = vim.bindeval('g:')

	def vim_set_global_var(var, val):
		'''Set a global var in vim using bindeval().'''
		_vim_globals[var] = val

	def vim_get_func(f, rettype=None):
		'''Return a vim function binding.'''
		try:
			func = vim.bindeval('function("' + f + '")')
			if sys.version_info >= (3,) and rettype is str:
				return (lambda *args, **kwargs: func(*args, **kwargs).decode('utf-8', errors='replace'))
			return func
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

if sys.version_info < (3,) or not hasattr(vim, 'bindeval'):
	getbufvar = vim_get_func('getbufvar')
else:
	_getbufvar = vim_get_func('getbufvar')

	def getbufvar(*args):
		r = _getbufvar(*args)
		if type(r) is bytes:
			return r.decode('utf-8')
		return r
