# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import sys
import codecs

from functools import partial

from powerline.lib.unicode import unicode


def get_vim_encoding(vim):
	'''Get encoding used for Vim strings

	:param module vim:
		Vim module.

	:return:
		Value of ``&encoding``. If it is empty (i.e. Vim is compiled 
		without +multibyte) returns ``'ascii'``. When building documentation 
		outputs ``'utf-8'`` unconditionally.
	'''
	if (
		hasattr(vim, 'options')
		and hasattr(vim, 'vvars')
		and vim.vvars['version'] > 703
	):
		if sys.version_info < (3,):
			return vim.options['encoding'] or 'ascii'
		else:
			return vim.options['encoding'].decode('ascii') or 'ascii'
	elif hasattr(vim, 'eval'):
		return vim.eval('&encoding') or 'ascii'
	else:
		return 'utf-8'


def get_python_to_vim(vim):
	vim_encoding = get_vim_encoding(vim)
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


def vim_global_exists(vim, name):
	# It may crash on some old vim versions and I do not remember in which patch 
	# I fixed this crash.
	if hasattr(vim, 'vvars') and vim.vvars[str('version')] > 703:
		try:
			vim.vars[name]
		except KeyError:
			return False
		else:
			return True
	else:
		return int(vim.eval('exists("g:' + name + '")'))


def vim_getoption(vim, option):
	if hasattr(vim, 'options'):
		return vim.options[str(option)]
	else:
		return vim.eval('&g:' + option)


class FalseObject(object):
	@staticmethod
	def __nonzero__():
		return False

	__bool__ = __nonzero__


def get_buffer(vim, number):
	for buffer in vim.buffers:
		if buffer.number == number:
			return buffer
	raise KeyError(number)


class WindowVars(object):
	__slots__ = ('tabnr', 'winnr', 'vim')

	def __init__(self, window):
		self.tabnr = window.tabnr
		self.winnr = window.number
		self.vim = window.vim

	def __getitem__(self, key):
		has_key = self.vim.eval(
			'has_key(gettabwinvar({0}, {1}, ""), "{2}")'.format(self.tabnr, self.winnr, key))
		if has_key == '0':
			raise KeyError
		return self.vim.eval('gettabwinvar({0}, {1}, "{2}")'.format(self.tabnr, self.winnr, key))

	def get(self, key, default=None):
		try:
			return self[key]
		except KeyError:
			return default


class Window(FalseObject):
	__slots__ = ('tabnr', 'number', '_vars', 'vim')

	def __init__(self, vim, tabnr, number):
		self.tabnr = tabnr
		self.number = number
		self.vars = WindowVars(self)
		self.vim = vim

	@property
	def buffer(self):
		return get_buffer(self.vim, int(self.vim.eval(
			'tabpagebuflist({0})[{1}]'.format(self.tabnr, self.number - 1))))


class Tabpage(FalseObject):
	__slots__ = ('number', 'vim')

	def __init__(self, vim, number):
		self.number = number
		self.vim = vim

	def __eq__(self, tabpage):
		if not isinstance(tabpage, Tabpage):
			raise NotImplementedError
		return self.number == tabpage.number

	@property
	def window(self):
		return Window(
			self.vim, self.number,
			int(self.vim.eval('tabpagewinnr({0})'.format(self.number))))


class LazyCurrentTabpage(object):
	'''Class which may serve as a drop-in replacement of vim.Tabpage object

	Does not create vim.Tabpage object up until required.

	:param module vim:
		Vim module.
	:param bool is_old_vim:
		True if using old vim (without vim.current.tabpage).
	:param dict input:
		Input.
	'''
	def __init__(self, vim, is_old_vim, input):
		self.__vim = vim
		self.__tabpage = None
		self.__is_old_vim = is_old_vim
		assert(input is None or isinstance(input, dict))
		number = input and input.get('current_tab_number')
		self.__number = number
		if number is not None:
			self.number = number

	def __getattr__(self, attr):
		if self.__tabpage is None:
			if self.__is_old_vim:
				if self.__number is None:
					self.__number = self.__vim.eval('tabpagenr()')
				return Tabpage(self.__vim, self.__number)
			else:
				self.__tabpage = self.__vim.current.tabpage
		return getattr(self.__tabpage, attr)


class LazyWindowBuffer(object):
	'''Class which may serve as a drop-in replacement of vim.Buffer object

	Does not create vim.Buffer object up until required.

	:param LazyWindow window:
		Window this buffer is shown in.
	'''
	def __init__(self, window):
		self.__window = window
		self.__buffer = None

	def __getattr__(self, attr):
		if self.__buffer is None:
			self.__buffer = self.__window.buffer
		return getattr(self.__buffer, attr)


class LazyWindow(object):
	'''Class which may serve as a drop-in replacement of vim.Window object

	Does not create vim.Window object up until required.

	:param module vim:
		Vim module.
	:param int winnr:
		Window number.
	'''
	def __init__(self, vim, winnr):
		self.number = winnr
		self.__window = None
		self.__vim = vim
		self.buffer = LazyWindowBuffer(self)

	def __getattr__(self, attr):
		if self.__window is None:
			self.__window = self.__vim.windows[self.number - 1]
		return getattr(self.__window, attr)


def current_tabpage(vim, is_old_vim, input):
	return LazyCurrentTabpage(vim, is_old_vim, input)


class VimEnviron(object):
	def __init__(self, vim):
		self.vim = vim

	def __getitem__(self, key):
		return self.vim.eval('$' + key)

	def get(self, key, default=None):
		return self.vim.eval('$' + key) or default

	def __setitem__(self, key, value):
		return self.vim.command(
			'let ${0}="{1}"'.format(
				key,
				value.replace('"', '\\"')
				     .replace('\\', '\\\\')
				     .replace('\n', '\\n')
				     .replace('\0', '')
			)
		)


def register_powerline_vim_strtrans_error(vim):
	vim_encoding = get_vim_encoding(vim)

	def vim_u(s):
		'''Return unicode instance assuming vim encoded string.
		'''
		if type(s) is unicode:
			return s
		else:
			return unicode(s, vim_encoding)

	if hasattr(vim, 'Function'):
		_vim_strtrans = vim.Function('strtrans')
	else:
		def _vim_strtrans(s):
			assert '"' not in s
			assert '\\' not in s
			return vim.eval()

	vim_strtrans = lambda s: vim_u(_vim_strtrans(s))

	def powerline_vim_strtrans_error(e):
		if not isinstance(e, UnicodeDecodeError):
			raise NotImplementedError
		text = vim_strtrans(e.object[e.start:e.end])
		return (text, e.end)

	codecs.register_error('powerline_vim_strtrans_error', powerline_vim_strtrans_error)


did_autocmd = False
buffer_caches = []


def register_buffer_cache(vim, cachedict):
	global did_autocmd
	global buffer_caches
	from powerline.vim import get_default_pycmd, pycmd
	if not did_autocmd:
		import __main__
		__main__.powerline_on_bwipe = partial(on_bwipe, vim)
		vim.command('augroup Powerline')
		vim.command('	autocmd! BufWipeout * :{pycmd} powerline_on_bwipe()'.format(
			pycmd=(pycmd or get_default_pycmd())))
		vim.command('augroup END')
		did_autocmd = True
	buffer_caches.append(cachedict)
	return cachedict


def on_bwipe(vim):
	global buffer_caches
	bufnr = int(vim.eval('expand("<abuf>")'))
	for cachedict in buffer_caches:
		cachedict.pop(bufnr, None)


def create_ruby_dpowerline(vim):
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
