# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import sys
import logging

from powerline import Powerline, finish_common_config
from powerline.lib.dict import mergedicts
from powerline.lib.unicode import u
from powerline.theme import Theme
from powerline.editors import EditorList
from powerline.editors.vim import VimFuncsDict, VimGlobalVar, VimVimEditor, VimPyEditor
from powerline.bindings.vim import (get_python_to_vim, register_powerline_vim_strtrans_error,
                                    LazyWindow)


class VimVarHandler(logging.Handler, object):
	'''Vim-specific handler which emits messages to Vim global variables

	:param str varname:
		Variable where log will be stored.
	:param module vim:
		Vim module.
	'''
	def __init__(self, vim, varname):
		super(VimVarHandler, self).__init__()
		utf_varname = u(varname)
		self.vim_varname = utf_varname.encode('ascii')
		vim.command('unlet! g:' + utf_varname)
		vim.command('let g:' + utf_varname + ' = []')
		self.vim = vim
		self.python_to_vim = get_python_to_vim(vim)

	def emit(self, record):
		message = u(record.message)
		if record.exc_text:
			message += '\n' + u(record.exc_text)
		self.vim.eval(b'add(g:' + self.vim_varname + b', ' + self.python_to_vim(message) + b')')


class VimPowerline(Powerline):
	prereqs = (
		'editor_overrides', 'editor_encoding',
		('use_var_handler', (VimGlobalVar('powerline_use_var_handler'),), 'bool'),
	)
	'''Data which is required first'''

	def init(self, pyeval='pyeval', **kwargs):
		import vim
		self.vim = vim
		self.is_old_vim = bool(int(self.vim.eval(
			'v:version < 800 '
			'|| exists("g:powerline_old_vim") '
			'|| has("nvim")')))
		self.vim_funcs = VimFuncsDict(vim)

		if self.is_old_vim:
			self.vim_cls = VimVimEditor
			prereqs_vim_expr, prereqs_finfunc = (
				self.vim_cls.compile_reqs_dict(self.vim_cls.reqs_to_reqs_dict(self.prereqs)))
			self.prereqs_input = prereqs_finfunc(self.vim.eval(prereqs_vim_expr))
		else:
			self.vim_cls = VimPyEditor
			reqs_dict = self.vim_cls.reqs_to_reqs_dict(self.prereqs)
			self.prereqs_input = self.vim_cls.compile_reqs_dict(reqs_dict, self.vim_funcs, self.vim)(
				self.vim.current.buffer, self.vim.current.window, self.vim.current.tabpage)

		self.encoding = self.prereqs_input['editor_encoding'] or 'ascii'

		super(VimPowerline, self).init('vim', **kwargs)
		self.pyeval = pyeval
		self.construct_window_statusline = self.create_window_statusline_constructor()
		self.renderer_options['vim'] = vim
		self.const_tabline_reqs = ['mode']
		self.renderer_options['vim_cls'] = self.vim_cls
		self.renderer_options['vim_funcs'] = self.vim_funcs

	if sys.version_info < (3,):
		def create_window_statusline_constructor(self):
			window_statusline = b'%!' + str(self.pyeval) + b'(\'powerline.statusline(window_id={0})\')'
			return window_statusline.format
	else:
		def create_window_statusline_constructor(self):
			startstr = b'%!' + self.pyeval.encode('ascii') + b'(\'powerline.statusline(window_id='
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
			self.renderer.add_local_theme(matcher, self.process_local_theme_config(theme_config))
		except KeyError:
			return False
		else:
			# Hack for local themes support: when reloading modules it is not 
			# guaranteed that .add_local_theme will be called once again, so 
			# this function arguments will be saved here for calling from 
			# .do_setup().
			self.create_old_vim_funcs()
			self.setup_kwargs.setdefault('_local_themes', []).append((key, config))
			return True

	def get_encoding(self):
		return self.encoding

	def _override_from(self, config, override_name, key=None):
		overrides = self.prereqs_input['editor_overrides'][override_name]
		if not overrides:
			return config
		if key is not None:
			try:
				overrides = overrides[key]
			except KeyError:
				return config
		mergedicts(config, overrides)
		return config

	def load_main_config(self):
		main_config = self._override_from(super(VimPowerline, self).load_main_config(), 'config_overrides')
		if self.prereqs_input['use_var_handler']:
			main_config.setdefault('common', {})
			main_config['common'] = finish_common_config(self.get_encoding(), main_config['common'])
			main_config['common']['log_file'].append(['powerline.vim.VimVarHandler', [['powerline_log_messages']]])
		return main_config

	def load_theme_config(self, name):
		return self._override_from(
			super(VimPowerline, self).load_theme_config(name),
			'theme_overrides',
			name
		)

	def process_local_theme_config(self, config, is_tabline=False):
		theme = Theme(
			theme_config=config,
			main_theme_config=self.renderer_options['theme_config'],
			**self.renderer_options['theme_kwargs']
		)
		return {
			'is_tabline': is_tabline,
			'config': config,
			'theme': theme,
			'reqs_dict': self.vim_cls.theme_to_reqs_dict(
				theme,
				self.const_tabline_reqs if is_tabline else None
			),
		}

	def get_local_themes(self, local_themes):
		if not local_themes:
			return []

		return list((
			(matcher, self.process_local_theme_config(self.load_theme_config(val), matcher is None))
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
		return self.prereqs_input['editor_overrides']['config_paths'] or super(VimPowerline, self).get_config_paths()

	def create_old_vim_funcs(self):
		if not self.is_old_vim:
			return
		inputdefs = [self.vim_cls.compile_reqs_dict(self.renderer.theme_reqs_dict)] + [
			self.vim_cls.compile_reqs_dict(theme['reqs_dict'], tabscope=(matcher is None))
			for matcher, theme in self.renderer.local_themes
		]
		self.finishers = [func for expr, func in inputdefs]
		themeexpr, themelambda = self.vim_cls.compile_themes_getter(self.renderer.local_themes)
		self.renderer.themelambda = themelambda
		command = lambda s: self.vim.command(s.format(
			pycmd=self.pycmd,
			themeexpr=themeexpr,
			inputs=self.vim_cls.toed(
				EditorList(*[expr for expr, func in inputdefs])
			),
			tablineinputnr=self.tablineinputnr,
		))
		command('''
			if !exists("g:_powerline_next_window_id")
				let g:_powerline_next_window_id = 1
			endif
		''')
		command('''
			function! _PowerlineWindowNr(winid)
				let ret = 0
				for window in range(1, winnr('$'))
					let winid = getwinvar(window, '_powerline_window_id')
					if empty(winid)
						call setwinvar(window, '_powerline_window_id', g:_powerline_next_window_id)
						call setwinvar(window, 'statusline', '%!_PowerlineStatusline('.g:_powerline_next_window_id.')')
						let g:_powerline_next_window_id += 1
					elseif getwinvar(window, '&statusline') isnot# '%!_PowerlineStatusline('.winid.')'
						call setwinvar(window, '&statusline', '%!_PowerlineStatusline('.winid.')')
					endif
					if winid == a:winid || (a:winid == 0 && window == winnr())
						let ret = window
					endif
				endfor
				return ret
			endfunction
		''')
		command('''
			function! _PowerlineNewStatusline()
				return _PowerlineStatusline(0)
			endfunction
		''')
		command('''
			let g:_powerline_inputs = {inputs}
		''')
		command('''
			function! _PowerlineStatusline(winid)
				let window = _PowerlineWindowNr(a:winid)
				let buffer = winbufnr(window)
				let tabpage = tabpagenr()
				let themenr = {themeexpr}
				let input = eval(g:_powerline_inputs[themenr])
				{pycmd} powerline.viml_return_str(powerline.statusline(input=powerline.finishers[int(vim.eval("themenr"))](powerline.vim.eval("input")), winnr=int(vim.eval("window")), themenr=int(vim.eval("themenr"))))
			endfunction
		''')
		command('''
			function! _PowerlineTabline()
				let window = winnr()
				let buffer = winbufnr(window)
				let tabpage = tabpagenr()
				let input = eval(g:_powerline_inputs[{tablineinputnr}])
				{pycmd} powerline.viml_return_str(powerline.tabline(powerline.finishers[{tablineinputnr}](input=powerline.vim.eval("input"))))
			endfunction
		''')

	def viml_return_str(self, s):
		'''Use VimL command ``:return`` to return a string

		:param bytes s:
			String to return.
		'''
		self.vim.command(b'return "' + s.replace(b'\\', b'\\\\').replace(b'"', b'\\"') + b'"')

	def do_setup(self, pyeval=None, pycmd=None, can_replace_pyeval=True, _local_themes=(), gvars=None):
		if not pyeval:
			pyeval = 'pyeval' if sys.version_info < (3,) else 'py3eval'
		if not pycmd:
			pycmd = get_default_pycmd()

		register_powerline_vim_strtrans_error(self.vim)

		self.renderer_options['is_old_vim'] = self.is_old_vim
		self.pycmd = pycmd
		set_pycmd(pycmd)

		self.update_renderer()

		try:
			self.tablineinputnr = next((
				i + 1
				for i, v in enumerate(self.renderer.local_themes)
				if v[0] is None
			))
		except StopIteration:
			self.tablineinputnr = None

		self.pyeval = pyeval
		self.construct_window_statusline = self.create_window_statusline_constructor()

		if gvars is None:
			import __main__
			__main__.powerline = self
		else:
			gvars['powerline'] = self

		try:
			if (
				bool(int(self.vim.eval('has(\'gui_running\') && argc() == 0')))
				and not self.vim.current.buffer.name
				and len(self.vim.windows) == 1
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
				if self.is_old_vim:
					self.vim.eval('_PowerlineNewStatusline()')
				else:
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
		self.vim.command('augroup Powerline')
		self.vim.command('	autocmd! ColorScheme * :{pycmd} powerline.reset_highlight()'.format(pycmd=self.pycmd))
		self.vim.command('	autocmd! VimLeavePre * :{pycmd} powerline.shutdown()'.format(pycmd=self.pycmd))
		self.vim.command('augroup END')

		# Hack for local themes support after reloading.
		for args in _local_themes:
			self.add_local_theme(*args)

		self.create_old_vim_funcs()

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

	def set_stls(self, window_id):
		assert(not self.is_old_vim)
		assert(window_id is not None)
		retwindow = None
		retwinnr = None
		win_getid = self.vim.Function('win_getid')
		for window in self.vim.windows:
			curwindow_id = win_getid(window.number)
			needed_stl = self.construct_window_statusline(curwindow_id)
			if needed_stl != window.options['statusline']:
				window.options['statusline'] = needed_stl
			if window_id == curwindow_id:
				retwindow = window
				retwinnr = window.number
		return retwindow, retwinnr

	def statusline(self, winnr=None, window_id=None, input=None, themenr=None):
		if self.is_old_vim:
			window = LazyWindow(self.vim, winnr)
		else:
			window, winnr = self.set_stls(window_id)
		return self.render(input=input, themenr=themenr, window_id=window_id, window=window, winnr=winnr)

	def tabline(self, input=None):
		return self.render(input=input, themenr=self.tablineinputnr, is_tabline=True)

	def new_window(self, input=None):
		assert(not self.is_old_vim)
		window_id = None
		winnr = None
		window = None
		win_getid = self.vim.Function('win_getid')
		for window in self.vim.windows:
			curwindow_id = win_getid(window.number)
			window.options['statusline'] = self.construct_window_statusline(curwindow_id)
			if window is self.vim.current.window:
				window_id = curwindow_id
				window = window
				winnr = window.number
		return self.render(input, window_id=window_id, window=window, winnr=winnr)

	def setup_components(self, components):
		if components is None:
			components = ('statusline', 'tabline')
		if 'statusline' in components:
			# Is immediately changed after new_window function is run. Good for 
			# global value.
			if self.is_old_vim:
				self.vim.command('set statusline=%!_PowerlineNewStatusline()')
			else:
				self.vim.command('set statusline=%!{pyeval}(\'powerline.new_window()\')'.format(
					pyeval=self.pyeval))
		if 'tabline' in components:
			if self.is_old_vim:
				self.vim.command('set tabline=%!_PowerlineTabline()')
			else:
				self.vim.command('set tabline=%!{pyeval}(\'powerline.tabline()\')'.format(
					pyeval=self.pyeval))


def get_default_pycmd():
	return 'python' if sys.version_info < (3,) else 'python3'


pycmd = None


def set_pycmd(new_pycmd):
	global pycmd
	pycmd = new_pycmd


def setup(*args, **kwargs):
	powerline = VimPowerline()
	return powerline.setup(*args, **kwargs)
