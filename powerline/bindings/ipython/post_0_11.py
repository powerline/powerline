from powerline.ipython import IpythonPowerline

from IPython.core.prompts import PromptManager


class PowerlinePromptManager(PromptManager):
	powerline = None

	def __init__(self, powerline, **kwargs):
		self.powerline = powerline
		super(PowerlinePromptManager, self).__init__(**kwargs)

	def render(self, name, color=True, *args, **kwargs):
		if name != 'in':
			return super(PowerlinePromptManager, self).render(name, color, *args, **kwargs)
		res, res_nocolor = self.powerline.renderer.render(output_raw=True)
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


def load_ipython_extension(ip):
	global old_prompt_manager

	old_prompt_manager = ip.prompt_manager
	powerline = ConfigurableIpythonPowerline(ip)

	ip.prompt_manager = PowerlinePromptManager(powerline=powerline,
		shell=ip.prompt_manager.shell, config=ip.prompt_manager.config)

def unload_ipython_extension(ip):
	ip.prompt_manager = old_prompt_manager
