# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import atexit

from weakref import WeakValueDictionary, ref

import zsh

from powerline.shell import ShellPowerline
from powerline.lib.overrides import parsedotval, parse_override_var
from powerline.lib.unicode import unicode, u
from powerline.lib.encoding import (get_preferred_output_encoding,
                                    get_preferred_environment_encoding)
from powerline.lib.dict import mergeargs


used_powerlines = WeakValueDictionary()


def shutdown():
	for powerline in tuple(used_powerlines.values()):
		powerline.shutdown()


def get_var_config(var):
	try:
		val = zsh.getvalue(var)
		if isinstance(val, dict):
			return mergeargs([parsedotval((u(k), u(v))) for k, v in val.items()])
		elif isinstance(val, (unicode, str, bytes)):
			return mergeargs(parse_override_var(u(val)))
		else:
			return None
	except:
		return None


class Args(object):
	__slots__ = ('last_pipe_status', 'last_exit_code')
	ext = ['shell']
	renderer_module = '.zsh'

	@property
	def config_override(self):
		return get_var_config('POWERLINE_CONFIG_OVERRIDES')

	@property
	def theme_override(self):
		return get_var_config('POWERLINE_THEME_OVERRIDES')

	@property
	def config_path(self):
		try:
			ret = zsh.getvalue('POWERLINE_CONFIG_PATHS')
		except IndexError:
			return None
		else:
			if isinstance(ret, (unicode, str, bytes)):
				return [
					path
					for path in ret.split((b':' if isinstance(ret, bytes) else ':'))
					if path
				]
			else:
				return ret

	@property
	def jobnum(self):
		return zsh.getvalue('_POWERLINE_JOBNUM')


def string(s):
	if type(s) is bytes:
		return s.decode(get_preferred_environment_encoding(), 'replace')
	else:
		return str(s)


class Environment(object):
	@staticmethod
	def __getitem__(key):
		try:
			return string(zsh.getvalue(key))
		except IndexError as e:
			raise KeyError(*e.args)

	@staticmethod
	def get(key, default=None):
		try:
			return string(zsh.getvalue(key))
		except IndexError:
			return default

	@staticmethod
	def __contains__(key):
		try:
			zsh.getvalue(key)
			return True
		except IndexError:
			return False


if hasattr(getattr(zsh, 'environ', None), '__contains__'):
	environ = zsh.environ
else:
	environ = Environment()


if hasattr(zsh, 'expand') and zsh.expand('${:-}') == '':
	zsh_expand = zsh.expand
else:
	def zsh_expand(s):
		zsh.eval('local _POWERLINE_REPLY="' + s + '"')
		ret = zsh.getvalue('_POWERLINE_REPLY')
		zsh.setvalue('_POWERLINE_REPLY', None)
		return ret


class ZshPowerline(ShellPowerline):
	def init(self, **kwargs):
		super(ZshPowerline, self).init(Args(), **kwargs)

	def precmd(self):
		self.args.last_pipe_status = zsh.pipestatus()
		self.args.last_exit_code = zsh.last_exit_code()

	def do_setup(self, zsh_globals):
		set_prompt(self, 'PS1', 'left', None, above=True)
		set_prompt(self, 'RPS1', 'right', None)
		set_prompt(self, 'PS2', 'left', 'continuation')
		set_prompt(self, 'RPS2', 'right', 'continuation')
		set_prompt(self, 'PS3', 'left', 'select')
		used_powerlines[id(self)] = self
		zsh_globals['_powerline'] = self


class Prompt(object):
	__slots__ = ('powerline', 'side', 'savedpsvar', 'savedps', 'args', 'theme', 'above', '__weakref__')

	def __init__(self, powerline, side, theme, savedpsvar=None, savedps=None, above=False):
		self.powerline = powerline
		self.side = side
		self.above = above
		self.savedpsvar = savedpsvar
		self.savedps = savedps
		self.args = powerline.args
		self.theme = theme

	def __str__(self):
		parser_state = u(zsh_expand('${(%):-%_}'))
		shortened_path = u(zsh_expand('${(%):-%~}'))
		try:
			mode = u(zsh.getvalue('_POWERLINE_MODE'))
		except IndexError:
			mode = None
		try:
			default_mode = u(zsh.getvalue('_POWERLINE_DEFAULT_MODE'))
		except IndexError:
			default_mode = None
		segment_info = {
			'args': self.args,
			'environ': environ,
			'client_id': 1,
			'local_theme': self.theme,
			'parser_state': parser_state,
			'shortened_path': shortened_path,
			'mode': mode,
			'default_mode': default_mode,
		}
		try:
			zle_rprompt_indent = zsh.getvalue('ZLE_RPROMPT_INDENT')
		except IndexError:
			zle_rprompt_indent = 1
		r = ''
		if self.above:
			for line in self.powerline.render_above_lines(
				width=zsh.columns() - zle_rprompt_indent,
				segment_info=segment_info,
			):
				if line:
					r += line + '\n'
		r += self.powerline.render(
			width=zsh.columns(),
			side=self.side,
			segment_info=segment_info,
			mode=mode,
		)
		if type(r) is not str:
			if type(r) is bytes:
				return r.decode(get_preferred_output_encoding(), 'replace')
			else:
				return r.encode(get_preferred_output_encoding(), 'replace')
		return r

	def __del__(self):
		if self.savedps:
			zsh.setvalue(self.savedpsvar, self.savedps)
		self.powerline.shutdown()


def set_prompt(powerline, psvar, side, theme, above=False):
	try:
		savedps = zsh.getvalue(psvar)
	except IndexError:
		savedps = None
	zpyvar = 'ZPYTHON_POWERLINE_' + psvar
	prompt = Prompt(powerline, side, theme, psvar, savedps, above)
	zsh.setvalue(zpyvar, None)
	zsh.set_special_string(zpyvar, prompt)
	zsh.setvalue(psvar, '${' + zpyvar + '}')
	return ref(prompt)


def reload():
	for powerline in tuple(used_powerlines.values()):
		powerline.reload()


def reload_config():
	for powerline in used_powerlines.values():
		powerline.create_renderer(load_main=True, load_colors=True, load_colorscheme=True, load_theme=True)


def setup(zsh_globals):
	powerline = ZshPowerline()
	powerline.setup(zsh_globals)
	atexit.register(shutdown)
