# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os
import re
import logging

from collections import defaultdict

from powerline.lib.threaded import ThreadedSegment
from powerline.lib.unicode import unicode
from powerline.lint.markedjson.markedvalue import MarkedUnicode
from powerline.lint.markedjson.error import DelayedEchoErr, Mark
from powerline.lint.selfcheck import havemarks
from powerline.lint.context import JStr, list_themes
from powerline.lint.imp import WithPath, import_function, import_segment
from powerline.lint.spec import Spec
from powerline.lint.inspect import getconfigargspec


list_sep = JStr(', ')


generic_keys = set((
	'exclude_modes', 'include_modes',
	'exclude_function', 'include_function',
	'width', 'align',
	'name',
	'draw_soft_divider', 'draw_hard_divider',
	'priority',
	'after', 'before',
	'display'
))
type_keys = {
	'function': set(('function', 'args', 'draw_inner_divider')),
	'string': set(('contents', 'type', 'highlight_groups', 'divider_highlight_group')),
	'segment_list': set(('function', 'segments', 'args', 'type')),
}
required_keys = {
	'function': set(('function',)),
	'string': set(()),
	'segment_list': set(('function', 'segments',)),
}
highlight_keys = set(('highlight_groups', 'name'))


def get_function_strings(function_name, context, ext):
	if '.' in function_name:
		module, function_name = function_name.rpartition('.')[::2]
	else:
		module = context[0][1].get(
			'default_module', MarkedUnicode('powerline.segments.' + ext, None))
	return module, function_name


def check_matcher_func(ext, match_name, data, context, echoerr):
	havemarks(match_name)
	import_paths = [os.path.expanduser(path) for path in context[0][1].get('common', {}).get('paths', [])]

	match_module, separator, match_function = match_name.rpartition('.')
	if not separator:
		match_module = 'powerline.matchers.{0}'.format(ext)
		match_function = match_name
	with WithPath(import_paths):
		try:
			func = getattr(__import__(str(match_module), fromlist=[str(match_function)]), str(match_function))
		except ImportError:
			echoerr(context='Error while loading matcher functions',
			        problem='failed to load module {0}'.format(match_module),
			        problem_mark=match_name.mark)
			return True, False, True
		except AttributeError:
			echoerr(context='Error while loading matcher functions',
			        problem='failed to load matcher function {0}'.format(match_function),
			        problem_mark=match_name.mark)
			return True, False, True

	if not callable(func):
		echoerr(context='Error while loading matcher functions',
		        problem='loaded “function” {0} is not callable'.format(match_function),
		        problem_mark=match_name.mark)
		return True, False, True

	if hasattr(func, 'func_code') and hasattr(func.func_code, 'co_argcount'):
		if func.func_code.co_argcount != 1:
			echoerr(
				context='Error while loading matcher functions',
				problem=(
					'function {0} accepts {1} arguments instead of 1. '
					'Are you sure it is the proper function?'
				).format(match_function, func.func_code.co_argcount),
				problem_mark=match_name.mark
			)

	return True, False, False


def check_ext(ext, data, context, echoerr):
	havemarks(ext)
	hadsomedirs = False
	hadproblem = False
	if ext not in data['lists']['exts']:
		hadproblem = True
		echoerr(context='Error while loading {0} extension configuration'.format(ext),
		        context_mark=ext.mark,
		        problem='extension configuration does not exist')
	else:
		for typ in ('themes', 'colorschemes'):
			if ext not in data['configs'][typ] and not data['configs']['top_' + typ]:
				hadproblem = True
				echoerr(context='Error while loading {0} extension configuration'.format(ext),
				        context_mark=ext.mark,
				        problem='{0} configuration does not exist'.format(typ))
			else:
				hadsomedirs = True
	return hadsomedirs, hadproblem


def check_config(d, theme, data, context, echoerr):
	if len(context) == 4:
		ext = context[-2][0]
	else:
		# local_themes
		ext = context[-3][0]
	if ext not in data['lists']['exts']:
		echoerr(context='Error while loading {0} extension configuration'.format(ext),
		        context_mark=ext.mark,
		        problem='extension configuration does not exist')
		return True, False, True
	if (
		(ext not in data['configs'][d] or theme not in data['configs'][d][ext])
		and theme not in data['configs']['top_' + d]
	):
		echoerr(context='Error while loading {0} from {1} extension configuration'.format(d[:-1], ext),
		        problem='failed to find configuration file {0}/{1}/{2}.json'.format(d, ext, theme),
		        problem_mark=theme.mark)
		return True, False, True
	return True, False, False


