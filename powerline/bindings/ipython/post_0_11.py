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
	def __init__(self, prompt_powerline, non_prompt_powerline, shell):
		self.prompt_powerline = prompt_powerline
		self.non_prompt_powerline = non_prompt_powerline
		self.powerline_segment_info = IpythonInfo(shell)
		self.shell = shell

	def render(self, name, color=True, *args, **kwargs):
		width = None if name == 'in' else self.width
		if name == 'out' or name == 'rewrite':
			powerline = self.non_prompt_powerline
		else:
			powerline = self.prompt_powerline
		res, res_nocolor = powerline.render(
			output_raw=True,
			width=width,
			matcher_info=name,
			segment_info=self.powerline_segment_info,
		)
		self.txtwidth = len(res_nocolor)
		self.width = self.txtwidth
		return res if color else res_nocolor


class ConfigurableIpythonPowerline(IpythonPowerline):
	def __init__(self, ip, is_prompt):
		config = ip.config.Powerline
		self.config_overrides = config.get('config_overrides')
		self.theme_overrides = config.get('theme_overrides', {})
		self.path = config.get('path')
		super(ConfigurableIpythonPowerline, self).__init__(is_prompt)


old_prompt_manager = None


def load_ipython_extension(ip):
	global old_prompt_manager

	old_prompt_manager = ip.prompt_manager
	prompt_powerline = ConfigurableIpythonPowerline(ip, True)
	non_prompt_powerline = ConfigurableIpythonPowerline(ip, False)

	ip.prompt_manager = PowerlinePromptManager(
		prompt_powerline=prompt_powerline,
		non_prompt_powerline=non_prompt_powerline,
		shell=ip.prompt_manager.shell
	)

	def shutdown_hook():
		prompt_powerline.shutdown()
		non_prompt_powerline.shutdown()
		raise TryNext()

	ip.hooks.shutdown_hook.add(shutdown_hook)


def unload_ipython_extension(ip):
	ip.prompt_manager = old_prompt_manager
