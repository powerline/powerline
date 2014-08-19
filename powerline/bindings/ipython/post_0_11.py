# vim:fileencoding=utf-8:noet
from powerline.ipython import IPythonPowerline, RewriteResult

from IPython.core.prompts import PromptManager
from IPython.core.hooks import TryNext


class IPythonInfo(object):
	def __init__(self, shell):
		self._shell = shell

	@property
	def prompt_count(self):
		return self._shell.execution_count


class PowerlinePromptManager(PromptManager):
	def __init__(self, prompt_powerline, non_prompt_powerline, shell):
		prompt_powerline.setup('prompt_powerline', self)
		non_prompt_powerline.setup('non_prompt_powerline', self)
		self.powerline_segment_info = IPythonInfo(shell)
		self.shell = shell

	def render(self, name, color=True, *args, **kwargs):
		if name == 'out' or name == 'rewrite':
			powerline = self.non_prompt_powerline
		else:
			powerline = self.prompt_powerline
		res = powerline.render(
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
	def init(self, ip, is_prompt, old_widths):
		config = ip.config.Powerline
		self.config_overrides = config.get('config_overrides')
		self.theme_overrides = config.get('theme_overrides', {})
		self.paths = config.get('paths')
		super(ConfigurableIPythonPowerline, self).init(is_prompt, old_widths)


old_prompt_manager = None


def load_ipython_extension(ip):
	global old_prompt_manager

	old_prompt_manager = ip.prompt_manager
	old_widths = {}
	prompt_powerline = ConfigurableIPythonPowerline(ip, True, old_widths)
	non_prompt_powerline = ConfigurableIPythonPowerline(ip, False, old_widths)

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