def check_top_theme(theme, data, context, echoerr):
	havemarks(theme)
	if theme not in data['configs']['top_themes']:
		echoerr(context='Error while checking extension configuration (key {key})'.format(key=context.key),
		        context_mark=context[-2][0].mark,
		        problem='failed to find top theme {0}'.format(theme),
		        problem_mark=theme.mark)
		return True, False, True
	return True, False, False


def check_color(color, data, context, echoerr):
	havemarks(color)
	if (color not in data['colors_config'].get('colors', {})
		and color not in data['colors_config'].get('gradients', {})):
		echoerr(
			context='Error while checking highlight group in colorscheme (key {key})'.format(
				key=context.key),
			problem='found unexistent color or gradient {0}'.format(color),
			problem_mark=color.mark
		)
		return True, False, True
	return True, False, False


def check_translated_group_name(group, data, context, echoerr):
	return check_group(group, data, context, echoerr)


def check_group(group, data, context, echoerr):
	havemarks(group)
	if not isinstance(group, unicode):
		return True, False, False
	colorscheme = data['colorscheme']
	ext = data['ext']
	configs = []
	if ext:
		if colorscheme == '__main__':
			configs.append([config for config in data['ext_colorscheme_configs'][ext].items()])
			configs.append([config for config in data['top_colorscheme_configs'].items()])
		else:
			try:
				configs.append([data['ext_colorscheme_configs'][ext][colorscheme]])
			except KeyError:
				pass
			try:
				configs.append([data['ext_colorscheme_configs'][ext]['__main__']])
			except KeyError:
				pass
			try:
				configs.append([data['top_colorscheme_configs'][colorscheme]])
			except KeyError:
				pass
	else:
		try:
			configs.append([data['top_colorscheme_configs'][colorscheme]])
		except KeyError:
			pass
	new_echoerr = DelayedEchoErr(echoerr)
	hadproblem = False
	for config_lst in configs:
		tofind = len(config_lst)
		not_found = []
		for config in config_lst:
			if isinstance(config, tuple):
				new_colorscheme, config = config
				new_data = data.copy()
				new_data['colorscheme'] = new_colorscheme
			else:
				new_data = data
			havemarks(config)
			try:
				group_data = config['groups'][group]
			except KeyError:
				not_found.append(config.mark.name)
			else:
				proceed, echo, chadproblem = check_group(
					group_data,
					new_data,
					context,
					echoerr,
				)
				if chadproblem:
					hadproblem = True
				else:
					tofind -= 1
					if not tofind:
						return proceed, echo, hadproblem
				if not proceed:
					break
		if not_found:
			new_echoerr(
				context='Error while checking group definition in colorscheme (key {key})'.format(
					key=context.key),
				problem='name {0} is not present in {1} {2} colorschemes: {3}'.format(
					group, tofind, ext, ', '.join(not_found)),
				problem_mark=group.mark
			)
	new_echoerr.echo_all()
	return True, False, hadproblem


def check_key_compatibility(segment, data, context, echoerr):
	havemarks(segment)
	segment_type = segment.get('type', MarkedUnicode('function', None))
	havemarks(segment_type)

	if segment_type not in type_keys:
		echoerr(context='Error while checking segments (key {key})'.format(key=context.key),
		        problem='found segment with unknown type {0}'.format(segment_type),
		        problem_mark=segment_type.mark)
		return False, False, True

	hadproblem = False

	keys = set(segment)
	if not ((keys - generic_keys) < type_keys[segment_type]):
		unknown_keys = keys - generic_keys - type_keys[segment_type]
		echoerr(
			context='Error while checking segments (key {key})'.format(key=context.key),
			context_mark=context[-1][1].mark,
			problem='found keys not used with the current segment type: {0}'.format(
				list_sep.join(unknown_keys)),
			problem_mark=list(unknown_keys)[0].mark
		)
		hadproblem = True

	if not (keys >= required_keys[segment_type]):
		missing_keys = required_keys[segment_type] - keys
		echoerr(
			context='Error while checking segments (key {key})'.format(key=context.key),
			context_mark=context[-1][1].mark,
			problem='found missing required keys: {0}'.format(
				list_sep.join(missing_keys))
		)
		hadproblem = True

	if not (segment_type == 'function' or (keys & highlight_keys)):
		echoerr(
			context='Error while checking segments (key {key})'.format(key=context.key),
			context_mark=context[-1][1].mark,
			problem=(
				'found missing keys required to determine highlight group. '
				'Either highlight_groups or name key must be present'
			)
		)
		hadproblem = True

	return True, False, hadproblem


