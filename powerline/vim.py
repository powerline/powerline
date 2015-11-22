# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import sys
import json
import logging

from itertools import count

try:
	import vim
except ImportError:
	vim = object()

from powerline.bindings.vim import vim_get_func, vim_getvar, get_vim_encoding, python_to_vim
from powerline import Powerline, FailedUnicode, finish_common_config
from powerline.lib.dict import mergedicts
from powerline.lib.unicode import u


def _override_from(config, override_varname, key=None):
	try:
		overrides = vim_getvar(override_varname)
	except KeyError:
		return config
	if key is not None:
		try:
			overrides = overrides[key]
		except KeyError:
			return config
	mergedicts(config, overrides)
	return config


class VimVarHandler(logging.Handler, object):
	'''Vim-specific handler which emits messages to Vim global variables

	:param str varname:
		Variable where
	'''
	def __init__(self, varname):
		super(VimVarHandler, self).__init__()
		utf_varname = u(varname)
		self.vim_varname = utf_varname.encode('ascii')
		vim.command('unlet! g:' + utf_varname)
		vim.command('let g:' + utf_varname + ' = []')

	def emit(self, record):
		message = u(record.message)
		if record.exc_text:
			message += '\n' + u(record.exc_text)
		vim.eval(b'add(g:' + self.vim_varname + b', ' + python_to_vim(message) + b')')


