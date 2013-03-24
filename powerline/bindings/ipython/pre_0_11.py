# vim:fileencoding=utf-8:noet
from powerline.ipython import IpythonPowerline
from IPython.Prompts import BasePrompt
from IPython.ipapi import get as get_ipython
from IPython.ipapi import TryNext

import re


def string(s):
	if type(s) is not str:
		return s.encode('utf-8')
	else:
		return s


# HACK: ipython tries to only leave us with plain ASCII
class RewriteResult(object):
	def __init__(self, prompt):
		self.prompt = string(prompt)

	def __str__(self):
		return self.prompt

	def __add__(self, s):
		if type(s) is not str:
			try:
				s = s.encode('utf-8')
			except AttributeError:
				raise NotImplementedError
		return RewriteResult(self.prompt + s)


class IpythonInfo(object):
	def __init__(self, cache):
		self._cache = cache

	@property
	def prompt_count(self):
		return self._cache.prompt_count


class PowerlinePrompt(BasePrompt):
	def __init__(self, powerline, powerline_last_in, old_prompt):
		self.powerline = powerline
		self.powerline_last_in = powerline_last_in
		self.powerline_segment_info = IpythonInfo(old_prompt.cache)
		self.cache = old_prompt.cache
		if hasattr(old_prompt, 'sep'):
			self.sep = old_prompt.sep
		self.pad_left = False

	def __str__(self):
		self.set_p_str()
		return string(self.p_str)

	def set_p_str(self, width=None):
		self.p_str, self.p_str_nocolor = (
			self.powerline.render(output_raw=True,
								segment_info=self.powerline_segment_info,
								matcher_info=self.powerline_prompt_type,
								width=width)
		)

	@staticmethod
	def set_colors():
		pass


class PowerlinePrompt1(PowerlinePrompt):
	powerline_prompt_type = 'in'
	rspace = re.compile(r'(\s*)$')

	def __str__(self):
		self.cache.prompt_count += 1
		self.set_p_str()
		self.cache.last_prompt = self.p_str_nocolor.split('\n')[-1]
		return string(self.p_str)

	def set_p_str(self):
		super(PowerlinePrompt1, self).set_p_str()
		self.nrspaces = len(self.rspace.search(self.p_str_nocolor).group())
		self.prompt_text_len = len(self.p_str_nocolor) - self.nrspaces
		self.powerline_last_in['nrspaces'] = self.nrspaces
		self.powerline_last_in['prompt_text_len'] = self.prompt_text_len

	def auto_rewrite(self):
		return RewriteResult(self.powerline.render(matcher_info='rewrite', width=self.prompt_text_len, segment_info=self.powerline_segment_info)
						+ (' ' * self.nrspaces))


class PowerlinePromptOut(PowerlinePrompt):
	powerline_prompt_type = 'out'

	def set_p_str(self):
		super(PowerlinePromptOut, self).set_p_str(width=self.powerline_last_in['prompt_text_len'])
		spaces = ' ' * self.powerline_last_in['nrspaces']
		self.p_str += spaces
		self.p_str_nocolor += spaces


class PowerlinePrompt2(PowerlinePromptOut):
	powerline_prompt_type = 'in2'


class ConfigurableIpythonPowerline(IpythonPowerline):
	def __init__(self, config_overrides=None, theme_overrides={}, path=None):
		self.config_overrides = config_overrides
		self.theme_overrides = theme_overrides
		self.path = path
		super(ConfigurableIpythonPowerline, self).__init__()


def setup(**kwargs):
	ip = get_ipython()

	powerline = ConfigurableIpythonPowerline(**kwargs)

	def late_startup_hook():
		last_in = {'nrspaces': 0, 'prompt_text_len': None}
		for attr, prompt_class in (
			('prompt1', PowerlinePrompt1),
			('prompt2', PowerlinePrompt2),
			('prompt_out', PowerlinePromptOut)
		):
			old_prompt = getattr(ip.IP.outputcache, attr)
			setattr(ip.IP.outputcache, attr, prompt_class(powerline, last_in, old_prompt))
		raise TryNext()

	def shutdown_hook():
		powerline.shutdown()
		raise TryNext()

	ip.IP.hooks.late_startup_hook.add(late_startup_hook)
	ip.IP.hooks.shutdown_hook.add(shutdown_hook)