def check_segment_module(module, data, context, echoerr):
	havemarks(module)
	with WithPath(data['import_paths']):
		try:
			__import__(str(module))
		except ImportError as e:
			if echoerr.logger.level >= logging.DEBUG:
				echoerr.logger.exception(e)
			echoerr(context='Error while checking segments (key {key})'.format(key=context.key),
			        problem='failed to import module {0}'.format(module),
			        problem_mark=module.mark)
			return True, False, True
	return True, False, False


def check_full_segment_data(segment, data, context, echoerr):
	if 'name' not in segment and 'function' not in segment:
		return True, False, False

	ext = data['ext']
	theme_segment_data = context[0][1].get('segment_data', {})
	main_theme_name = data['main_config'].get('ext', {}).get(ext, {}).get('theme', None)
	if not main_theme_name or data['theme'] == main_theme_name:
		top_segment_data = {}
	else:
		top_segment_data = data['ext_theme_configs'].get(main_theme_name, {}).get('segment_data', {})

	if segment.get('type', 'function') == 'function':
		function_name = segment.get('function')
		if function_name:
			module, function_name = get_function_strings(function_name, context, ext)
			names = [module + '.' + function_name, function_name]
		else:
			names = []
	elif segment.get('name'):
		names = [segment['name']]
	else:
		return True, False, False

	segment_copy = segment.copy()

	for key in ('before', 'after', 'args', 'contents'):
		if key not in segment_copy:
			for segment_data in [theme_segment_data, top_segment_data]:
				for name in names:
					try:
						val = segment_data[name][key]
						k = segment_data[name].keydict[key]
						segment_copy[k] = val
					except KeyError:
						pass

	return check_key_compatibility(segment_copy, data, context, echoerr)


highlight_group_spec = Spec().ident().copy
_highlight_group_spec = highlight_group_spec().context_message(
	'Error while checking function documentation while checking theme (key {key})')


def check_hl_group_name(hl_group, context_mark, context, echoerr):
	'''Check highlight group name: it should match naming conventions

	:param str hl_group:
		Checked group.
	:param Mark context_mark:
		Context mark. May be ``None``.
	:param Context context:
		Current context.
	:param func echoerr:
		Function used for error reporting.

	:return: ``False`` if check succeeded and ``True`` if it failed.
	'''
	return _highlight_group_spec.match(hl_group, context_mark=context_mark, context=context, echoerr=echoerr)[1]