class VimPowerline(Powerline):
	def init(self, pyeval='PowerlinePyeval', **kwargs):
		super(VimPowerline, self).init('vim', **kwargs)
		self.last_window_id = 1
		self.pyeval = pyeval
		self.construct_window_statusline = self.create_window_statusline_constructor()
		if all((hasattr(vim.current.window, attr) for attr in ('options', 'vars', 'number'))):
			self.win_idx = self.new_win_idx
		else:
			self.win_idx = self.old_win_idx
			self._vim_getwinvar = vim_get_func('getwinvar', 'bytes')
			self._vim_setwinvar = vim_get_func('setwinvar')

	if sys.version_info < (3,):
		def create_window_statusline_constructor(self):
			window_statusline = b'%!' + str(self.pyeval) + b'(\'powerline.statusline({0})\')'
			return window_statusline.format
	else:
		def create_window_statusline_constructor(self):
			startstr = b'%!' + self.pyeval.encode('ascii') + b'(\'powerline.statusline('
			endstr = b')\')'
			return lambda idx: (
				startstr + str(idx).encode('ascii') + endstr
			)

	create_window_statusline_constructor.__doc__ = (
		'''Create function which returns &l:stl value being given window index

		Created function must return :py:class:`bytes` instance because this is 
		what ``window.options['statusline']`` returns (``window`` is 
		:py:class:`vim.Window` instance).

		:return:
			Function with type ``int → bytes``.
		'''
	)

	default_log_stream = sys.stdout

	def add_local_theme(self, key, config):
		'''Add local themes at runtime (during vim session).

		:param str key:
			Matcher name (in format ``{matcher_module}.{module_attribute}`` or 
			``{module_attribute}`` if ``{matcher_module}`` is 
			``powerline.matchers.vim``). Function pointed by 
			``{module_attribute}`` should be hashable and accept a dictionary 
			with information about current buffer and return boolean value 
			indicating whether current window matched conditions. See also 
			:ref:`local_themes key description <config-ext-local_themes>`.

		:param dict config:
			:ref:`Theme <config-themes>` dictionary.

		:return:
			``True`` if theme was added successfully and ``False`` if theme with 
			the same matcher already exists.
		'''
		self.update_renderer()
		matcher = self.get_matcher(key)
		theme_config = {}
		for cfg_path in self.theme_levels:
			try:
				lvl_config = self.load_config(cfg_path, 'theme')
			except IOError:
				pass
			else:
				mergedicts(theme_config, lvl_config)
		mergedicts(theme_config, config)
		try:
			self.renderer.add_local_theme(matcher, {'config': theme_config})
		except KeyError:
			return False
		else:
			# Hack for local themes support: when reloading modules it is not 
			# guaranteed that .add_local_theme will be called once again, so 
			# this function arguments will be saved here for calling from 
			# .do_setup().
			self.setup_kwargs.setdefault('_local_themes', []).append((key, config))
			return True

	get_encoding = staticmethod(get_vim_encoding)

	def load_main_config(self):
		main_config = _override_from(super(VimPowerline, self).load_main_config(), 'powerline_config_overrides')
		try:
			use_var_handler = bool(int(vim_getvar('powerline_use_var_handler')))
		except KeyError:
			use_var_handler = False
		if use_var_handler:
			main_config.setdefault('common', {})
			main_config['common'] = finish_common_config(self.get_encoding(), main_config['common'])
			main_config['common']['log_file'].append(['powerline.vim.VimVarHandler', [['powerline_log_messages']]])
		return main_config

	def load_theme_config(self, name):
		return _override_from(
			super(VimPowerline, self).load_theme_config(name),
			'powerline_theme_overrides',
			name
		)

	def get_local_themes(self, local_themes):
		if not local_themes:
			return {}

		return dict((
			(matcher, {'config': self.load_theme_config(val)})
			for matcher, key, val in (
				(
					(None if k == '__tabline__' else self.get_matcher(k)),
					k,
					v
				)
				for k, v in local_themes.items()
			) if (
				matcher or
				key == '__tabline__'
			)
		))

	def get_matcher(self, match_name):
		match_module, separator, match_function = match_name.rpartition('.')
		if not separator:
			match_module = 'powerline.matchers.{0}'.format(self.ext)
			match_function = match_name
		return self.get_module_attr(match_module, match_function, prefix='matcher_generator')

	def get_config_paths(self):
		try:
			return vim_getvar('powerline_config_paths')
		except KeyError:
			return super(VimPowerline, self).get_config_paths()

	def do_setup(self, pyeval=None, pycmd=None, can_replace_pyeval=True, _local_themes=()):
		import __main__
		if not pyeval:
			pyeval = 'pyeval' if sys.version_info < (3,) else 'py3eval'
			can_replace_pyeval = True
		if not pycmd:
			pycmd = get_default_pycmd()

		set_pycmd(pycmd)

		# pyeval() and vim.bindeval were both introduced in one patch
		if (not hasattr(vim, 'bindeval') and can_replace_pyeval) or pyeval == 'PowerlinePyeval':
			vim.command(('''
				function! PowerlinePyeval(e)
					{pycmd} powerline.do_pyeval()
				endfunction
			''').format(pycmd=pycmd))
			pyeval = 'PowerlinePyeval'

		self.pyeval = pyeval
		self.construct_window_statusline = self.create_window_statusline_constructor()

		self.update_renderer()
		__main__.powerline = self

		try:
			if (
				bool(int(vim.eval('has(\'gui_running\') && argc() == 0')))
				and not vim.current.buffer.name
				and len(vim.windows) == 1
			):
				# Hack to show startup screen. Problems in GUI:
				# - Defining local value of &statusline option while computing
				#   global value purges startup screen.
				# - Defining highlight group while computing statusline purges
				#   startup screen.
				# This hack removes the “while computing statusline” part: both 
				# things are defined, but they are defined right now.
				#
				# The above condition disables this hack if no GUI is running, 
				# Vim did not open any files and there is only one window. 
				# Without GUI everything works, in other cases startup screen is 
				# not shown.
				self.new_window()
		except UnicodeDecodeError:
			# vim.current.buffer.name may raise UnicodeDecodeError when using 
			# Python-3*. Fortunately, this means that current buffer is not 
			# empty buffer, so the above condition should be False.
			pass

		# Cannot have this in one line due to weird newline handling (in :execute 
		# context newline is considered part of the command in just the same cases 
		# when bar is considered part of the command (unless defining function 
		# inside :execute)). vim.command is :execute equivalent regarding this case.
		vim.command('augroup Powerline')
		vim.command('	autocmd! ColorScheme * :{pycmd} powerline.reset_highlight()'.format(pycmd=pycmd))
		vim.command('	autocmd! VimLeavePre * :{pycmd} powerline.shutdown()'.format(pycmd=pycmd))
		vim.command('augroup END')

		# Hack for local themes support after reloading.
		for args in _local_themes:
			self.add_local_theme(*args)

	def reset_highlight(self):
		try:
			self.renderer.reset_highlight()
		except AttributeError:
			# Renderer object appears only after first `.render()` call. Thus if 
			# ColorScheme event happens before statusline is drawn for the first 
			# time AttributeError will be thrown for the self.renderer. It is 
			# fine to ignore it: no renderer == no colors to reset == no need to 
			# do anything.
			pass

	def new_win_idx(self, window_id):
		r = None
		for window in vim.windows:
			try:
				curwindow_id = window.vars['powerline_window_id']
				if r is not None and curwindow_id == window_id:
					raise KeyError
			except KeyError:
				curwindow_id = self.last_window_id
				self.last_window_id += 1
				window.vars['powerline_window_id'] = curwindow_id
			statusline = self.construct_window_statusline(curwindow_id)
			if window.options['statusline'] != statusline:
				window.options['statusline'] = statusline
			if curwindow_id == window_id if window_id else window is vim.current.window:
				r = (window, curwindow_id, window.number)
		return r

	def old_win_idx(self, window_id):
		r = None
		for winnr, window in zip(count(1), vim.windows):
			curwindow_id = self._vim_getwinvar(winnr, 'powerline_window_id')
			if curwindow_id and not (r is not None and curwindow_id == window_id):
				curwindow_id = int(curwindow_id)
			else:
				curwindow_id = self.last_window_id
				self.last_window_id += 1
				self._vim_setwinvar(winnr, 'powerline_window_id', curwindow_id)
			statusline = self.construct_window_statusline(curwindow_id)
			if self._vim_getwinvar(winnr, '&statusline') != statusline:
				self._vim_setwinvar(winnr, '&statusline', statusline)
			if curwindow_id == window_id if window_id else window is vim.current.window:
				r = (window, curwindow_id, winnr)
		return r

	def statusline(self, window_id):
		window, window_id, winnr = self.win_idx(window_id) or (None, None, None)
		if not window:
			return FailedUnicode('No window {0}'.format(window_id))
		return self.render(window, window_id, winnr)

	def tabline(self):
		return self.render(*self.win_idx(None), is_tabline=True)

	def new_window(self):
		return self.render(*self.win_idx(None))

	@staticmethod
	def do_pyeval():
		'''Evaluate python string passed to PowerlinePyeval

		Is here to reduce the number of requirements to __main__ globals to just 
		one powerline object (previously it required as well vim and json).
		'''
		import __main__
		vim.command('return ' + json.dumps(eval(vim.eval('a:e'), __main__.__dict__)))

	def setup_components(self, components):
		if components is None:
			components = ('statusline', 'tabline')
		if 'statusline' in components:
			# Is immediately changed after new_window function is run. Good for 
			# global value.
			vim.command('set statusline=%!{pyeval}(\'powerline.new_window()\')'.format(
				pyeval=self.pyeval))
		if 'tabline' in components:
			vim.command('set tabline=%!{pyeval}(\'powerline.tabline()\')'.format(
				pyeval=self.pyeval))


pycmd = None


def set_pycmd(new_pycmd):
	global pycmd
	pycmd = new_pycmd


def get_default_pycmd():
	return 'python' if sys.version_info < (3,) else 'python3'


def setup(*args, **kwargs):
	powerline = VimPowerline()
	return powerline.setup(*args, **kwargs)
