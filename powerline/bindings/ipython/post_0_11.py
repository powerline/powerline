# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from weakref import ref

from IPython.core.prompts import PromptManager
from IPython.core.magic import Magics, magics_class, line_magic

from powerline.ipython import IPythonPowerline, RewriteResult


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


class IPythonInfo(object):
	def __init__(self, shell):
		self._shell = shell

	@property
	def prompt_count(self):
		return self._shell.execution_count


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


class ConfigurableIPythonPowerline(IPythonPowerline):
	def init(self, ip):
		config = ip.config.Powerline
		self.config_overrides = config.get('config_overrides')
		self.theme_overrides = config.get('theme_overrides', {})
		self.paths = config.get('paths')
		super(ConfigurableIPythonPowerline, self).init()

	def do_setup(self, ip, shutdown_hook):
		prompt_manager = PowerlinePromptManager(
			powerline=self,
			shell=ip.prompt_manager.shell,
		)
		magics = PowerlineMagics(ip, self)
		shutdown_hook.powerline = ref(self)

		ip.prompt_manager = prompt_manager
		ip.register_magics(magics)


old_prompt_manager = None


def load_ipython_extension(ip):
	global old_prompt_manager
	old_prompt_manager = ip.prompt_manager

	powerline = ConfigurableIPythonPowerline(ip)
	shutdown_hook = ShutdownHook()

	powerline.setup(ip, shutdown_hook)

	ip.hooks.shutdown_hook.add(shutdown_hook)


def unload_ipython_extension(ip):
	ip.prompt_manager = old_prompt_manager
