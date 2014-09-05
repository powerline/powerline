# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import sys
import codecs

try:
	import vim
except ImportError:
	vim = {}

if not hasattr(vim, 'bindeval'):
	import json


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


_getbufvar = vim_get_func('getbufvar')


# It may crash on some old vim versions and I do not remember in which patch 
# I fixed this crash.
if hasattr(vim, 'vvars') and vim.vvars['version'] > 703:
	_vim_to_python_types = {
		getattr(vim, 'Dictionary', None) or type(vim.bindeval('{}')):
			lambda value: dict(((key, _vim_to_python(value[key])) for key in value.keys())),
		getattr(vim, 'List', None) or type(vim.bindeval('[]')):
			lambda value: [_vim_to_python(item) for item in value],
		getattr(vim, 'Function', None) or type(vim.bindeval('function("mode")')):
			lambda _: None,
	}

	def vim_getvar(varname):
		return _vim_to_python(vim.vars[str(varname)])

	def bufvar_exists(buffer, varname):
		buffer = buffer or vim.current.buffer
		return varname in buffer.vars

	def vim_getwinvar(segment_info, varname):
		return _vim_to_python(segment_info['window'].vars[str(varname)])
else:
	_vim_to_python_types = {
		dict: (lambda value: dict(((k, _vim_to_python(v)) for k, v in value.items()))),
		list: (lambda value: [_vim_to_python(i) for i in value]),
	}

	_vim_exists = vim_get_func('exists', rettype=int)

	def vim_getvar(varname):
		varname = 'g:' + varname
		if _vim_exists(varname):
			return vim.eval(varname)
		else:
			raise KeyError(varname)

	def bufvar_exists(buffer, varname):
		if not buffer or buffer.number == vim.current.buffer.number:
			return int(vim.eval('exists("b:{0}")'.format(varname)))
		else:
			return int(vim.eval(
				'has_key(getbufvar({0}, ""), {1})'.format(buffer.number, varname)
			))

	def vim_getwinvar(segment_info, varname):
		result = vim.eval('getwinvar({0}, "{1}")'.format(segment_info['winnr'], varname))
		if result == '':
			if not int(vim.eval('has_key(getwinvar({0}, ""), "{1}")'.format(segment_info['winnr'], varname))):
				raise KeyError(varname)
		return result


if sys.version_info < (3,):
	getbufvar = _getbufvar
else:
	_vim_to_python_types[bytes] = lambda value: value.decode('utf-8')

	def getbufvar(*args):
		return _vim_to_python(_getbufvar(*args))


_id = lambda value: value


def _vim_to_python(value):
	return _vim_to_python_types.get(type(value), _id)(value)


if hasattr(vim, 'options'):
	def vim_getbufoption(info, option):
		return info['buffer'].options[str(option)]

	def vim_getoption(option):
		return vim.options[str(option)]

	def vim_setoption(option, value):
		vim.options[str(option)] = value
else:
	def vim_getbufoption(info, option):
		return getbufvar(info['bufnr'], '&' + option)

	def vim_getoption(option):
		return vim.eval('&g:' + option)

	def vim_setoption(option, value):
		vim.command('let &g:{option} = {value}'.format(
			option=option, value=json.encode(value)))


if hasattr(vim, 'tabpages'):
	current_tabpage = lambda: vim.current.tabpage
	list_tabpages = lambda: vim.tabpages

	def list_tabpage_buffers_segment_info(segment_info):
		return (
			{'buffer': window.buffer, 'bufnr': window.buffer.number}
			for window in segment_info['tabpage'].windows
		)
