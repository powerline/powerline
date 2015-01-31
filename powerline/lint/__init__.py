# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os
import logging

from collections import defaultdict
from itertools import chain
from functools import partial

from powerline import generate_config_finder, get_config_paths, load_config
from powerline.segments.vim import vim_modes
from powerline.lib.dict import mergedicts_copy
from powerline.lib.config import ConfigLoader
from powerline.lib.unicode import unicode
from powerline.lib.path import join
from powerline.lint.markedjson import load
from powerline.lint.markedjson.error import echoerr, EchoErr, MarkedError
from powerline.lint.checks import (check_matcher_func, check_ext, check_config, check_top_theme,
                                   check_color, check_translated_group_name, check_group,
                                   check_segment_module, check_exinclude_function, type_keys,
                                   check_segment_function, check_args, get_one_segment_function,
                                   check_highlight_groups, check_highlight_group, check_full_segment_data,
                                   get_all_possible_functions, check_segment_data_key, register_common_name,
                                   highlight_group_spec)
from powerline.lint.spec import Spec
from powerline.lint.context import Context


def open_file(path):
	return open(path, 'rb')


def generate_json_config_loader(lhadproblem):
	def load_json_config(config_file_path, load=load, open_file=open_file):
		with open_file(config_file_path) as config_file_fp:
			r, hadproblem = load(config_file_fp)
			if hadproblem:
				lhadproblem[0] = True
			return r
	return load_json_config


function_name_re = '^(\w+\.)*[a-zA-Z_]\w*$'


divider_spec = Spec().printable().len(
	'le', 3, (lambda value: 'Divider {0!r} is too large!'.format(value))).copy
ext_theme_spec = Spec().type(unicode).func(lambda *args: check_config('themes', *args)).copy
top_theme_spec = Spec().type(unicode).func(check_top_theme).copy
ext_spec = Spec(
	colorscheme=Spec().type(unicode).func(
		(lambda *args: check_config('colorschemes', *args))
	),
	theme=ext_theme_spec(),
	top_theme=top_theme_spec().optional(),
).copy
gen_components_spec = (lambda *components: Spec().list(Spec().type(unicode).oneof(set(components))))
main_spec = (Spec(
	common=Spec(
		default_top_theme=top_theme_spec().optional(),
		term_truecolor=Spec().type(bool).optional(),
		term_escape_style=Spec().type(unicode).oneof(set(('auto', 'xterm', 'fbterm'))).optional(),
		# Python is capable of loading from zip archives. Thus checking path 
		# only for existence of the path, not for it being a directory
		paths=Spec().list(
			(lambda value, *args: (True, True, not os.path.exists(os.path.expanduser(value.value)))),
			(lambda value: 'path does not exist: {0}'.format(value))
		).optional(),
		log_file=Spec().type(unicode).func(
			(
				lambda value, *args: (
					True,
					True,
					not os.path.isdir(os.path.dirname(os.path.expanduser(value)))
				)
			),
			(lambda value: 'directory does not exist: {0}'.format(os.path.dirname(value)))
		).optional(),
		log_level=Spec().re('^[A-Z]+$').func(
			(lambda value, *args: (True, True, not hasattr(logging, value))),
			(lambda value: 'unknown debugging level {0}'.format(value))
		).optional(),
		log_format=Spec().type(unicode).optional(),
		interval=Spec().either(Spec().cmp('gt', 0.0), Spec().type(type(None))).optional(),
		reload_config=Spec().type(bool).optional(),
		watcher=Spec().type(unicode).oneof(set(('auto', 'inotify', 'stat'))).optional(),
	).context_message('Error while loading common configuration (key {key})'),
	ext=Spec(
		vim=ext_spec().update(
			components=gen_components_spec('statusline', 'tabline').optional(),
			local_themes=Spec(
				__tabline__=ext_theme_spec(),
			).unknown_spec(
				Spec().re(function_name_re).func(partial(check_matcher_func, 'vim')),
				ext_theme_spec()
			),
		).optional(),
		ipython=ext_spec().update(
			local_themes=Spec(
				in2=ext_theme_spec(),
				out=ext_theme_spec(),
				rewrite=ext_theme_spec(),
			),
		).optional(),
		shell=ext_spec().update(
			components=gen_components_spec('tmux', 'prompt').optional(),
			local_themes=Spec(
				continuation=ext_theme_spec(),
				select=ext_theme_spec(),
			),
		).optional(),
	).unknown_spec(
		check_ext,
		ext_spec(),
	).context_message('Error while loading extensions configuration (key {key})'),
).context_message('Error while loading main configuration'))

