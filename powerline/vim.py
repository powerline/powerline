# vim:fileencoding=utf-8:noet

from __future__ import absolute_import

from powerline.bindings.vim import vim_get_func, vim_getvar
from powerline import Powerline
from powerline.lib import mergedicts
from powerline.matcher import gen_matcher_getter
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
	def __init__(self, pyeval='PowerlinePyeval'):
		super(VimPowerline, self).__init__('vim')
		self.last_window_id = 1
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
		try:
			self.renderer.add_local_theme(key, {'config': config})
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
		return _override_from(super(VimPowerline, self).load_theme_config(name),
						'powerline_theme_overrides__' + name)

	def get_local_themes(self, local_themes):
		if not local_themes:
			return {}

		self.get_matcher = gen_matcher_getter(self.ext, self.import_paths)
		return dict(((self.get_matcher(key), {'config': self.load_theme_config(val)})
					for key, val in local_themes.items()))

	def get_config_paths(self):
		try:
			return [vim_getvar('powerline_config_path')]
		except KeyError:
			return super(VimPowerline, self).get_config_paths()

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
				except KeyError:
					curwindow_id = self.last_window_id
					self.last_window_id += 1
					window.vars['powerline_window_id'] = curwindow_id
				statusline = self.window_statusline.format(curwindow_id)
				if window.options['statusline'] != statusline:
					window.options['statusline'] = statusline
				if curwindow_id == window_id if window_id else window is vim.current.window:
					assert r is None, "Non-unique window ID"
					r = (window, curwindow_id, window.number)
			return r
	else:
		_vim_getwinvar = staticmethod(vim_get_func('getwinvar'))
		_vim_setwinvar = staticmethod(vim_get_func('setwinvar'))

		def win_idx(self, window_id):  # NOQA
			r = None
			for winnr, window in zip(count(1), vim.windows):
				curwindow_id = self._vim_getwinvar(winnr, 'powerline_window_id')
				if curwindow_id:
					curwindow_id = int(curwindow_id)
				else:
					curwindow_id = self.last_window_id
					self.last_window_id += 1
					self._vim_setwinvar(winnr, 'powerline_window_id', curwindow_id)
				statusline = self.window_statusline.format(curwindow_id)
				if self._vim_getwinvar(winnr, '&statusline') != statusline:
					self._vim_setwinvar(winnr, '&statusline', statusline)
				if curwindow_id == window_id if window_id else window is vim.current.window:
					assert r is None, "Non-unique window ID"
					r = (window, curwindow_id, winnr)
			return r

	def statusline(self, window_id):
		window, window_id, winnr = self.win_idx(window_id) or (None, None, None)
		if not window:
			return 'No window {0}'.format(window_id)
		return self.render(window, window_id, winnr)

	def new_window(self):
		window, window_id, winnr = self.win_idx(None)
		return self.render(window, window_id, winnr)

	if not hasattr(vim, 'bindeval'):
		# Method for PowerlinePyeval function. Is here to reduce the number of 
		# requirements to __main__ globals to just one powerline object 
		# (previously it required as well vim and json)
		@staticmethod
		def pyeval():
			import __main__
			vim.command('return ' + json.dumps(eval(vim.eval('a:e'),
													__main__.__dict__)))


def setup(pyeval=None, pycmd=None):
	import sys
	import __main__
	if not pyeval:
		pyeval = 'pyeval' if sys.version_info < (3,) else 'py3eval'
	if not pycmd:
		pycmd = 'python' if sys.version_info < (3,) else 'python3'

	# pyeval() and vim.bindeval were both introduced in one patch
	if not hasattr(vim, 'bindeval'):
		vim.command(('''
				function! PowerlinePyeval(e)
					{pycmd} powerline.pyeval()
				endfunction
			''').format(pycmd=pycmd))
		pyeval = 'PowerlinePyeval'

	powerline = VimPowerline(pyeval)
	__main__.powerline = powerline

	# Cannot have this in one line due to weird newline handling (in :execute 
	# context newline is considered part of the command in just the same cases 
	# when bar is considered part of the command (unless defining function 
	# inside :execute)). vim.command is :execute equivalent regarding this case.
	vim.command('augroup Powerline')
	vim.command('	autocmd! ColorScheme * :{pycmd} powerline.reset_highlight()'.format(pycmd=pycmd))
	vim.command('	autocmd! VimEnter    * :redrawstatus!')
	vim.command('	autocmd! VimLeavePre * :{pycmd} powerline.shutdown()'.format(pycmd=pycmd))
	vim.command('augroup END')

	# Is immediately changed after new_window function is run. Good for global 
	# value.
	vim.command('set statusline=%!{pyeval}(\'powerline.new_window()\')'.format(pyeval=pyeval))