def check_segment_function(function_name, data, context, echoerr):
	havemarks(function_name)
	ext = data['ext']
	module, function_name = get_function_strings(function_name, context, ext)
	if context[-2][1].get('type', 'function') == 'function':
		func = import_segment(function_name, data, context, echoerr, module=module)

		if not func:
			return True, False, True

		hl_groups = []
		divider_hl_group = None

		if func.__doc__:
			H_G_USED_STR = 'Highlight groups used: '
			LHGUS = len(H_G_USED_STR)
			D_H_G_USED_STR = 'Divider highlight group used: '
			LDHGUS = len(D_H_G_USED_STR)
			pointer = 0
			mark_name = '<{0} docstring>'.format(function_name)
			for i, line in enumerate(func.__doc__.split('\n')):
				if H_G_USED_STR in line:
					idx = line.index(H_G_USED_STR) + LHGUS
					hl_groups.append((
						line[idx:],
						(mark_name, i + 1, idx + 1, func.__doc__),
						pointer + idx
					))
				elif D_H_G_USED_STR in line:
					idx = line.index(D_H_G_USED_STR) + LDHGUS + 2
					mark = Mark(mark_name, i + 1, idx + 1, func.__doc__, pointer + idx)
					divider_hl_group = MarkedUnicode(line[idx:-3], mark)
				pointer += len(line) + len('\n')

		hadproblem = False

		if divider_hl_group:
			r = hl_exists(divider_hl_group, data, context, echoerr, allow_gradients=True)
			if r:
				echoerr(
					context='Error while checking theme (key {key})'.format(key=context.key),
					context_mark=function_name.mark,
					problem=(
						'found highlight group {0} not defined in the following colorschemes: {1}\n'
						'(Group name was obtained from function documentation.)'
					).format(divider_hl_group, list_sep.join(r)),
					problem_mark=divider_hl_group.mark,
				)
				hadproblem = True
			if check_hl_group_name(divider_hl_group, function_name.mark, context, echoerr):
				hadproblem = True

		if hl_groups:
			greg = re.compile(r'``([^`]+)``( \(gradient\))?')
			parsed_hl_groups = []
			for line, mark_args, pointer in hl_groups:
				for s in line.split(', '):
					required_pack = []
					sub_pointer = pointer
					for subs in s.split(' or '):
						match = greg.match(subs)
						try:
							if not match:
								continue
							hl_group = MarkedUnicode(
								match.group(1),
								Mark(*mark_args, pointer=sub_pointer + match.start(1))
							)
							if check_hl_group_name(hl_group, function_name.mark, context, echoerr):
								hadproblem = True
							gradient = bool(match.group(2))
							required_pack.append((hl_group, gradient))
						finally:
							sub_pointer += len(subs) + len(' or ')
					parsed_hl_groups.append(required_pack)
					pointer += len(s) + len(', ')
			del hl_group, gradient
			for required_pack in parsed_hl_groups:
				rs = [
					hl_exists(hl_group, data, context, echoerr, allow_gradients=('force' if gradient else False))
					for hl_group, gradient in required_pack
				]
				if all(rs):
					echoerr(
						context='Error while checking theme (key {key})'.format(key=context.key),
						problem=(
							'found highlight groups list ({0}) with all groups not defined in some colorschemes\n'
							'(Group names were taken from function documentation.)'
						).format(list_sep.join((h[0] for h in required_pack))),
						problem_mark=function_name.mark
					)
					for r, h in zip(rs, required_pack):
						echoerr(
							context='Error while checking theme (key {key})'.format(key=context.key),
							problem='found highlight group {0} not defined in the following colorschemes: {1}'.format(
								h[0], list_sep.join(r))
						)
					hadproblem = True
		else:
			r = hl_exists(function_name, data, context, echoerr, allow_gradients=True)
			if r:
				echoerr(
					context='Error while checking theme (key {key})'.format(key=context.key),
					problem=(
						'found highlight group {0} not defined in the following colorschemes: {1}\n'
						'(If not specified otherwise in documentation, '
						'highlight group for function segments\n'
						'is the same as the function name.)'
					).format(function_name, list_sep.join(r)),
					problem_mark=function_name.mark
				)
				hadproblem = True

		return True, False, hadproblem
	elif context[-2][1].get('type') != 'segment_list':
		if function_name not in context[0][1].get('segment_data', {}):
			main_theme_name = data['main_config'].get('ext', {}).get(ext, {}).get('theme', None)
			if data['theme'] == main_theme_name:
				main_theme = {}
			else:
				main_theme = data['ext_theme_configs'].get(main_theme_name, {})
			if (
				function_name not in main_theme.get('segment_data', {})
				and function_name not in data['ext_theme_configs'].get('__main__', {}).get('segment_data', {})
				and not any(((function_name in theme.get('segment_data', {})) for theme in data['top_themes'].values()))
			):
				echoerr(context='Error while checking segments (key {key})'.format(key=context.key),
				        problem='found useless use of name key (such name is not present in theme/segment_data)',
				        problem_mark=function_name.mark)

	return True, False, False


