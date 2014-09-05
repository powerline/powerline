# vim:fileencoding=utf-8:noet
# WARNING: using unicode_literals causes errors in argparse
from __future__ import (division, absolute_import, print_function)

from powerline import Powerline
from powerline.lib import mergedicts, parsedotval


def mergeargs(argvalue):
	if not argvalue:
		return None
	r = {}
	for subval in argvalue:
		mergedicts(r, dict([subval]))
	return r


class ShellPowerline(Powerline):
	def init(self, args, **kwargs):
		self.args = args
		self.theme_option = args.theme_option
		super(ShellPowerline, self).init(args.ext[0], args.renderer_module, **kwargs)

	def load_main_config(self):
		r = super(ShellPowerline, self).load_main_config()
		if self.args.config:
			mergedicts(r, self.args.config)
		return r

	def load_theme_config(self, name):
		r = super(ShellPowerline, self).load_theme_config(name)
		if self.theme_option and name in self.theme_option:
			mergedicts(r, self.theme_option[name])
		return r

	def get_config_paths(self):
		return self.args.config_path or super(ShellPowerline, self).get_config_paths()

	def get_local_themes(self, local_themes):
		if not local_themes:
			return {}

		return dict((
			(key, {'config': self.load_theme_config(val)})
			for key, val in local_themes.items()
		))

	def do_setup(self, obj):
		obj.powerline = self


def get_argparser(parser=None, *args, **kwargs):
	if not parser:
		import argparse
		parser = argparse.ArgumentParser
	p = parser(*args, **kwargs)
	p.add_argument('ext', nargs=1, help='Extension: application for which powerline command is launched (usually `shell\' or `tmux\')')
	p.add_argument('side', nargs='?', choices=('left', 'right', 'above', 'aboveleft'), help='Side: `left\' and `right\' represent left and right side respectively, `above\' emits lines that are supposed to be printed just above the prompt and `aboveleft\' is like concatenating `above\' with `left\' with the exception that only one Python instance is used in this case.')
	p.add_argument(
		'-r', '--renderer_module', metavar='MODULE', type=str,
		help='Renderer module. Usually something like `.bash\' or `.zsh\', is supposed to be set only in shell-specific bindings file.'
	)
	p.add_argument('-w', '--width', type=int, help='Maximum prompt with. Triggers truncation of some segments')
	p.add_argument('--last_exit_code', metavar='INT', type=int, help='Last exit code')
	p.add_argument('--last_pipe_status', metavar='LIST', default='', type=lambda s: [int(status) for status in s.split()], help='Like above, but is supposed to contain space-separated array of statuses, representing exit statuses of commands in one pipe.')
	p.add_argument('--jobnum', metavar='INT', type=int, help='Number of jobs.')
	p.add_argument('-c', '--config', metavar='KEY.KEY=VALUE', action='append', help='Configuration overrides for `config.json\'. Is translated to a dictionary and merged with the dictionary obtained from actual JSON configuration: KEY.KEY=VALUE is translated to `{"KEY": {"KEY": VALUE}}\' and then merged recursively. VALUE may be any JSON value, values that are not `null\', `true\', `false\', start with digit, `{\', `[\' are treated like strings. If VALUE is omitted then corresponding key is removed.')
	p.add_argument('-t', '--theme_option', metavar='THEME.KEY.KEY=VALUE', action='append', help='Like above, but theme-specific. THEME should point to an existing and used theme to have any effect, but it is fine to use any theme here.')
	p.add_argument('-R', '--renderer_arg', metavar='KEY=VAL', action='append', help='Like above, but provides argument for renderer. Is supposed to be used only by shell bindings to provide various data like last_exit_code or last_pipe_status (they are not using --renderer_arg for historical resons: renderer_arg was added later).')
	p.add_argument('-p', '--config_path', action='append', metavar='PATH', help='Path to configuration directory. If it is present then configuration files will only be seeked in the provided path. May be provided multiple times to search in a list of directories.')
	p.add_argument('--socket', metavar='ADDRESS', type=str, help='Socket address to use in daemon clients. Is always UNIX domain socket on linux and file socket on Mac OS X. Not used here, present only for compatibility with other powerline clients. This argument must always be the first one and be in a form `--socket ADDRESS\': no `=\' or short form allowed (in other powerline clients, not here).')
	return p


def finish_args(args):
	if args.config:
		args.config = mergeargs((parsedotval(v) for v in args.config))
	if args.theme_option:
		args.theme_option = mergeargs((parsedotval(v) for v in args.theme_option))
	else:
		args.theme_option = {}
	if args.renderer_arg:
		args.renderer_arg = mergeargs((parsedotval(v) for v in args.renderer_arg))


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