term_color_spec = Spec().unsigned().cmp('le', 255).copy
true_color_spec = Spec().re(
	'^[0-9a-fA-F]{6}$',
	(lambda value: '"{0}" is not a six-digit hexadecimal unsigned integer written as a string'.format(value))
).copy
colors_spec = (Spec(
	colors=Spec().unknown_spec(
		Spec().ident(),
		Spec().either(
			Spec().tuple(term_color_spec(), true_color_spec()),
			term_color_spec()
		)
	).context_message('Error while checking colors (key {key})'),
	gradients=Spec().unknown_spec(
		Spec().ident(),
		Spec().tuple(
			Spec().len('gt', 1).list(term_color_spec()),
			Spec().len('gt', 1).list(true_color_spec()).optional(),
		)
	).context_message('Error while checking gradients (key {key})'),
).context_message('Error while loading colors configuration'))


color_spec = Spec().type(unicode).func(check_color).copy
name_spec = Spec().type(unicode).len('gt', 0).optional().copy
group_name_spec = Spec().ident().copy
group_spec = Spec().either(Spec(
	fg=color_spec(),
	bg=color_spec(),
	attrs=Spec().list(Spec().type(unicode).oneof(set(('bold', 'italic', 'underline')))),
), group_name_spec().func(check_group)).copy
groups_spec = Spec().unknown_spec(
	group_name_spec(),
	group_spec(),
).context_message('Error while loading groups (key {key})').copy
colorscheme_spec = (Spec(
	name=name_spec(),
	groups=groups_spec(),
).context_message('Error while loading coloscheme'))
mode_translations_value_spec = Spec(
	colors=Spec().unknown_spec(
		color_spec(),
		color_spec(),
	).optional(),
	groups=Spec().unknown_spec(
		group_name_spec().func(check_translated_group_name),
		group_spec(),
	).optional(),
).copy
top_colorscheme_spec = (Spec(
	name=name_spec(),
	groups=groups_spec(),
	mode_translations=Spec().unknown_spec(
		Spec().type(unicode),
		mode_translations_value_spec(),
	).optional().context_message('Error while loading mode translations (key {key})').optional(),
).context_message('Error while loading top-level coloscheme'))
vim_mode_spec = Spec().oneof(set(list(vim_modes) + ['nc', 'tab_nc', 'buf_nc'])).copy
vim_colorscheme_spec = (Spec(
	name=name_spec(),
	groups=groups_spec(),
	mode_translations=Spec().unknown_spec(
		vim_mode_spec(),
		mode_translations_value_spec(),
	).optional().context_message('Error while loading mode translations (key {key})'),
).context_message('Error while loading vim colorscheme'))
shell_mode_spec = Spec().re('^(?:[\w\-]+|\.safe)$').copy
shell_colorscheme_spec = (Spec(
	name=name_spec(),
	groups=groups_spec(),
	mode_translations=Spec().unknown_spec(
		shell_mode_spec(),
		mode_translations_value_spec(),
	).optional().context_message('Error while loading mode translations (key {key})'),
).context_message('Error while loading shell colorscheme'))