def hl_group_in_colorscheme(hl_group, cconfig, allow_gradients, data, context, echoerr):
	havemarks(hl_group, cconfig)
	if hl_group not in cconfig.get('groups', {}):
		return False
	elif not allow_gradients or allow_gradients == 'force':
		group_config = cconfig['groups'][hl_group]
		while isinstance(group_config, unicode):
			try:
				group_config = cconfig['groups'][group_config]
			except KeyError:
				# No such group. Error was already reported when checking 
				# colorschemes.
				return True
		havemarks(group_config)
		hadgradient = False
		for ckey in ('fg', 'bg'):
			color = group_config.get(ckey)
			if not color:
				# No color. Error was already reported when checking 
				# colorschemes.
				return True
			havemarks(color)
			# Gradients are only allowed for function segments. Note that 
			# whether *either* color or gradient exists should have been 
			# already checked
			hascolor = color in data['colors_config'].get('colors', {})
			hasgradient = color in data['colors_config'].get('gradients', {})
			if hasgradient:
				hadgradient = True
			if allow_gradients is False and not hascolor and hasgradient:
				echoerr(
					context='Error while checking highlight group in theme (key {key})'.format(
						key=context.key),
					context_mark=hl_group.mark,
					problem='group {0} is using gradient {1} instead of a color'.format(hl_group, color),
					problem_mark=color.mark
				)
				return False
		if allow_gradients == 'force' and not hadgradient:
			echoerr(
				context='Error while checking highlight group in theme (key {key})'.format(
					key=context.key),
				context_mark=hl_group.mark,
				problem='group {0} should have at least one gradient color, but it has no'.format(hl_group),
				problem_mark=group_config.mark
			)
			return False
	return True


def hl_exists(hl_group, data, context, echoerr, allow_gradients=False):
	havemarks(hl_group)
	ext = data['ext']
	if ext not in data['colorscheme_configs']:
		# No colorschemes. Error was already reported, no need to report it 
		# twice
		return []
	r = []
	found = False
	for colorscheme, cconfig in data['colorscheme_configs'][ext].items():
		if hl_group_in_colorscheme(hl_group, cconfig, allow_gradients, data, context, echoerr):
			found = True
		else:
			r.append(colorscheme)
	if not found:
		pass
	return r


def check_highlight_group(hl_group, data, context, echoerr):
	havemarks(hl_group)
	r = hl_exists(hl_group, data, context, echoerr)
	if r:
		echoerr(
			context='Error while checking theme (key {key})'.format(key=context.key),
			problem='found highlight group {0} not defined in the following colorschemes: {1}'.format(
				hl_group, list_sep.join(r)),
			problem_mark=hl_group.mark
		)
		return True, False, True
	return True, False, False


def check_highlight_groups(hl_groups, data, context, echoerr):
	havemarks(hl_groups)
	rs = [hl_exists(hl_group, data, context, echoerr) for hl_group in hl_groups]
	if all(rs):
		echoerr(
			context='Error while checking theme (key {key})'.format(key=context.key),
			problem='found highlight groups list ({0}) with all groups not defined in some colorschemes'.format(
				list_sep.join((unicode(h) for h in hl_groups))),
			problem_mark=hl_groups.mark
		)
		for r, hl_group in zip(rs, hl_groups):
			echoerr(
				context='Error while checking theme (key {key})'.format(key=context.key),
				problem='found highlight group {0} not defined in the following colorschemes: {1}'.format(
					hl_group, list_sep.join(r)),
				problem_mark=hl_group.mark
			)
		return True, False, True
	return True, False, False


def check_segment_data_key(key, data, context, echoerr):
	havemarks(key)
	has_module_name = '.' in key
	found = False
	for ext, theme in list_themes(data, context):
		for segments in theme.get('segments', {}).values():
			for segment in segments:
				if 'name' in segment:
					if key == segment['name']:
						found = True
						break
				else:
					function_name = segment.get('function')
					if function_name:
						module, function_name = get_function_strings(function_name, ((None, theme),), ext)
						if has_module_name:
							full_name = module + '.' + function_name
							if key == full_name:
								found = True
								break
						else:
							if key == function_name:
								found = True
								break
			if found:
				break
		if found:
			break
	else:
		if data['theme_type'] != 'top':
			echoerr(context='Error while checking segment data',
			        problem='found key {0} that cannot be associated with any segment'.format(key),
			        problem_mark=key.mark)
			return True, False, True

	return True, False, False


