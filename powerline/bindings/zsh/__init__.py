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
	__slots__ = ('render', 'side', 'savedpsvar', 'savedps')

	def __init__(self, powerline, side, savedpsvar=None, savedps=None):
		self.render = powerline.renderer.render
		self.side = side
		self.savedpsvar = savedpsvar
		self.savedps = savedps

	def __str__(self):
		return self.render(width=zsh.columns(), side=self.side).encode('utf-8')

	def __del__(self):
		if self.savedps:
			zsh.setvalue(self.savedpsvar, self.savedps)


def set_prompt(powerline, psvar, side):
	savedps = zsh.getvalue(psvar)
	zpyvar = 'ZPYTHON_POWERLINE_' + psvar
	prompt = Prompt(powerline, side, psvar, savedps)
	zsh.set_special_string(zpyvar, prompt)
	zsh.setvalue(psvar, '${' + zpyvar + '}')


def setup():
	powerline = Powerline(ext='shell', renderer_module='zsh_prompt', segment_info=Args())
	set_prompt(powerline, 'PS1', 'left')
	set_prompt(powerline, 'RPS1', 'right')
