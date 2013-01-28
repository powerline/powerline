import zsh
from powerline.core import Powerline


class Args(object):
	@property
	def last_exit_code(self):
		return zsh.last_exit_code()

	@property
	def last_pipe_status(self):
		# FIXME Use arrays when they will be supported
		zsh.eval('POWERLINE_PIPE_STATUS="$pipestatus"')
		return [int(code) for code in zsh.getvalue('POWERLINE_PIPE_STATUS').split()]

def setup():
	render = Powerline(ext='shell', renderer_module='zsh_prompt', segment_info=Args()).renderer.render

	def powerline_setprompt():
		zsh.setvalue('PS1', render(width=zsh.columns(), side='left').encode('utf-8'))
		zsh.setvalue('RPS1', render(width=zsh.columns(), side='right').encode('utf-8'))

	return powerline_setprompt
