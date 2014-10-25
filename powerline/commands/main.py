# vim:fileencoding=utf-8:noet
# WARNING: using unicode_literals causes errors in argparse
from __future__ import (division, absolute_import, print_function)

import argparse

from powerline.lib import mergedicts, parsedotval


def mergeargs(argvalue):
	if not argvalue:
		return None
	r = {}
	for subval in argvalue:
		mergedicts(r, dict([subval]))
	return r


def finish_args(args):
	if args.config:
		args.config = mergeargs((parsedotval(v) for v in args.config))
	if args.theme_option:
		args.theme_option = mergeargs((parsedotval(v) for v in args.theme_option))
	else:
		args.theme_option = {}
	if args.renderer_arg:
		args.renderer_arg = mergeargs((parsedotval(v) for v in args.renderer_arg))


def get_argparser(ArgumentParser=argparse.ArgumentParser):
	parser = ArgumentParser(description='Powerline prompt and statusline script.')
	parser.add_argument('ext', nargs=1, help='Extension: application for which powerline command is launched (usually `shell\' or `tmux\').')
	parser.add_argument('side', nargs='?', choices=('left', 'right', 'above', 'aboveleft'), help='Side: `left\' and `right\' represent left and right side respectively, `above\' emits lines that are supposed to be printed just above the prompt and `aboveleft\' is like concatenating `above\' with `left\' with the exception that only one Python instance is used in this case.')
	parser.add_argument(
		'-r', '--renderer_module', metavar='MODULE', type=str,
		help='Renderer module. Usually something like `.bash\' or `.zsh\', is supposed to be set only in shell-specific bindings file.'
	)
	parser.add_argument('-w', '--width', type=int, help='Maximum prompt with. Triggers truncation of some segments.')
	parser.add_argument('--last_exit_code', metavar='INT', type=int, help='Last exit code.')
	parser.add_argument('--last_pipe_status', metavar='LIST', default='', type=lambda s: [int(status) for status in s.split()], help='Like above, but is supposed to contain space-separated array of statuses, representing exit statuses of commands in one pipe.')
	parser.add_argument('--jobnum', metavar='INT', type=int, help='Number of jobs.')
	parser.add_argument('-c', '--config', metavar='KEY.KEY=VALUE', action='append', help='Configuration overrides for `config.json\'. Is translated to a dictionary and merged with the dictionary obtained from actual JSON configuration: KEY.KEY=VALUE is translated to `{"KEY": {"KEY": VALUE}}\' and then merged recursively. VALUE may be any JSON value, values that are not `null\', `true\', `false\', start with digit, `{\', `[\' are treated like strings. If VALUE is omitted then corresponding key is removed.')
	parser.add_argument('-t', '--theme_option', metavar='THEME.KEY.KEY=VALUE', action='append', help='Like above, but theme-specific. THEME should point to an existing and used theme to have any effect, but it is fine to use any theme here.')
	parser.add_argument('-R', '--renderer_arg', metavar='KEY=VAL', action='append', help='Like above, but provides argument for renderer. Is supposed to be used only by shell bindings to provide various data like last_exit_code or last_pipe_status (they are not using `--renderer_arg\' for historical resons: `--renderer_arg\' was added later).')
	parser.add_argument('-p', '--config_path', action='append', metavar='PATH', help='Path to configuration directory. If it is present then configuration files will only be seeked in the provided path. May be provided multiple times to search in a list of directories.')
	parser.add_argument('--socket', metavar='ADDRESS', type=str, help='Socket address to use in daemon clients. Is always UNIX domain socket on linux and file socket on Mac OS X. Not used here, present only for compatibility with other powerline clients. This argument must always be the first one and be in a form `--socket ADDRESS\': no `=\' or short form allowed (in other powerline clients, not here).')
	return parser


def write_output(args, powerline, segment_info, write, encoding):
	if args.renderer_arg:
		segment_info.update(args.renderer_arg)
	if args.side.startswith('above'):
		for line in powerline.render_above_lines(
			width=args.width,
			segment_info=segment_info,
			mode=segment_info['environ'].get('_POWERLINE_MODE'),
		):
			write(line.encode(encoding, 'replace'))
			write(b'\n')
		args.side = args.side[len('above'):]

	if args.side:
		rendered = powerline.render(
			width=args.width,
			side=args.side,
			segment_info=segment_info,
			mode=segment_info['environ'].get('_POWERLINE_MODE'),
		)
		write(rendered.encode(encoding, 'replace'))
