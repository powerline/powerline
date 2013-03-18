# vim:fileencoding=utf-8:noet
from powerline.ipython import IpythonPowerline
from IPython.Prompts import BasePrompt
from IPython.ipapi import get as get_ipython
from IPython.ipapi import TryNext


class PowerlinePrompt(BasePrompt):
	def __init__(self, powerline, *args, **kwargs):
		self.powerline = powerline
		super(PowerlinePrompt, self).__init__(*args, **kwargs)

	def set_p_str(self):
		self.p_str, self.p_str_nocolor = self.powerline.renderer.render(output_raw=True)
		self.nrspaces = len(self.rspace.search(self.p_str_nocolor).group())
		self.prompt_text_len = len(self.p_str_nocolor) - self.nrspaces - 1

	def auto_rewrite(self):
		# TODO color this
		return '%s>%s' % ('-' * self.prompt_text_len, ' ' * self.nrspaces)


class ConfigurableIpythonPowerline(IpythonPowerline):
	def __init__(self, config_overrides=None, theme_overrides={}, path=None):
		self.config_overrides = config_overrides
		self.theme_overrides = theme_overrides
		self.path = path
		super(ConfigurableIpythonPowerline, self).__init__()


def setup(prompt='1', **kwargs):
	ip = get_ipython()

	powerline = ConfigurableIpythonPowerline(**kwargs)

	attr = 'prompt' + prompt

	def late_startup_hook():
		old_prompt = getattr(ip.IP.outputcache, attr)
		setattr(ip.IP.outputcache, attr, PowerlinePrompt(powerline,
			old_prompt.cache, old_prompt.sep, '', old_prompt.pad_left))
		raise TryNext()

	def shutdown_hook():
		powerline.renderer.shutdown()
		raise TryNext()

	ip.IP.hooks.late_startup_hook.add(late_startup_hook)
	ip.IP.hooks.shutdown_hook.add(shutdown_hook)
