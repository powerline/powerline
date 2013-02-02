import zsh
from powerline.core import Powerline


class Args(object):
	@property
	def last_exit_code(self):
		return zsh.last_exit_code()

	@property
	def last_pipe_status(self):
		return zsh.pipestatus()

class Prompt(object):
	__slots__ = ('render', 'side')
	def __init__(self, powerline, side):
		self.render = powerline.renderer.render
		self.side = side

	def __str__(self):
		return self.render(width=zsh.columns(), side=self.side).encode('utf-8')

def setup():
	powerline = Powerline(ext='shell', renderer_module='zsh_prompt', segment_info=Args())

	zsh.set_special_string('ZPYTHON_PS1', Prompt(powerline, 'left'))
	zsh.set_special_string('ZPYTHON_RPS1', Prompt(powerline, 'right'))
	zsh.setvalue('PS1',  '${ZPYTHON_PS1}')
	zsh.setvalue('RPS1', '${ZPYTHON_RPS1}')
