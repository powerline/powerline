from powerline.core import Powerline
from IPython.ipapi import get as get_ipython

def setup(ip=None, key='prompt_in1', varname='_powerline'):
	if not ip:
		ip = get_ipython()

	powerline = Powerline('ipython')
	ip.to_user_ns({varname : powerline})

	if key:
		setattr(ip.options, key, '${{{0}.renderer.render()}}'.format(varname))

load_ipython_extension = setup