args_spec = Spec(
	pl=Spec().error('pl object must be set by powerline').optional(),
	segment_info=Spec().error('Segment info dictionary must be set by powerline').optional(),
).unknown_spec(Spec(), Spec()).optional().copy
segment_module_spec = Spec().type(unicode).func(check_segment_module).optional().copy
sub_segments_spec = Spec()
exinclude_spec = Spec().re(function_name_re).func(check_exinclude_function).copy
segment_spec = Spec(
	type=Spec().oneof(type_keys).optional(),
	name=Spec().re('^[a-zA-Z_]\w*$').optional(),
	function=Spec().re(function_name_re).func(check_segment_function).optional(),
	exclude_modes=Spec().list(vim_mode_spec()).optional(),
	include_modes=Spec().list(vim_mode_spec()).optional(),
	exclude_function=exinclude_spec().optional(),
	include_function=exinclude_spec().optional(),
	draw_hard_divider=Spec().type(bool).optional(),
	draw_soft_divider=Spec().type(bool).optional(),
	draw_inner_divider=Spec().type(bool).optional(),
	display=Spec().type(bool).optional(),
	module=segment_module_spec(),
	priority=Spec().type(int, float, type(None)).optional(),
	after=Spec().printable().optional(),
	before=Spec().printable().optional(),
	width=Spec().either(Spec().unsigned(), Spec().cmp('eq', 'auto')).optional(),
	align=Spec().oneof(set('lr')).optional(),
	args=args_spec().func(lambda *args, **kwargs: check_args(get_one_segment_function, *args, **kwargs)),
	contents=Spec().printable().optional(),
	highlight_groups=Spec().list(
		highlight_group_spec().re(
			'^(?:(?!:divider$).)+$',
			(lambda value: 'it is recommended that only divider highlight group names end with ":divider"')
		)
	).func(check_highlight_groups).optional(),
	divider_highlight_group=highlight_group_spec().func(check_highlight_group).re(
		':divider$',
		(lambda value: 'it is recommended that divider highlight group names end with ":divider"')
	).optional(),
	segments=sub_segments_spec,
).func(check_full_segment_data)
sub_segments_spec.optional().list(segment_spec)
del sub_segments_spec
segments_spec = Spec().optional().list(segment_spec).copy
segdict_spec = Spec(
	left=segments_spec().context_message('Error while loading segments from left side (key {key})'),
	right=segments_spec().context_message('Error while loading segments from right side (key {key})'),
).func(
	(lambda value, *args: (True, True, not (('left' in value) or ('right' in value)))),
	(lambda value: 'segments dictionary must contain either left, right or both keys')
).context_message('Error while loading segments (key {key})').copy
divside_spec = Spec(
	hard=divider_spec(),
	soft=divider_spec(),
).copy
segment_data_value_spec = Spec(
	after=Spec().printable().optional(),
	before=Spec().printable().optional(),
	display=Spec().type(bool).optional(),
	args=args_spec().func(lambda *args, **kwargs: check_args(get_all_possible_functions, *args, **kwargs)),
	contents=Spec().printable().optional(),
).copy
dividers_spec = Spec(
	left=divside_spec(),
	right=divside_spec(),
).copy
spaces_spec = Spec().unsigned().cmp(
	'le', 2, (lambda value: 'Are you sure you need such a big ({0}) number of spaces?'.format(value))
).copy
common_theme_spec = Spec(
	default_module=segment_module_spec().optional(),
	cursor_space=Spec().type(int, float).cmp('le', 100).cmp('gt', 0).optional(),
	cursor_columns=Spec().type(int).cmp('gt', 0).optional(),
).context_message('Error while loading theme').copy
top_theme_spec = common_theme_spec().update(
	dividers=dividers_spec(),
	spaces=spaces_spec(),
	use_non_breaking_spaces=Spec().type(bool).optional(),
	segment_data=Spec().unknown_spec(
		Spec().func(check_segment_data_key),
		segment_data_value_spec(),
	).optional().context_message('Error while loading segment data (key {key})'),
)
main_theme_spec = common_theme_spec().update(
	dividers=dividers_spec().optional(),
	spaces=spaces_spec().optional(),
	segment_data=Spec().unknown_spec(
		Spec().func(check_segment_data_key),
		segment_data_value_spec(),
	).optional().context_message('Error while loading segment data (key {key})'),
)
theme_spec = common_theme_spec().update(
	dividers=dividers_spec().optional(),
	spaces=spaces_spec().optional(),
	segment_data=Spec().unknown_spec(
		Spec().func(check_segment_data_key),
		segment_data_value_spec(),
	).optional().context_message('Error while loading segment data (key {key})'),
	segments=segdict_spec().update(above=Spec().list(segdict_spec()).optional()),
)


def register_common_names():
	register_common_name('player', 'powerline.segments.common.players', '_player')


def load_json_file(path):
	with open_file(path) as F:
		try:
			config, hadproblem = load(F)
		except MarkedError as e:
			return True, None, str(e)
		else:
			return hadproblem, config, None


def updated_with_config(d):
	hadproblem, config, error = load_json_file(d['path'])
	d.update(
		hadproblem=hadproblem,
		config=config,
		error=error,
	)
	return d


