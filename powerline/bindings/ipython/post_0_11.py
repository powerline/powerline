# vim:fileencoding=utf-8:noet
from powerline.ipython import IpythonPowerline

from IPython.core.prompts import PromptManager
from IPython.core.hooks import TryNext


class IpythonInfo(object):
	def __init__(self, shell):
		self._shell = shell

	@property
	def prompt_count(self):
		return self._shell.execution_count


class PowerlinePromptManager(PromptManager):
	powerline = None

	def __init__(self, powerline, shell):
		self.powerline = powerline
		self.powerline_segment_info = IpythonInfo(shell)
		self.shell = shell

	def render(self, name, color=True, *args, **kwargs):
		width = None if name == 'in' else self.width
		res, res_nocolor = self.powerline.render(output_raw=True, width=width, matcher_info=name, segment_info=self.powerline_segment_info)
		self.txtwidth = len(res_nocolor)
		self.width = self.txtwidth
		return res if color else res_nocolor


class ConfigurableIpythonPowerline(IpythonPowerline):
	def __init__(self, ip):
		config = ip.config.Powerline
		self.config_overrides = config.get('config_overrides')
		self.theme_overrides = config.get('theme_overrides', {})
		self.path = config.get('path')
		super(ConfigurableIpythonPowerline, self).__init__()


old_prompt_manager = None


def load_ipython_extension(ip):
	global old_prompt_manager

	old_prompt_manager = ip.prompt_manager
	powerline = ConfigurableIpythonPowerline(ip)

	ip.prompt_manager = PowerlinePromptManager(powerline=powerline, shell=ip.prompt_manager.shell)

	def shutdown_hook():
		powerline.shutdown()
		raise TryNext()

	ip.hooks.shutdown_hook.add(shutdown_hook)


def unload_ipython_extension(ip):
	ip.prompt_manager = old_prompt_manager
