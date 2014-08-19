# vim:fileencoding=utf-8:noet

from weakref import ref

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
	def __init__(self, powerline, shell):
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
		self.paths = config.get('paths')
		super(ConfigurableIPythonPowerline, self).init()


old_prompt_manager = None


def load_ipython_extension(ip):
	global old_prompt_manager

	old_prompt_manager = ip.prompt_manager
	powerline = ConfigurableIPythonPowerline(ip)

	ip.prompt_manager = PowerlinePromptManager(
		powerline=powerline,
		shell=ip.prompt_manager.shell,
	)
	powerline.setup(ref(ip.prompt_manager))

	def shutdown_hook():
		powerline.shutdown()
		raise TryNext()

	ip.hooks.shutdown_hook.add(shutdown_hook)


def unload_ipython_extension(ip):
	ip.prompt_manager = old_prompt_manager
