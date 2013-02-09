from powerline.core import Powerline
from IPython.Prompts import BasePrompt
from IPython.ipapi import get as get_ipython


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
		return '%s>%s' % ('-'*self.prompt_text_len, ' '*self.nrspaces)


def setup(prompt='1'):
	ip = get_ipython()

	powerline = Powerline('ipython')

	attr = 'prompt' + prompt

	def late_startup_hook():
		old_prompt = getattr(ip.IP.outputcache, attr)
		setattr(ip.IP.outputcache, attr, PowerlinePrompt(powerline,
			old_prompt.cache, old_prompt.sep, '', old_prompt.pad_left))
	ip.IP.hooks.late_startup_hook.add(late_startup_hook)
