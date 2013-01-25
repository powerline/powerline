from powerline.core import Powerline
from collections import defaultdict

all_prompts = (('in', 1), ('in', 2), ('out', ''))

setups = {}

try:
	from IPython.core.prompts import PromptManager
	import re

	name_to_key = {
		'in': ('in', 1),
		'in2': ('in', 2),
		'out': ('out', ''),
	}

	re_sub = re.compile('\033\\[\\d+(;\\d+)+m').sub

	class PowerlinePromptManager(PromptManager):
		def _render(self, name, color=True, **kwargs):
			key = name_to_key.get(name)
			if key not in setups:
				return super(PowerlinePromptManager, self)._render(name, color, **kwargs)
			return setups[key].renderer.render(color=color)

except ImportError:
	from IPython.Prompts import BasePrompt
	class PowerlinePrompt(BasePrompt):
		def __init__(self, powerline, *args, **kwargs):
			self.powerline = powerline
			super(PowerlinePrompt, self).__init__(*args, **kwargs)

		def set_p_str(self):
			self.p_str = self.powerline.renderer.render()
			self.p_str_nocolor = self.powerline.renderer.render(color=False)

def setup(ip=None, prompt_type='in', level=1):
	if not ip:
		from IPython.ipapi import get as get_ipython
		ip = get_ipython()

	if prompt_type == 'out':
		level = ''

	key = (prompt_type, level)

	powerline = Powerline('ipython')

	setups[key] = powerline

	if hasattr(ip, 'prompt_manager'):
		ip.prompt_manager = PowerlinePromptManager(shell=ip.prompt_manager.shell, config=ip.prompt_manager.config)
	else:
		if prompt_type == 'in':
			attr = 'prompt{0}'.format(level)
		else:
			attr = 'prompt_out'
		def late_startup_hook():
			old_prompt = getattr(ip.IP.outputcache, attr)
			setattr(ip.IP.outputcache, attr, PowerlinePrompt(powerline,
													old_prompt.cache, old_prompt.sep, '', old_prompt.pad_left))
		ip.IP.hooks.late_startup_hook.add(late_startup_hook)

load_ipython_extension = setup
