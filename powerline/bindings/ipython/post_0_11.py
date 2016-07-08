# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from weakref import ref

try:
	from IPython.core.prompts import PromptManager
	has_prompt_manager = True
except ImportError:
	from IPython.terminal.interactiveshell import TerminalInteractiveShell
	has_prompt_manager = False
from IPython.core.magic import Magics, magics_class, line_magic

from powerline.ipython import IPythonPowerline, IPythonInfo

if has_prompt_manager:
	from powerline.ipython import RewriteResult
else:
	from powerline.renderers.ipython.since_5 import PowerlinePromptStyle, PowerlinePrompts


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


class ShutdownHook(object):
	powerline = lambda: None

	def __call__(self):
		from IPython.core.hooks import TryNext
		powerline = self.powerline()
		if powerline is not None:
			powerline.shutdown()
		raise TryNext()


old_prompt_manager = None
old_style = None
old_prompts = None


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
		global old_style
		global old_prompts

		if has_prompt_manager:
			if old_prompt_manager is None:
				old_prompt_manager = ip.prompt_manager
			prompt_manager = PowerlinePromptManager(
				powerline=self,
				shell=ip.prompt_manager.shell,
			)
			ip.prompt_manager = prompt_manager
		else:
			if ip.pt_cli is not None:
				if old_style is None:
					old_style = ip.pt_cli.application.style
				prev_style = ip.pt_cli.application.style
				while isinstance(prev_style, PowerlinePromptStyle):
					prev_style = prev_style.get_style()
				new_style = PowerlinePromptStyle(lambda: prev_style)
				ip.pt_cli.application.style = new_style
				ip.pt_cli.renderer.style = new_style

			if old_prompts is None:
				old_prompts = ip.prompts
			ip.prompts = PowerlinePrompts(ip.prompts, self)

		magics = PowerlineMagics(ip, self)
		shutdown_hook.powerline = ref(self)
		ip.register_magics(magics)


def load_ipython_extension(ip):
	powerline = ConfigurableIPythonPowerline(ip)
	shutdown_hook = ShutdownHook()

	powerline.setup(ip, shutdown_hook)

	ip.hooks.shutdown_hook.add(shutdown_hook)


def unload_ipython_extension(ip):
	if old_prompt_manager is not None:
		ip.prompt_manager = old_prompt_manager
	if old_style is not None:
		ip.pt_cli.application.style = old_style
		ip.pt_cli.renderer.style = old_style
		ip.prompts = old_prompts
	old_prompt_manager = None
	old_style = None
