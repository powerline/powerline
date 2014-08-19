# vim:fileencoding=utf-8:noet

from __future__ import absolute_import

import sys
from powerline.bindings.vim import vim_get_func, vim_getvar
from powerline import Powerline
from powerline.lib import mergedicts
import vim
from itertools import count

if not hasattr(vim, 'bindeval'):
	import json


def _override_from(config, override_varname):
	try:
		overrides = vim_getvar(override_varname)
	except KeyError:
		return config
	mergedicts(config, overrides)
	return config


class VimPowerline(Powerline):
	def init(self, pyeval='PowerlinePyeval', **kwargs):
		super(VimPowerline, self).init('vim', **kwargs)
		self.last_window_id = 1
		self.pyeval = pyeval
		self.window_statusline = '%!' + pyeval + '(\'powerline.statusline({0})\')'

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
		key = self.get_matcher(key)
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
			self.renderer.add_local_theme(key, {'config': theme_config})
		except KeyError:
			return False
		else:
			return True

	def load_main_config(self):
		return _override_from(super(VimPowerline, self).load_main_config(), 'powerline_config_overrides')

	def load_theme_config(self, name):
		# Note: themes with non-[a-zA-Z0-9_] names are impossible to override 
		# (though as far as I know exists() won’t throw). Won’t fix, use proper 
		# theme names.
		return _override_from(
			super(VimPowerline, self).load_theme_config(name),
			'powerline_theme_overrides__' + name
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
			return [vim_getvar('powerline_config_path')]
		except KeyError:
			return super(VimPowerline, self).get_config_paths()

	def setup(self, pyeval=None, pycmd=None, can_replace_pyeval=True):
		super(VimPowerline, self).setup()
		import __main__
		if not pyeval:
			pyeval = 'pyeval' if sys.version_info < (3,) else 'py3eval'
			can_replace_pyeval = True
		if not pycmd:
			pycmd = get_default_pycmd()

		set_pycmd(pycmd)

		# pyeval() and vim.bindeval were both introduced in one patch
		if not hasattr(vim, 'bindeval') and can_replace_pyeval:
			vim.command(('''
				function! PowerlinePyeval(e)
					{pycmd} powerline.do_pyeval()
				endfunction
			''').format(pycmd=pycmd))
			pyeval = 'PowerlinePyeval'

		self.pyeval = pyeval
		self.window_statusline = '%!' + pyeval + '(\'powerline.statusline({0})\')'

		self.update_renderer()
		__main__.powerline = self

		if (
			bool(int(vim.eval("has('gui_running') && argc() == 0")))
			and not vim.current.buffer.name
			and len(vim.windows) == 1
		):
			# Hack to show startup screen. Problems in GUI:
			# - Defining local value of &statusline option while computing global
			#   value purges startup screen.
			# - Defining highlight group while computing statusline purges startup
			#   screen.
			# This hack removes the “while computing statusline” part: both things 
			# are defined, but they are defined right now.
			#
			# The above condition disables this hack if no GUI is running, Vim did 
			# not open any files and there is only one window. Without GUI 
			# everything works, in other cases startup screen is not shown.
			self.new_window()

		# Cannot have this in one line due to weird newline handling (in :execute 
		# context newline is considered part of the command in just the same cases 
		# when bar is considered part of the command (unless defining function 
		# inside :execute)). vim.command is :execute equivalent regarding this case.
		vim.command('augroup Powerline')
		vim.command('	autocmd! ColorScheme * :{pycmd} powerline.reset_highlight()'.format(pycmd=pycmd))
		vim.command('	autocmd! VimLeavePre * :{pycmd} powerline.shutdown()'.format(pycmd=pycmd))
		vim.command('augroup END')

	@staticmethod
	def get_segment_info():
		return {}

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

	if all((hasattr(vim.current.window, attr) for attr in ('options', 'vars', 'number'))):
		def win_idx(self, window_id):
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
				statusline = self.window_statusline.format(curwindow_id)
				if window.options['statusline'] != statusline:
					window.options['statusline'] = statusline
				if curwindow_id == window_id if window_id else window is vim.current.window:
					r = (window, curwindow_id, window.number)
			return r
	else:
		_vim_getwinvar = staticmethod(vim_get_func('getwinvar'))
		_vim_setwinvar = staticmethod(vim_get_func('setwinvar'))

		def win_idx(self, window_id):  # NOQA
			r = None
			for winnr, window in zip(count(1), vim.windows):
				curwindow_id = self._vim_getwinvar(winnr, 'powerline_window_id')
				if curwindow_id and not (r is not None and curwindow_id == window_id):
					curwindow_id = int(curwindow_id)
				else:
					curwindow_id = self.last_window_id
					self.last_window_id += 1
					self._vim_setwinvar(winnr, 'powerline_window_id', curwindow_id)
				statusline = self.window_statusline.format(curwindow_id)
				if self._vim_getwinvar(winnr, '&statusline') != statusline:
					self._vim_setwinvar(winnr, '&statusline', statusline)
				if curwindow_id == window_id if window_id else window is vim.current.window:
					r = (window, curwindow_id, winnr)
			return r

	def statusline(self, window_id):
		window, window_id, winnr = self.win_idx(window_id) or (None, None, None)
		if not window:
			return 'No window {0}'.format(window_id)
		return self.render(window, window_id, winnr)

	def tabline(self):
		return self.render()

	def new_window(self):
		window, window_id, winnr = self.win_idx(None)
		return self.render(window, window_id, winnr)

	if not hasattr(vim, 'bindeval'):
		# Method for PowerlinePyeval function. Is here to reduce the number of 
		# requirements to __main__ globals to just one powerline object 
		# (previously it required as well vim and json)
		@staticmethod
		def do_pyeval():
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
