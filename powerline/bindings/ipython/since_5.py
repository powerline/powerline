# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from weakref import ref

from IPython.terminal.prompts import Prompts
from pygments.token import Token  # NOQA

from powerline.ipython import IPythonPowerline
from powerline.renderers.ipython.since_5 import PowerlinePromptStyle
from powerline.bindings.ipython.post_0_11 import PowerlineMagics, ShutdownHook


class ConfigurableIPythonPowerline(IPythonPowerline):
	def init(self, ip):
		config = ip.config.Powerline
		self.config_overrides = config.get('config_overrides')
		self.theme_overrides = config.get('theme_overrides', {})
		self.config_paths = config.get('config_paths')
		super(ConfigurableIPythonPowerline, self).init(
			renderer_module='.since_5')

	def do_setup(self, ip, prompts, shutdown_hook):
		prompts.powerline = self

		saved_msfn = ip._make_style_from_name

		if hasattr(saved_msfn, 'powerline_original'):
			saved_msfn = saved_msfn.powerline_original

		def _make_style_from_name(ip, name):
			prev_style = saved_msfn(name)
			new_style = PowerlinePromptStyle(lambda: prev_style)
			return new_style

		_make_style_from_name.powerline_original = saved_msfn

		if not isinstance(ip._style, PowerlinePromptStyle):
			prev_style = ip._style
			ip._style = PowerlinePromptStyle(lambda: prev_style)

		if not isinstance(saved_msfn, type(self.init)):
			_saved_msfn = saved_msfn
			saved_msfn = lambda: _saved_msfn(ip)

		ip._make_style_from_name = _make_style_from_name

		magics = PowerlineMagics(ip, self)
		ip.register_magics(magics)

		if shutdown_hook:
			shutdown_hook.powerline = ref(self)


class PowerlinePrompts(Prompts):
	'''Class that returns powerline prompts
	'''
	def __init__(self, shell):
		shutdown_hook = ShutdownHook(shell)
		powerline = ConfigurableIPythonPowerline(shell)
		self.shell = shell
		powerline.do_setup(shell, self, shutdown_hook)
		self.last_output_count = None
		self.last_output = {}

	for prompt in ('in', 'continuation', 'rewrite', 'out'):
		exec((
			'def {0}_prompt_tokens(self, *args, **kwargs):\n'
			'	if self.last_output_count != self.shell.execution_count:\n'
			'		self.last_output.clear()\n'
			'		self.last_output_count = self.shell.execution_count\n'
			'	if "{0}" not in self.last_output:\n'
			'		self.last_output["{0}"] = self.powerline.render('
			'			side="left",'
			'			matcher_info="{1}",'
			'			segment_info=self.shell,'
			'		) + [(Token.Generic.Prompt, " ")]\n'
			'	return self.last_output["{0}"]'
		).format(prompt, 'in2' if prompt == 'continuation' else prompt))
