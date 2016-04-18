# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import sys
import codecs

try:
	import vim
except ImportError:
	vim = object()

from powerline.lib.unicode import unicode


if (
	hasattr(vim, 'options')
	and hasattr(vim, 'vvars')
	and vim.vvars['version'] > 703
):
	if sys.version_info < (3,):
		def get_vim_encoding():
			return vim.options['encoding'] or 'ascii'
	else:
		def get_vim_encoding():
			return vim.options['encoding'].decode('ascii') or 'ascii'
elif hasattr(vim, 'eval'):
	def get_vim_encoding():
		return vim.eval('&encoding') or 'ascii'
else:
	def get_vim_encoding():
		return 'utf-8'

get_vim_encoding.__doc__ = (
	'''Get encoding used for Vim strings

	:return:
		Value of ``&encoding``. If it is empty (i.e. Vim is compiled 
		without +multibyte) returns ``'ascii'``. When building documentation 
		outputs ``'utf-8'`` unconditionally.
	'''
)


vim_encoding = get_vim_encoding()


python_to_vim_types = {
	unicode: (
		lambda o: b'\'' + (o.translate({
			ord('\''): '\'\'',
		}).encode(vim_encoding)) + b'\''
	),
	list: (
		lambda o: b'[' + (
			b','.join((python_to_vim(i) for i in o))
		) + b']'
	),
	bytes: (lambda o: b'\'' + o.replace(b'\'', b'\'\'') + b'\''),
	int: (str if str is bytes else (lambda o: unicode(o).encode('ascii'))),
}
python_to_vim_types[float] = python_to_vim_types[int]


def python_to_vim(o):
	return python_to_vim_types[type(o)](o)


if sys.version_info < (3,):
	def str_to_bytes(s):
		return s

	def unicode_eval(expr):
		ret = vim.eval(expr)
		return ret.decode(vim_encoding, 'powerline_vim_strtrans_error')
else:
	def str_to_bytes(s):
		return s.encode(vim_encoding)

	def unicode_eval(expr):
		return vim.eval(expr)


def safe_bytes_eval(expr):
	return bytes(bytearray((
		int(chunk) for chunk in (
			vim.eval(
				b'substitute(' + expr + b', ' +
				b'\'^.*$\', \'\\=join(map(range(len(submatch(0))), ' +
				b'"char2nr(submatch(0)[v:val])"))\', "")'
			).split()
		)
	)))


def eval_bytes(expr):
	try:
		return str_to_bytes(vim.eval(expr))
	except UnicodeDecodeError:
		return safe_bytes_eval(expr)


def eval_unicode(expr):
	try:
		return unicode_eval(expr)
	except UnicodeDecodeError:
		return safe_bytes_eval(expr).decode(vim_encoding, 'powerline_vim_strtrans_error')


if hasattr(vim, 'bindeval'):
	rettype_func = {
		None: lambda f: f,
		'unicode': (
			lambda f: (
				lambda *args, **kwargs: (
					f(*args, **kwargs).decode(
						vim_encoding, 'powerline_vim_strtrans_error'
					))))
	}
	rettype_func['int'] = rettype_func['bytes'] = rettype_func[None]
	rettype_func['str'] = rettype_func['bytes'] if str is bytes else rettype_func['unicode']

	def vim_get_func(f, rettype=None):
		'''Return a vim function binding.'''
		try:
			func = vim.bindeval('function("' + f + '")')
		except vim.error:
			return None
		else:
			return rettype_func[rettype](func)
else:
	rettype_eval = {
		None: getattr(vim, 'eval', None),
		'int': lambda expr: int(vim.eval(expr)),
		'bytes': eval_bytes,
		'unicode': eval_unicode,
	}
	rettype_eval['str'] = rettype_eval[None]

	class VimFunc(object):
		'''Evaluate a vim function using vim.eval().

		This is a fallback class for older vim versions.
		'''
		__slots__ = ('f', 'eval')

		def __init__(self, f, rettype=None):
			self.f = f.encode('utf-8')
			self.eval = rettype_eval[rettype]

		def __call__(self, *args):
			return self.eval(self.f + b'(' + (b','.join((
				python_to_vim(o) for o in args
			))) + b')')

	vim_get_func = VimFunc


def vim_get_autoload_func(f, rettype=None):
	func = vim_get_func(f)
	if not func:
		vim.command('runtime! ' + f.replace('#', '/')[:f.rindex('#')] + '.vim')
		func = vim_get_func(f)
	return func


if hasattr(vim, 'Function'):
	def vim_func_exists(f):
		try:
			vim.Function(f)
		except ValueError:
			return False
		else:
			return True
else:
	def vim_func_exists(f):
		try:
			return bool(int(vim.eval('exists("*{0}")'.format(f))))
		except vim.error:
			return False


if type(vim) is object:
	vim_get_func = lambda *args, **kwargs: None


_getbufvar = vim_get_func('getbufvar')
_vim_exists = vim_get_func('exists', rettype='int')


# It may crash on some old vim versions and I do not remember in which patch 
# I fixed this crash.
if hasattr(vim, 'vvars') and vim.vvars[str('version')] > 703:
	_vim_to_python_types = {
		getattr(vim, 'Dictionary', None) or type(vim.bindeval('{}')):
			lambda value: dict((
				(_vim_to_python(k), _vim_to_python(v))
				for k, v in value.items()
			)),
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

	def vim_global_exists(name):
		try:
			vim.vars[name]
		except KeyError:
			return False
		else:
			return True
else:
	_vim_to_python_types = {
		dict: (lambda value: dict(((k, _vim_to_python(v)) for k, v in value.items()))),
		list: (lambda value: [_vim_to_python(i) for i in value]),
	}

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

	def vim_global_exists(name):
		return int(vim.eval('exists("g:' + name + '")'))


def vim_command_exists(name):
	return _vim_exists(':' + name)


if sys.version_info < (3,):
	getbufvar = _getbufvar
else:
	_vim_to_python_types[bytes] = lambda value: value.decode(vim_encoding)

	def getbufvar(*args):
		return _vim_to_python(_getbufvar(*args))


_id = lambda value: value


def _vim_to_python(value):
	return _vim_to_python_types.get(type(value), _id)(value)


if hasattr(vim, 'options'):
	def vim_getbufoption(info, option):
		return _vim_to_python(info['buffer'].options[str(option)])

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
			option=option, value=python_to_vim(value)))


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
	def buffer_name(segment_info):
		return segment_info['buffer'].name
else:
	vim_bufname = vim_get_func('bufname', rettype='bytes')

	def buffer_name(segment_info):
		try:
			name = segment_info['buffer'].name
		except UnicodeDecodeError:
			return vim_bufname(segment_info['bufnr'])
		else:
			return name.encode(segment_info['encoding']) if name else None


vim_strtrans = vim_get_func('strtrans', rettype='unicode')


def powerline_vim_strtrans_error(e):
	if not isinstance(e, UnicodeDecodeError):
		raise NotImplementedError
	text = vim_strtrans(e.object[e.start:e.end])
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


def create_ruby_dpowerline():
	vim.command((
		'''
		ruby
		if $powerline == nil
			class Powerline
			end
			$powerline = Powerline.new
		end
		'''
	))