def find_all_ext_config_files(search_paths, subdir):
	for config_root in search_paths:
		top_config_subpath = join(config_root, subdir)
		if not os.path.isdir(top_config_subpath):
			if os.path.exists(top_config_subpath):
				yield {
					'error': 'Path {0} is not a directory'.format(top_config_subpath),
					'path': top_config_subpath,
				}
			continue
		for ext_name in os.listdir(top_config_subpath):
			ext_path = os.path.join(top_config_subpath, ext_name)
			if not os.path.isdir(ext_path):
				if ext_name.endswith('.json') and os.path.isfile(ext_path):
					yield updated_with_config({
						'error': False,
						'path': ext_path,
						'name': ext_name[:-5],
						'ext': None,
						'type': 'top_' + subdir,
					})
				else:
					yield {
						'error': 'Path {0} is not a directory or configuration file'.format(ext_path),
						'path': ext_path,
					}
				continue
			for config_file_name in os.listdir(ext_path):
				config_file_path = os.path.join(ext_path, config_file_name)
				if config_file_name.endswith('.json') and os.path.isfile(config_file_path):
					yield updated_with_config({
						'error': False,
						'path': config_file_path,
						'name': config_file_name[:-5],
						'ext': ext_name,
						'type': subdir,
					})
				else:
					yield {
						'error': 'Path {0} is not a configuration file'.format(config_file_path),
						'path': config_file_path,
					}


def dict2(d):
	return defaultdict(dict, ((k, dict(v)) for k, v in d.items()))


