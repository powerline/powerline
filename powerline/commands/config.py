# vim:fileencoding=utf-8:noet
from __future__ import (division, absolute_import, print_function)

import argparse

import powerline.bindings.config as config


class StrFunction(object):
	def __init__(self, function, name=None):
		self.name = name or function.__name__
		self.function = function

	def __call__(self, *args, **kwargs):
		self.function(*args, **kwargs)

	def __str__(self):
		return self.name


TMUX_ACTIONS = {
	'source': StrFunction(config.source_tmux_files, 'source'),
}


SHELL_ACTIONS = {
	'command': StrFunction(config.shell_command, 'command'),
	'uses': StrFunction(config.uses),
}


class ConfigArgParser(argparse.ArgumentParser):
	def parse_args(self, *args, **kwargs):
		ret = super(ConfigArgParser, self).parse_args(*args, **kwargs)
		if not hasattr(ret, 'function'):
			# In Python-3* `powerline-config` (without arguments) raises 
			# AttributeError. I have not found any standard way to display same 
			# error message as in Python-2*.
			self.error('too few arguments')
		return ret


def get_argparser(ArgumentParser=ConfigArgParser):
	parser = ArgumentParser(description='Script used to obtain powerline configuration.')
	subparsers = parser.add_subparsers()
	tmux_parser = subparsers.add_parser('tmux', help='Tmux-specific commands')
	tmux_parser.add_argument(
		'function',
		choices=tuple(TMUX_ACTIONS.values()),
		metavar='ACTION',
		type=(lambda v: TMUX_ACTIONS.get(v)),
		help='If action is `source\' then version-specific tmux configuration files are sourced.'
	)

	shell_parser = subparsers.add_parser('shell', help='Shell-specific commands')
	shell_parser.add_argument(
		'function',
		choices=tuple(SHELL_ACTIONS.values()),
		type=(lambda v: SHELL_ACTIONS.get(v)),
		metavar='ACTION',
		help='If action is `command\' then preferred powerline command is output, if it is `uses\' then powerline-config script will exit with 1 if specified component is disabled and 0 otherwise.',
	)
	shell_parser.add_argument(
		'component',
		nargs='?',
		choices=('tmux', 'prompt'),
		metavar='COMPONENT',
		help='Only applicable for `uses\' subcommand: makes `powerline-config\' exit with 0 if specific component is enabled and with 1 otherwise. `tmux\' component stands for tmux bindings (e.g. those that notify tmux about current directory changes), `prompt\' component stands for shell prompt.'
	)
	shell_parser.add_argument(
		'-s', '--shell',
		metavar='SHELL',
		help='Shell for which query is run',
	)
	return parser
