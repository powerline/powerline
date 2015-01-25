# vim:fileencoding=utf-8:noet
# WARNING: using unicode_literals causes errors in argparse
from __future__ import (division, absolute_import, print_function)

import argparse
import sys

from itertools import chain

from powerline.lib.overrides import parsedotval, parse_override_var
from powerline.lib.dict import mergeargs
from powerline.lib.encoding import get_preferred_arguments_encoding
from powerline.lib.unicode import u


if sys.version_info < (3,):
	encoding = get_preferred_arguments_encoding()

	def arg_to_unicode(s):
		return unicode(s, encoding, 'replace') if not isinstance(s, unicode) else s  # NOQA
else:
	def arg_to_unicode(s):
		return s


def finish_args(environ, args):
	'''Do some final transformations

	Transforms ``*_override`` arguments into dictionaries, adding overrides from 
	environment variables. Transforms ``renderer_arg`` argument into dictionary 
	as well, but only if it is true.

	:param dict environ:
		Environment from which additional overrides should be taken from.
	:param args:
		Arguments object returned by 
		:py:meth:`argparse.ArgumentParser.parse_args`. Will be modified 
		in-place.

	:return: Object received as second (``args``) argument.
	'''
	args.config_override = mergeargs(chain(
		parse_override_var(environ.get('POWERLINE_CONFIG_OVERRIDES', '')),
		(parsedotval(v) for v in args.config_override or ()),
	))
	args.theme_override = mergeargs(chain(
		parse_override_var(environ.get('POWERLINE_THEME_OVERRIDES', '')),
		(parsedotval(v) for v in args.theme_override or ()),
	))
	if args.renderer_arg:
		args.renderer_arg = mergeargs((parsedotval(v) for v in args.renderer_arg), remove=True)
	args.config_path = (
		[path for path in environ.get('POWERLINE_CONFIG_PATHS', '').split(':') if path]
		+ (args.config_path or [])
	)
	return args


def int_or_sig(s):
	if s.startswith('sig'):
		return u(s)
	else:
		return int(s)


def get_argparser(ArgumentParser=argparse.ArgumentParser):
	parser = ArgumentParser(description='Powerline prompt and statusline script.')
	parser.add_argument(
		'ext', nargs=1,
		help='Extension: application for which powerline command is launched '
		     '(usually `shell\' or `tmux\').'
	)
	parser.add_argument(
		'side', nargs='?', choices=('left', 'right', 'above', 'aboveleft'),
		help='Side: `left\' and `right\' represent left and right side '
		     'respectively, `above\' emits lines that are supposed to be printed '
		     'just above the prompt and `aboveleft\' is like concatenating '
		     '`above\' with `left\' with the exception that only one Python '
		     'instance is used in this case.'
	)
	parser.add_argument(
		'-r', '--renderer-module', metavar='MODULE', type=str,
		help='Renderer module. Usually something like `.bash\' or `.zsh\' '
		     '(with leading dot) which is `powerline.renderers.{ext}{MODULE}\', '
		     'may also be full module name (must contain at least one dot or '
		     'end with a dot in case it is top-level module) or '
		     '`powerline.renderers\' submodule (in case there are no dots).'
	)
	parser.add_argument(
		'-w', '--width', type=int,
		help='Maximum prompt with. Triggers truncation of some segments.'
	)
	parser.add_argument(
		'--last-exit-code', metavar='INT', type=int_or_sig,
		help='Last exit code.'
	)
	parser.add_argument(
		'--last-pipe-status', metavar='LIST', default='',
		type=lambda s: [int_or_sig(status) for status in s.split()],
		help='Like above, but is supposed to contain space-separated array '
		     'of statuses, representing exit statuses of commands in one pipe.'
	)
	parser.add_argument(
		'--jobnum', metavar='INT', type=int,
		help='Number of jobs.'
	)
	parser.add_argument(
		'-c', '--config-override', metavar='KEY.KEY=VALUE', type=arg_to_unicode,
		action='append',
		help='Configuration overrides for `config.json\'. Is translated to a '
		     'dictionary and merged with the dictionary obtained from actual '
		     'JSON configuration: KEY.KEY=VALUE is translated to '
		     '`{"KEY": {"KEY": VALUE}}\' and then merged recursively. '
		     'VALUE may be any JSON value, values that are not '
		     '`null\', `true\', `false\', start with digit, `{\', `[\' '
		     'are treated like strings. If VALUE is omitted '
		     'then corresponding key is removed.'
	)
	parser.add_argument(
		'-t', '--theme-override', metavar='THEME.KEY.KEY=VALUE', type=arg_to_unicode,
		action='append',
		help='Like above, but theme-specific. THEME should point to '
		     'an existing and used theme to have any effect, but it is fine '
		     'to use any theme here.'
	)
	parser.add_argument(
		'-R', '--renderer-arg',
		metavar='KEY=VAL', type=arg_to_unicode, action='append',
		help='Like above, but provides argument for renderer. Is supposed '
		     'to be used only by shell bindings to provide various data like '
		     'last-exit-code or last-pipe-status (they are not using '
		     '`--renderer-arg\' for historical resons: `--renderer-arg\' '
		     'was added later).'
	)
	parser.add_argument(
		'-p', '--config-path', action='append', metavar='PATH',
		help='Path to configuration directory. If it is present then '
		     'configuration files will only be seeked in the provided path. '
		     'May be provided multiple times to search in a list of directories.'
	)
	parser.add_argument(
		'--socket', metavar='ADDRESS', type=str,
		help='Socket address to use in daemon clients. Is always UNIX domain '
		     'socket on linux and file socket on Mac OS X. Not used here, '
		     'present only for compatibility with other powerline clients. '
		     'This argument must always be the first one and be in a form '
		     '`--socket ADDRESS\': no `=\' or short form allowed '
		     '(in other powerline clients, not here).'
	)
	return parser


def write_output(args, powerline, segment_info, write):
	if args.renderer_arg:
		segment_info.update(args.renderer_arg)
	if args.side.startswith('above'):
		for line in powerline.render_above_lines(
			width=args.width,
			segment_info=segment_info,
			mode=segment_info.get('mode', None),
		):
			write(line + '\n')
		args.side = args.side[len('above'):]

	if args.side:
		rendered = powerline.render(
			width=args.width,
			side=args.side,
			segment_info=segment_info,
			mode=segment_info.get('mode', None),
		)
		write(rendered)