else:
	class FalseObject(object):
		@staticmethod
		def __nonzero__():
			return False

		__bool__ = __nonzero__

	def get_buffer(number):
		for buffer in vim.buffers:
			if buffer.number == number:
				return buffer
		raise KeyError(number)

	class WindowVars(object):
		__slots__ = ('tabnr', 'winnr')

		def __init__(self, window):
			self.tabnr = window.tabnr
			self.winnr = window.number

		def __getitem__(self, key):
			has_key = vim.eval('has_key(gettabwinvar({0}, {1}, ""), "{2}")'.format(self.tabnr, self.winnr, key))
			if has_key == '0':
				raise KeyError
			return vim.eval('gettabwinvar({0}, {1}, "{2}")'.format(self.tabnr, self.winnr, key))

		def get(self, key, default=None):
			try:
				return self[key]
			except KeyError:
				return default

	class Window(FalseObject):
		__slots__ = ('tabnr', 'number', '_vars')

		def __init__(self, tabnr, number):
			self.tabnr = tabnr
			self.number = number
			self.vars = WindowVars(self)

		@property
		def buffer(self):
			return get_buffer(int(vim.eval('tabpagebuflist({0})[{1}]'.format(self.tabnr, self.number - 1))))

	class Tabpage(FalseObject):
		__slots__ = ('number',)

		def __init__(self, number):
			self.number = number

		def __eq__(self, tabpage):
			if not isinstance(tabpage, Tabpage):
				raise NotImplementedError
			return self.number == tabpage.number

		@property
		def window(self):
			return Window(self.number, int(vim.eval('tabpagewinnr({0})'.format(self.number))))

	def _last_tab_nr():
		return int(vim.eval('tabpagenr("$")'))

	def current_tabpage():
		return Tabpage(int(vim.eval('tabpagenr()')))

	def list_tabpages():
		return [Tabpage(nr) for nr in range(1, _last_tab_nr() + 1)]

	class TabBufSegmentInfo(dict):
		def __getitem__(self, key):
			try:
				return super(TabBufSegmentInfo, self).__getitem__(key)
			except KeyError:
				if key != 'buffer':
					raise
				else:
					buffer = get_buffer(super(TabBufSegmentInfo, self).__getitem__('bufnr'))
					self['buffer'] = buffer
					return buffer

	def list_tabpage_buffers_segment_info(segment_info):
		return (
			TabBufSegmentInfo(bufnr=int(bufnrstr))
			for bufnrstr in vim.eval('tabpagebuflist({0})'.format(segment_info['tabnr']))
		)


class VimEnviron(object):
	@staticmethod
	def __getitem__(key):
		return vim.eval('$' + key)

	@staticmethod
	def get(key, default=None):
		return vim.eval('$' + key) or default

	@staticmethod
	def __setitem__(key, value):
		return vim.command(
			'let ${0}="{1}"'.format(
				key,
				value.replace('"', '\\"')
				     .replace('\\', '\\\\')
				     .replace('\n', '\\n')
				     .replace('\0', '')
			)
		)


if sys.version_info < (3,):
	def buffer_name(buf):
		return buf.name
else:
	vim_bufname = vim_get_func('bufname')

	def buffer_name(buf):
		try:
			name = buf.name
		except UnicodeDecodeError:
			return vim_bufname(buf.number)
		else:
			return name.encode('utf-8') if name else None


vim_strtrans = vim_get_func('strtrans')


def powerline_vim_strtrans_error(e):
	if not isinstance(e, UnicodeDecodeError):
		raise NotImplementedError
	# Assuming &encoding is utf-8 strtrans should not return anything but ASCII 
	# under current circumstances
	text = vim_strtrans(e.object[e.start:e.end]).decode()
	return (text, e.end)


codecs.register_error('powerline_vim_strtrans_error', powerline_vim_strtrans_error)


did_autocmd = False
buffer_caches = []


def register_buffer_cache(cachedict):
	global did_autocmd
	global buffer_caches
	from powerline.vim import get_default_pycmd, pycmd
	if not did_autocmd:
		import __main__
		__main__.powerline_on_bwipe = on_bwipe
		vim.command('augroup Powerline')
		vim.command('	autocmd! BufWipeout * :{pycmd} powerline_on_bwipe()'.format(
			pycmd=(pycmd or get_default_pycmd())))
		vim.command('augroup END')
		did_autocmd = True
	buffer_caches.append(cachedict)
	return cachedict


def on_bwipe():
	global buffer_caches
	bufnr = int(vim.eval('expand("<abuf>")'))
	for cachedict in buffer_caches:
		cachedict.pop(bufnr, None)


environ = VimEnviron()
