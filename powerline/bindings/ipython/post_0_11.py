# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from weakref import ref
from warnings import warn

try:
	from IPython.core.prompts import PromptManager
	has_prompt_manager = True
except ImportError:
	has_prompt_manager = False
from IPython.core.magic import Magics, magics_class, line_magic

from powerline.ipython import IPythonPowerline, IPythonInfo

if has_prompt_manager:
	from powerline.ipython import RewriteResult


@magics_class
class PowerlineMagics(Magics):
	def __init__(self, ip, powerline):
		super(PowerlineMagics, self).__init__(ip)
		self._powerline = powerline

	@line_magic
	def powerline(self, line):
		if line == 'reload':
			self._powerline.reload()
		else:
			raise ValueError('Expected `reload`, but got {0}'.format(line))


old_prompt_manager = None


class ShutdownHook(object):
	def __init__(self, ip):
		self.powerline = lambda: None
		ip.hooks.shutdown_hook.add(self)

	def __call__(self):
		from IPython.core.hooks import TryNext
		powerline = self.powerline()
		if powerline is not None:
			powerline.shutdown()
		raise TryNext()


if has_prompt_manager:
	class PowerlinePromptManager(PromptManager):
		def __init__(self, powerline, shell):
			self.powerline = powerline
			self.powerline_segment_info = IPythonInfo(shell)
			self.shell = shell

		def render(self, name, color=True, *args, **kwargs):
			res = self.powerline.render(
				is_prompt=name.startswith('in'),
				side='left',
				output_width=True,
				output_raw=not color,
				matcher_info=name,
				segment_info=self.powerline_segment_info,
			)
			self.txtwidth = res[-1]
			self.width = res[-1]
			ret = res[0] if color else res[1]
			if name == 'rewrite':
				return RewriteResult(ret)
			else:
				return ret

	class ConfigurableIPythonPowerline(IPythonPowerline):
		def init(self, ip):
			config = ip.config.Powerline
			self.config_overrides = config.get('config_overrides')
			self.theme_overrides = config.get('theme_overrides', {})
			self.config_paths = config.get('config_paths')
			if has_prompt_manager:
				renderer_module = '.pre_5'
			else:
				renderer_module = '.since_5'
			super(ConfigurableIPythonPowerline, self).init(
				renderer_module=renderer_module)

		def do_setup(self, ip, shutdown_hook):
			global old_prompt_manager

			if old_prompt_manager is None:
				old_prompt_manager = ip.prompt_manager
			prompt_manager = PowerlinePromptManager(
				powerline=self,
				shell=ip.prompt_manager.shell,
			)
			ip.prompt_manager = prompt_manager

			magics = PowerlineMagics(ip, self)
			shutdown_hook.powerline = ref(self)
			ip.register_magics(magics)


def load_ipython_extension(ip):
	if has_prompt_manager:
		shutdown_hook = ShutdownHook(ip)
		powerline = ConfigurableIPythonPowerline(ip)
		powerline.setup(ip, shutdown_hook)
	else:
		from powerline.bindings.ipython.since_5 import PowerlinePrompts
		ip.prompts_class = PowerlinePrompts
		ip.prompts = PowerlinePrompts(ip)
		warn(DeprecationWarning(
			'post_0_11 extension is deprecated since IPython 5, use\n'
			'  from powerline.bindings.ipython.since_5 import PowerlinePrompts\n'
			'  c.TerminalInteractiveShell.prompts_class = PowerlinePrompts\n'
		))


def unload_ipython_extension(ip):
	global old_prompt_manager
	if old_prompt_manager is not None:
		ip.prompt_manager = old_prompt_manager
	old_prompt_manager = None
