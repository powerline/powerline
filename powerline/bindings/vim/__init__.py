# vim:fileencoding=utf-8:noet

import sys

try:
	import vim
except ImportError:
	vim = {}

if hasattr(vim, 'bindeval'):
	def vim_get_func(f, rettype=None):
		'''Return a vim function binding.'''
		try:
			func = vim.bindeval('function("' + f + '")')
			if sys.version_info >= (3,) and rettype is str:
				return (lambda *args, **kwargs: func(*args, **kwargs).decode('utf-8', errors='replace'))
			return func
		except vim.error:
			return None
else:
	import json

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


if hasattr(vim, 'vars'):
	def vim_getvar(varname):
		return vim.vars[str(varname)]
elif hasattr(vim, 'bindeval'):
	_vim_globals = vim.bindeval('g:')

	def vim_getvar(varname):  # NOQA
		try:
			return _vim_globals[str(varname)]
		except (KeyError, IndexError):
			raise KeyError(varname)
else:
	_vim_exists = vim_get_func('exists', rettype=int)

	def vim_getvar(varname):  # NOQA
		varname = 'g:' + varname
		if _vim_exists(varname):
			return vim.eval(varname)
		else:
			raise KeyError(varname)

if hasattr(vim, 'options'):
	def vim_getbufoption(info, option):
		return info['buffer'].options[option]
else:
	def vim_getbufoption(info, option):  # NOQA
		return getbufvar(info['bufnr'], '&' + option)


if sys.version_info < (3,) or not hasattr(vim, 'bindeval'):
	getbufvar = vim_get_func('getbufvar')
else:
	_getbufvar = vim_get_func('getbufvar')

	def getbufvar(*args):
		r = _getbufvar(*args)
		if type(r) is bytes:
			return r.decode('utf-8')
		return r


class VimEnviron(object):
	@staticmethod
	def __getitem__(key):
		return vim.eval('$' + key)

	@staticmethod
	def get(key, default=None):
		return vim.eval('$' + key) or default

	@staticmethod
	def __setitem__(key, value):
		return vim.command('let $' + key + '="'
					+ value.replace('"', '\\"').replace('\\', '\\\\').replace('\n', '\\n').replace('\0', '')
					+ '"')

environ = VimEnviron()
