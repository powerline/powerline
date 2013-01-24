from powerline.core import Powerline

def setup(ip=None, prompt_type='in', level=1, varname='_powerline'):
	if not ip:
		from IPython.ipapi import get as get_ipython
		ip = get_ipython()

	powerline = Powerline('ipython')
	try:
		ip.to_user_ns({varname : powerline})
	except AttributeError:
		ip.ns_table.update({varname : powerline})

	if hasattr(ip, 'options'):
		attr = 'prompt_{0}{1}'.format(prompt_type, level)
		prompt = '${{{0}.renderer.render()}}'.format(varname)
		setattr(ip.options, attr, prompt)
	else:
		attr = '{0}{1}_template'.format(prompt_type, level if level>1 else '')
		setattr(ip.prompt_manager, attr, '{{{0}}}'.format(varname))
		def update_prompt(ip):
			ip.user_ns.update({varname : powerline.renderer.render()})
		ip.set_hook('pre_prompt_hook', update_prompt)

load_ipython_extension = setup
