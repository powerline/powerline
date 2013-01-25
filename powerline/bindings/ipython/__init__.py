from powerline.core import Powerline
from collections import defaultdict

all_prompts = (('in', 1), ('in', 2), ('out', ''))

setups = {}

class Prompt(object):
	def __init__(self, powerline):
		self.powerline = powerline

	def __str__(self):
		return self.powerline.renderer.render()

def old_gen_prompt(varname):
	return '${{{0}}}'.format(varname)

def new_gen_prompt(varname):
	return '{{{0}}}'.format(varname)

def old_attr(prompt_type, level):
	return 'prompt_{0}{1}'.format(prompt_type, level)

def new_attr(prompt_type, level):
	return '{0}{1}_template'.format(prompt_type, level if level and level>1 else '')

def old_set_prompt(ip, prompt, key):
	setattr(ip.options, old_attr(*key), prompt)

def new_set_prompt(ip, prompt, key):
	setattr(ip.prompt_manager, new_attr(*key), prompt)

def old_get_prompt(ip, key):
	return getattr(ip.options, old_attr(*key))

def new_get_prompt(ip, key):
	return getattr(ip.prompt_manager, new_attr(*key))

def gen_varname(key):
	return '_powerline_{0}{1}'.format(*key)

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
	pass

def setup(ip=None, prompt_type='in', level=1):
	if not ip:
		from IPython.ipapi import get as get_ipython
		ip = get_ipython()

	if prompt_type == 'out':
		level = ''

	key = (prompt_type, level)
	varname = gen_varname(key)

	powerline = Powerline('ipython')

	ip.user_ns.update({varname : Prompt(powerline)})

	if hasattr(ip, 'options'):
		set_prompt = old_set_prompt
		get_prompt = old_get_prompt
		gen_prompt = old_gen_prompt
	else:
		set_prompt = new_set_prompt
		get_prompt = new_get_prompt
		gen_prompt = new_gen_prompt

	setups[key] = powerline

	varname = gen_varname(key)
	shift_varname = varname + '_sc'

	if key in setups:
		prompt = gen_prompt(varname)
	else:
		prompt = get_prompt(ip, key)

	if key != all_prompts[0]:
		prompt = gen_prompt(shift_varname) + prompt
		ip.user_ns.update({shift_varname : ShiftCompensator(key)})

	set_prompt(ip, prompt, key)
	if hasattr(ip, 'prompt_manager'):
		ip.prompt_manager = PowerlinePromptManager(shell=ip.prompt_manager.shell, config=ip.prompt_manager.config)
	ip.user_ns.update({'ip': ip})

load_ipython_extension = setup
