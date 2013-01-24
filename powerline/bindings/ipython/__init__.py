from powerline.core import Powerline
from collections import defaultdict

all_prompts = (('in', 1), ('in', 2), ('out', ''))

setups = set()

last_colors = defaultdict(lambda : '')

class Prompt(object):
	def __init__(self, powerline, key):
		self.powerline = powerline
		self.keys = all_prompts[all_prompts.index(key):]

	def __str__(self):
		r, last_colors_str = self.powerline.renderer.render()
		last_colors.clear()
		for key in self.keys:
			last_colors[key] = last_colors_str
		return r

class ShiftCompensator(object):
	def __init__(self, key):
		index = all_prompts.index(key)
		if index:
			self.prev_key = all_prompts[index-1]
		else:
			self.prev_key = None

	def __str__(self):
		return last_colors[self.prev_key]

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

def setup(ip=None, prompt_type='in', level=1):
	if not ip:
		from IPython.ipapi import get as get_ipython
		ip = get_ipython()

	if prompt_type == 'out':
		level = ''

	key = (prompt_type, level)
	varname = gen_varname(key)

	prompt = Prompt(Powerline('ipython'), key)

	ip.user_ns.update({varname : prompt})

	if hasattr(ip, 'options'):
		set_prompt = old_set_prompt
		get_prompt = old_get_prompt
		gen_prompt = old_gen_prompt
	else:
		set_prompt = new_set_prompt
		get_prompt = new_get_prompt
		gen_prompt = new_gen_prompt

	setups.add(key)

	for key in all_prompts:
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

load_ipython_extension = setup