def check(paths=None, debug=False, echoerr=echoerr, require_ext=None):
	'''Check configuration sanity

	:param list paths:
		Paths from which configuration should be loaded.
	:param bool debug:
		Determines whether some information useful for debugging linter should 
		be output.
	:param function echoerr:
		Function that will be used to echo the error(s). Should accept four 
		optional keyword parameters: ``problem`` and ``problem_mark``, and 
		``context`` and ``context_mark``.
	:param str require_ext:
		Require configuration for some extension to be present.

	:return:
		``False`` if user configuration seems to be completely sane and ``True`` 
		if some problems were found.
	'''
	hadproblem = False

	register_common_names()
	search_paths = paths or get_config_paths()
	find_config_files = generate_config_finder(lambda: search_paths)

	logger = logging.getLogger('powerline-lint')
	logger.setLevel(logging.DEBUG if debug else logging.ERROR)
	logger.addHandler(logging.StreamHandler())

	ee = EchoErr(echoerr, logger)

	if require_ext:
		used_main_spec = main_spec.copy()
		try:
			used_main_spec['ext'][require_ext].required()
		except KeyError:
			used_main_spec['ext'][require_ext] = ext_spec()
	else:
		used_main_spec = main_spec

	lhadproblem = [False]
	load_json_config = generate_json_config_loader(lhadproblem)

	config_loader = ConfigLoader(run_once=True, load=load_json_config)

	lists = {
		'colorschemes': set(),
		'themes': set(),
		'exts': set(),
	}
	found_dir = {
		'themes': False,
		'colorschemes': False,
	}
	config_paths = defaultdict(lambda: defaultdict(dict))
	loaded_configs = defaultdict(lambda: defaultdict(dict))
	for d in chain(
		find_all_ext_config_files(search_paths, 'colorschemes'),
		find_all_ext_config_files(search_paths, 'themes'),
	):
		if d['error']:
			hadproblem = True
			ee(problem=d['error'])
			continue
		if d['hadproblem']:
			hadproblem = True
		if d['ext']:
			found_dir[d['type']] = True
			lists['exts'].add(d['ext'])
			if d['name'] == '__main__':
				pass
			elif d['name'].startswith('__') or d['name'].endswith('__'):
				hadproblem = True
				ee(problem='File name is not supposed to start or end with “__”: {0}'.format(
					d['path']))
			else:
				lists[d['type']].add(d['name'])
			config_paths[d['type']][d['ext']][d['name']] = d['path']
			loaded_configs[d['type']][d['ext']][d['name']] = d['config']
		else:
			config_paths[d['type']][d['name']] = d['path']
			loaded_configs[d['type']][d['name']] = d['config']

	for typ in ('themes', 'colorschemes'):
		if not found_dir[typ]:
			hadproblem = True
			ee(problem='Subdirectory {0} was not found in paths {1}'.format(typ, ', '.join(search_paths)))

	diff = set(config_paths['colorschemes']) - set(config_paths['themes'])
	if diff:
		hadproblem = True
		for ext in diff:
			typ = 'colorschemes' if ext in config_paths['themes'] else 'themes'
			if not config_paths['top_' + typ] or typ == 'themes':
				ee(problem='{0} extension {1} not present in {2}'.format(
					ext,
					'configuration' if (
						ext in loaded_configs['themes'] and ext in loaded_configs['colorschemes']
					) else 'directory',
					typ,
				))

	try:
		main_config = load_config('config', find_config_files, config_loader)
	except IOError:
		main_config = {}
		ee(problem='Configuration file not found: config.json')
		hadproblem = True
	except MarkedError as e:
		main_config = {}
		ee(problem=str(e))
		hadproblem = True
	else:
		if used_main_spec.match(
			main_config,
			data={'configs': config_paths, 'lists': lists},
			context=Context(main_config),
			echoerr=ee
		)[1]:
			hadproblem = True

	import_paths = [os.path.expanduser(path) for path in main_config.get('common', {}).get('paths', [])]

	try:
		colors_config = load_config('colors', find_config_files, config_loader)
	except IOError:
		colors_config = {}
		ee(problem='Configuration file not found: colors.json')
		hadproblem = True
	except MarkedError as e:
		colors_config = {}
		ee(problem=str(e))
		hadproblem = True
	else:
		if colors_spec.match(colors_config, context=Context(colors_config), echoerr=ee)[1]:
			hadproblem = True

	if lhadproblem[0]:
		hadproblem = True

	top_colorscheme_configs = dict(loaded_configs['top_colorschemes'])
	data = {
		'ext': None,
		'top_colorscheme_configs': top_colorscheme_configs,
		'ext_colorscheme_configs': {},
		'colors_config': colors_config
	}
	for colorscheme, config in loaded_configs['top_colorschemes'].items():
		data['colorscheme'] = colorscheme
		if top_colorscheme_spec.match(config, context=Context(config), data=data, echoerr=ee)[1]:
			hadproblem = True

	ext_colorscheme_configs = dict2(loaded_configs['colorschemes'])
	for ext, econfigs in ext_colorscheme_configs.items():
		data = {
			'ext': ext,
			'top_colorscheme_configs': top_colorscheme_configs,
			'ext_colorscheme_configs': ext_colorscheme_configs,
			'colors_config': colors_config,
		}
		for colorscheme, config in econfigs.items():
			data['colorscheme'] = colorscheme
			if ext == 'vim':
				spec = vim_colorscheme_spec
			elif ext == 'shell':
				spec = shell_colorscheme_spec
			else:
				spec = colorscheme_spec
			if spec.match(config, context=Context(config), data=data, echoerr=ee)[1]:
				hadproblem = True

	colorscheme_configs = {}
	for ext in lists['exts']:
		colorscheme_configs[ext] = {}
		for colorscheme in lists['colorschemes']:
			econfigs = ext_colorscheme_configs[ext]
			ecconfigs = econfigs.get(colorscheme)
			mconfigs = (
				top_colorscheme_configs.get(colorscheme),
				econfigs.get('__main__'),
				ecconfigs,
			)
			if not (mconfigs[0] or mconfigs[2]):
				continue
			config = None
			for mconfig in mconfigs:
				if not mconfig:
					continue
				if config:
					config = mergedicts_copy(config, mconfig)
				else:
					config = mconfig
			colorscheme_configs[ext][colorscheme] = config

	theme_configs = dict2(loaded_configs['themes'])
	top_theme_configs = dict(loaded_configs['top_themes'])
	for ext, configs in theme_configs.items():
		data = {
			'ext': ext,
			'colorscheme_configs': colorscheme_configs,
			'import_paths': import_paths,
			'main_config': main_config,
			'top_themes': top_theme_configs,
			'ext_theme_configs': configs,
			'colors_config': colors_config
		}
		for theme, config in configs.items():
			data['theme'] = theme
			if theme == '__main__':
				data['theme_type'] = 'main'
				spec = main_theme_spec
			else:
				data['theme_type'] = 'regular'
				spec = theme_spec
			if spec.match(config, context=Context(config), data=data, echoerr=ee)[1]:
				hadproblem = True

	for top_theme, config in top_theme_configs.items():
		data = {
			'ext': None,
			'colorscheme_configs': colorscheme_configs,
			'import_paths': import_paths,
			'main_config': main_config,
			'theme_configs': theme_configs,
			'ext_theme_configs': None,
			'colors_config': colors_config
		}
		data['theme_type'] = 'top'
		data['theme'] = top_theme
		if top_theme_spec.match(config, context=Context(config), data=data, echoerr=ee)[1]:
			hadproblem = True

	return hadproblem
