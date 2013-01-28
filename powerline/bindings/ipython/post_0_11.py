from powerline.core import Powerline

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


def load_ipython_extension(ip):
	powerline = Powerline('ipython')

	ip.prompt_manager = PowerlinePromptManager(powerline=powerline,
		shell=ip.prompt_manager.shell, config=ip.prompt_manager.config)