threaded_args_specs = {
	'interval': Spec().cmp('gt', 0.0),
	'update_first': Spec().type(bool),
	'shutdown_event': Spec().error('Shutdown event must be set by powerline'),
}


def check_args_variant(func, args, data, context, echoerr):
	havemarks(args)
	argspec = getconfigargspec(func)
	present_args = set(args)
	all_args = set(argspec.args)
	required_args = set(argspec.args[:-len(argspec.defaults)])

	hadproblem = False

	if required_args - present_args:
		echoerr(
			context='Error while checking segment arguments (key {key})'.format(key=context.key),
			context_mark=args.mark,
			problem='some of the required keys are missing: {0}'.format(list_sep.join(required_args - present_args))
		)
		hadproblem = True

	if not all_args >= present_args:
		echoerr(context='Error while checking segment arguments (key {key})'.format(key=context.key),
		        context_mark=args.mark,
		        problem='found unknown keys: {0}'.format(list_sep.join(present_args - all_args)),
		        problem_mark=next(iter(present_args - all_args)).mark)
		hadproblem = True

	if isinstance(func, ThreadedSegment):
		for key in set(threaded_args_specs) & present_args:
			proceed, khadproblem = threaded_args_specs[key].match(
				args[key],
				args.mark,
				data,
				context.enter_key(args, key),
				echoerr
			)
			if khadproblem:
				hadproblem = True
			if not proceed:
				return hadproblem

	return hadproblem


def check_args(get_functions, args, data, context, echoerr):
	new_echoerr = DelayedEchoErr(echoerr)
	count = 0
	hadproblem = False
	for func in get_functions(data, context, new_echoerr):
		count += 1
		shadproblem = check_args_variant(func, args, data, context, echoerr)
		if shadproblem:
			hadproblem = True

	if not count:
		hadproblem = True
		if new_echoerr:
			new_echoerr.echo_all()
		else:
			echoerr(context='Error while checking segment arguments (key {key})'.format(key=context.key),
			        context_mark=context[-2][1].mark,
			        problem='no suitable segments found')

	return True, False, hadproblem


def get_one_segment_function(data, context, echoerr):
	ext = data['ext']
	function_name = context[-2][1].get('function')
	if function_name:
		module, function_name = get_function_strings(function_name, context, ext)
		func = import_segment(function_name, data, context, echoerr, module=module)
		if func:
			yield func


common_names = defaultdict(set)


def register_common_name(name, cmodule, cname):
	s = cmodule + '.' + cname
	cmodule_mark = Mark('<common name definition>', 1, 1, s, 1)
	cname_mark = Mark('<common name definition>', 1, len(cmodule) + 1, s, len(cmodule) + 1)
	common_names[name].add((MarkedUnicode(cmodule, cmodule_mark), MarkedUnicode(cname, cname_mark)))


def get_all_possible_functions(data, context, echoerr):
	name = context[-2][0]
	module, name = name.rpartition('.')[::2]
	if module:
		func = import_segment(name, data, context, echoerr, module=module)
		if func:
			yield func
	else:
		if name in common_names:
			for cmodule, cname in common_names[name]:
				cfunc = import_segment(cname, data, context, echoerr, module=MarkedUnicode(cmodule, None))
				if cfunc:
					yield cfunc
		for ext, theme_config in list_themes(data, context):
			for segments in theme_config.get('segments', {}).values():
				for segment in segments:
					if segment.get('type', 'function') == 'function':
						function_name = segment.get('function')
						current_name = segment.get('name')
						if function_name:
							module, function_name = get_function_strings(function_name, ((None, theme_config),), ext)
							if current_name == name or function_name == name:
								func = import_segment(function_name, data, context, echoerr, module=module)
								if func:
									yield func


def check_exinclude_function(name, data, context, echoerr):
	ext = data['ext']
	module, name = name.rpartition('.')[::2]
	if not module:
		module = MarkedUnicode('powerline.selectors.' + ext, None)
	func = import_function('selector', name, data, context, echoerr, module=module)
	if not func:
		return True, False, True
	return True, False, False
