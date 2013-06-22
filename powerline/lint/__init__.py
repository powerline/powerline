# vim:fileencoding=utf-8:noet

from powerline.lint.markedjson import load
from powerline import find_config_file, Powerline
from powerline.lib.config import load_json_config
from powerline.lint.markedjson.error import echoerr, MarkedError
from powerline.segments.vim import vim_modes
from powerline.lint.inspect import getconfigargspec
from powerline.lib.threaded import ThreadedSegment
import itertools
import sys
import os
import re
from collections import defaultdict
from copy import copy
import logging


try:
	from __builtin__ import unicode
except ImportError:
	unicode = str


def open_file(path):
	return open(path, 'rb')


EMPTYTUPLE = tuple()


class JStr(unicode):
	def join(self, iterable):
		return super(JStr, self).join((unicode(item) for item in iterable))


key_sep = JStr('/')
list_sep = JStr(', ')


def context_key(context):
	return key_sep.join((c[0] for c in context))


class EchoErr(object):
	__slots__ = ('echoerr', 'logger',)

	def __init__(self, echoerr, logger):
		self.echoerr = echoerr
		self.logger = logger

	def __call__(self, *args, **kwargs):
		self.echoerr(*args, **kwargs)


class DelayedEchoErr(EchoErr):
	__slots__ = ('echoerr', 'logger', 'errs')

	def __init__(self, echoerr):
		super(DelayedEchoErr, self).__init__(echoerr, echoerr.logger)
		self.errs = []

	def __call__(self, *args, **kwargs):
		self.errs.append((args, kwargs))

	def echo_all(self):
		for args, kwargs in self.errs:
			self.echoerr(*args, **kwargs)

	def __nonzero__(self):
		return not not self.errs


class Spec(object):
	def __init__(self, **keys):
		new_keys = {}
		self.specs = list(keys.values())
		for k, v in keys.items():
			new_keys[k] = len(self.specs)
			self.specs.append(v)
		self.keys = new_keys
		self.checks = []
		self.cmsg = ''
		self.isoptional = False
		self.uspecs = []
		self.ufailmsg = lambda key: 'found unknown key: {0}'.format(key)
		if keys:
			self.type(dict)

	def copy(self):
		return self.__class__().update(self.__dict__)

	def update(self, d):
		self.__dict__.update(d)
		self.checks = copy(self.checks)
		self.uspecs = copy(self.uspecs)
		self.specs = [spec.copy() for spec in self.specs]
		return self

	def unknown_spec(self, keyfunc, spec):
		if isinstance(keyfunc, Spec):
			self.specs.append(keyfunc)
			keyfunc = len(self.specs) - 1
		self.specs.append(spec)
		self.uspecs.append((keyfunc, len(self.specs) - 1))
		return self

	def unknown_msg(self, msgfunc):
		self.ufailmsg = msgfunc
		return self

	def context_message(self, msg):
		self.cmsg = msg
		for spec in self.specs:
			if not spec.cmsg:
				spec.context_message(msg)
		return self

	def check_type(self, value, context_mark, data, context, echoerr, types):
		if type(value.value) not in types:
			echoerr(context=self.cmsg.format(key=context_key(context)),
					context_mark=context_mark,
					problem='{0!r} must be a {1} instance, not {2}'.format(
						value,
						list_sep.join((t.__name__ for t in types)),
						type(value.value).__name__
					),
					problem_mark=value.mark)
			return False, True
		return True, False

	def check_func(self, value, context_mark, data, context, echoerr, func, msg_func):
		proceed, echo, hadproblem = func(value, data, context, echoerr)
		if echo and hadproblem:
			echoerr(context=self.cmsg.format(key=context_key(context)),
					context_mark=context_mark,
					problem=msg_func(value),
					problem_mark=value.mark)
		return proceed, hadproblem

	def check_list(self, value, context_mark, data, context, echoerr, item_func, msg_func):
		i = 0
		hadproblem = False
		for item in value:
			if isinstance(item_func, int):
				spec = self.specs[item_func]
				proceed, fhadproblem = spec.match(item, value.mark, data, context + (('list item ' + unicode(i), item),), echoerr)
			else:
				proceed, echo, fhadproblem = item_func(item, data, context, echoerr)
				if echo and fhadproblem:
					echoerr(context=self.cmsg.format(key=context_key(context) + '/list item ' + unicode(i)),
							context_mark=value.mark,
							problem=msg_func(item),
							problem_mark=item.mark)
			if fhadproblem:
				hadproblem = True
			if not proceed:
				return proceed, hadproblem
			i += 1
		return True, hadproblem

	def check_either(self, value, context_mark, data, context, echoerr, start, end):
		new_echoerr = DelayedEchoErr(echoerr)

		hadproblem = False
		for spec in self.specs[start:end]:
			proceed, hadproblem = spec.match(value, value.mark, data, context, new_echoerr)
			if not proceed:
				break
			if not hadproblem:
				return True, False

		new_echoerr.echo_all()

		return False, hadproblem

	def check_tuple(self, value, context_mark, data, context, echoerr, start, end):
		hadproblem = False
		for (i, item, spec) in zip(itertools.count(), value, self.specs[start:end]):
			proceed, ihadproblem = spec.match(item, value.mark, data, context + (('tuple item ' + unicode(i), item),), echoerr)
			if ihadproblem:
				hadproblem = True
			if not proceed:
				return False, hadproblem
		return True, hadproblem

	def type(self, *args):
		self.checks.append(('check_type', args))
		return self

	cmp_funcs = {
		'le': lambda x, y: x <= y,
		'lt': lambda x, y: x < y,
		'ge': lambda x, y: x >= y,
		'gt': lambda x, y: x > y,
		'eq': lambda x, y: x == y,
	}

	cmp_msgs = {
		'le': 'lesser or equal to',
		'lt': 'lesser then',
		'ge': 'greater or equal to',
		'gt': 'greater then',
		'eq': 'equal to',
	}

	def len(self, comparison, cint, msg_func=None):
		cmp_func = self.cmp_funcs[comparison]
		msg_func = msg_func or (lambda value: 'length of {0!r} is not {1} {2}'.format(value, self.cmp_msgs[comparison], cint))
		self.checks.append(('check_func',
					(lambda value, *args: (True, True, not cmp_func(len(value), cint))),
					msg_func))
		return self

	def cmp(self, comparison, cint, msg_func=None):
		if type(cint) is str:
			self.type(unicode)
		elif type(cint) is float:
			self.type(int, float)
		else:
			self.type(type(cint))
		cmp_func = self.cmp_funcs[comparison]
		msg_func = msg_func or (lambda value: '{0} is not {1} {2}'.format(value, self.cmp_msgs[comparison], cint))
		self.checks.append(('check_func',
					(lambda value, *args: (True, True, not cmp_func(value.value, cint))),
					msg_func))
		return self

	def unsigned(self, msg_func=None):
		self.type(int)
		self.checks.append(('check_func',
					(lambda value, *args: (True, True, value < 0)),
					lambda value: '{0} must be greater then zero'.format(value)))
		return self

	def list(self, item_func, msg_func=None):
		self.type(list)
		if isinstance(item_func, Spec):
			self.specs.append(item_func)
			item_func = len(self.specs) - 1
		self.checks.append(('check_list', item_func, msg_func or (lambda item: 'failed check')))
		return self

	def tuple(self, *specs):
		self.type(list)

		max_len = len(specs)
		min_len = max_len
		for spec in reversed(specs):
			if spec.isoptional:
				min_len -= 1
			else:
				break
		if max_len == min_len:
			self.len('eq', len(specs))
		else:
			self.len('ge', min_len)
			self.len('le', max_len)

		start = len(self.specs)
		for i, spec in zip(itertools.count(), specs):
			self.specs.append(spec)
		self.checks.append(('check_tuple', start, len(self.specs)))
		return self

	def func(self, func, msg_func=None):
		self.checks.append(('check_func', func, msg_func or (lambda value: 'failed check')))
		return self

	def re(self, regex, msg_func=None):
		self.type(unicode)
		compiled = re.compile(regex)
		msg_func = msg_func or (lambda value: 'String "{0}" does not match "{1}"'.format(value, regex))
		self.checks.append(('check_func',
					(lambda value, *args: (True, True, not compiled.match(value.value))),
					msg_func))
		return self

	def ident(self, msg_func=None):
		msg_func = msg_func or (lambda value: 'String "{0}" is not an alphanumeric/underscore identifier'.format(value))
		return self.re('^\w+$', msg_func)

	def oneof(self, collection, msg_func=None):
		msg_func = msg_func or (lambda value: '"{0}" must be one of {1!r}'.format(value, list(collection)))
		self.checks.append(('check_func',
						lambda value, *args: (True, True, value not in collection),
						msg_func))
		return self

	def error(self, msg):
		self.checks.append(('check_func', lambda *args: (True, True, True),
							lambda value: msg.format(value)))
		return self

	def either(self, *specs):
		start = len(self.specs)
		self.specs.extend(specs)
		self.checks.append(('check_either', start, len(self.specs)))
		return self

	def optional(self):
		self.isoptional = True
		return self

	def match_checks(self, *args):
		hadproblem = False
		for check in self.checks:
			proceed, chadproblem = getattr(self, check[0])(*(args + check[1:]))
			if chadproblem:
				hadproblem = True
			if not proceed:
				return False, hadproblem
		return True, hadproblem

	def match(self, value, context_mark=None, data=None, context=EMPTYTUPLE, echoerr=echoerr):
		proceed, hadproblem = self.match_checks(value, context_mark, data, context, echoerr)
		if proceed:
			if self.keys or self.uspecs:
				for key, vali in self.keys.items():
					valspec = self.specs[vali]
					if key in value:
						proceed, mhadproblem = valspec.match(value[key], value.mark, data, context + ((key, value[key]),), echoerr)
						if mhadproblem:
							hadproblem = True
						if not proceed:
							return False, hadproblem
					else:
						if not valspec.isoptional:
							hadproblem = True
							echoerr(context=self.cmsg.format(key=context_key(context)),
									context_mark=None,
									problem='required key is missing: {0}'.format(key),
									problem_mark=value.mark)
				for key in value.keys():
					if key not in self.keys:
						for keyfunc, vali in self.uspecs:
							valspec = self.specs[vali]
							if isinstance(keyfunc, int):
								spec = self.specs[keyfunc]
								proceed, khadproblem = spec.match(key, context_mark, data, context, echoerr)
							else:
								proceed, khadproblem = keyfunc(key, data, context, echoerr)
							if khadproblem:
								hadproblem = True
							if proceed:
								proceed, vhadproblem = valspec.match(value[key], value.mark, data, context + ((key, value[key]),), echoerr)
								if vhadproblem:
									hadproblem = True
								break
						else:
							hadproblem = True
							if self.ufailmsg:
								echoerr(context=self.cmsg.format(key=context_key(context)),
										context_mark=None,
										problem=self.ufailmsg(key),
										problem_mark=key.mark)
		return True, hadproblem


class WithPath(object):
	def __init__(self, import_paths):
		self.import_paths = import_paths

	def __enter__(self):
		self.oldpath = sys.path
		sys.path = self.import_paths + sys.path

	def __exit__(self, *args):
		sys.path = self.oldpath


def check_matcher_func(ext, match_name, data, context, echoerr):
	import_paths = [os.path.expanduser(path) for path in context[0][1].get('common', {}).get('paths', [])]

	match_module, separator, match_function = match_name.rpartition('.')
	if not separator:
		match_module = 'powerline.matchers.{0}'.format(ext)
		match_function = match_name
	with WithPath(import_paths):
		try:
			func = getattr(__import__(match_module, fromlist=[match_function]), unicode(match_function))
		except ImportError:
			echoerr(context='Error while loading matcher functions',
					problem='failed to load module {0}'.format(match_module),
					problem_mark=match_name.mark)
			return True, True
		except AttributeError:
			echoerr(context='Error while loading matcher functions',
					problem='failed to load matcher function {0}'.format(match_function),
					problem_mark=match_name.mark)
			return True, True

	if not callable(func):
		echoerr(context='Error while loading matcher functions',
				problem='loaded "function" {0} is not callable'.format(match_function),
				problem_mark=match_name.mark)
		return True, True

	if hasattr(func, 'func_code') and hasattr(func.func_code, 'co_argcount'):
		if func.func_code.co_argcount != 1:
			echoerr(context='Error while loading matcher functions',
					problem='function {0} accepts {1} arguments instead of 1. Are you sure it is the proper function?'.format(match_function, func.func_code.co_argcount),
					problem_mark=match_name.mark)

	return True, False


def check_ext(ext, data, context, echoerr):
	hadsomedirs = False
	hadproblem = False
	for subdir in ('themes', 'colorschemes'):
		if ext not in data['configs'][subdir]:
			hadproblem = True
			echoerr(context='Error while loading {0} extension configuration'.format(ext),
					context_mark=ext.mark,
					problem='{0} configuration does not exist'.format(subdir))
		else:
			hadsomedirs = True
	return hadsomedirs, hadproblem


def check_config(d, theme, data, context, echoerr):
	if len(context) == 4:
		ext = context[-2][0]
	else:
		# local_themes
		ext = context[-3][0]
	if ext not in data['configs'][d] or theme not in data['configs'][d][ext]:
		echoerr(context='Error while loading {0} from {1} extension configuration'.format(d[:-1], ext),
				problem='failed to find configuration file {0}/{1}/{2}.json'.format(d, ext, theme),
				problem_mark=theme.mark)
		return True, False, True
	return True, False, False


divider_spec = Spec().type(unicode).len('le', 3,
					lambda value: 'Divider {0!r} is too large!'.format(value)).copy
divside_spec = Spec(
	hard=divider_spec(),
	soft=divider_spec(),
).copy
colorscheme_spec = Spec().type(unicode).func(lambda *args: check_config('colorschemes', *args)).copy
theme_spec = Spec().type(unicode).func(lambda *args: check_config('themes', *args)).copy
main_spec = (Spec(
	common=Spec(
		dividers=Spec(
			left=divside_spec(),
			right=divside_spec(),
		),
		spaces=Spec().unsigned().cmp('le', 2,
							lambda value: 'Are you sure you need such a big ({0}) number of spaces?'.format(value)),
		term_truecolor=Spec().type(bool).optional(),
		# Python is capable of loading from zip archives. Thus checking path 
		# only for existence of the path, not for it being a directory
		paths=Spec().list((lambda value, *args: (True, True, not os.path.exists(os.path.expanduser(value.value)))),
					lambda value: 'path does not exist: {0}'.format(value)).optional(),
		log_file=Spec().type(str).func(lambda value, *args: (True, True, not os.path.isdir(os.path.dirname(os.path.expanduser(value)))),
						lambda value: 'directory does not exist: {0}'.format(os.path.dirname(value))).optional(),
		log_level=Spec().re('^[A-Z]+$').func(lambda value, *args: (True, True, not hasattr(logging, value)),
										lambda value: 'unknown debugging level {0}'.format(value)).optional(),
		log_format=Spec().type(str).optional(),
		interval=Spec().either(Spec().cmp('gt', 0.0), Spec().type(type(None))).optional(),
		reload_config=Spec().type(bool).optional(),
	).context_message('Error while loading common configuration (key {key})'),
	ext=Spec(
		vim=Spec(
			colorscheme=colorscheme_spec(),
			theme=theme_spec(),
			local_themes=Spec()
				.unknown_spec(lambda *args: check_matcher_func('vim', *args), theme_spec())
		).optional(),
		ipython=Spec(
			colorscheme=colorscheme_spec(),
			theme=theme_spec(),
			local_themes=Spec(
				in2=theme_spec(),
				out=theme_spec(),
				rewrite=theme_spec(),
			),
		).optional(),
	).unknown_spec(check_ext,
				Spec(
					colorscheme=colorscheme_spec(),
					theme=theme_spec(),
				))
	.context_message('Error while loading extensions configuration (key {key})'),
).context_message('Error while loading main configuration'))

term_color_spec = Spec().unsigned().cmp('le', 255).copy
true_color_spec = Spec().re('^[0-9a-fA-F]{6}$',
						lambda value: '"{0}" is not a six-digit hexadecimal unsigned integer written as a string'.format(value)).copy
colors_spec = (Spec(
	colors=Spec().unknown_spec(
		Spec().ident(),
		Spec().either(
			Spec().tuple(term_color_spec(), true_color_spec()),
			term_color_spec()))
	.context_message('Error while checking colors (key {key})'),
	gradients=Spec().unknown_spec(
		Spec().ident(),
		Spec().tuple(
			Spec().len('gt', 1).list(term_color_spec()),
			Spec().len('gt', 1).list(true_color_spec()).optional(),
		)
	).context_message('Error while checking gradients (key {key})'),
).context_message('Error while loading colors configuration'))


def check_color(color, data, context, echoerr):
	if color not in data['colors_config'].get('colors', {}) and color not in data['colors_config'].get('gradients', {}):
		echoerr(context='Error while checking highlight group in colorscheme (key {key})'.format(key=context_key(context)),
				problem='found unexistent color or gradient {0}'.format(color),
				problem_mark=color.mark)
		return True, False, True
	return True, False, False


def check_translated_group_name(group, data, context, echoerr):
	if group not in context[0][1].get('groups', {}):
		echoerr(context='Error while checking translated group in colorscheme (key {key})'.format(key=context_key(context)),
				problem='translated group {0} is not in main groups dictionary'.format(group),
				problem_mark=group.mark)
		return True, False, True
	return True, False, False


color_spec = Spec().type(unicode).func(check_color).copy
name_spec = Spec().type(unicode).len('gt', 0).optional().copy
group_spec = Spec(
	fg=color_spec(),
	bg=color_spec(),
	attr=Spec().list(Spec().type(unicode).oneof(set(('bold', 'italic', 'underline')))).optional(),
).copy
group_name_spec = Spec().re('^\w+(?::\w+)?$').copy
groups_spec = Spec().unknown_spec(
	group_name_spec(),
	group_spec(),
).context_message('Error while loading groups (key {key})').copy
colorscheme_spec = (Spec(
	name=name_spec(),
	groups=groups_spec(),
).context_message('Error while loading coloscheme'))
vim_mode_spec = Spec().oneof(set(list(vim_modes) + ['nc'])).copy
vim_colorscheme_spec = (Spec(
	name=name_spec(),
	groups=groups_spec(),
	mode_translations=Spec().unknown_spec(
		vim_mode_spec(),
		Spec(
			colors=Spec().unknown_spec(
				color_spec(),
				color_spec(),
			).optional(),
			groups=Spec().unknown_spec(
				group_name_spec().func(check_translated_group_name),
				group_spec(),
			).optional(),
		),
	).context_message('Error while loading mode translations (key {key})'),
).context_message('Error while loading vim colorscheme'))
shell_mode_spec = Spec().re('^(?:[\w\-]+|\.safe)$').copy
shell_colorscheme_spec = (Spec(
	name=name_spec(),
	groups=groups_spec(),
	mode_translations=Spec().unknown_spec(
		shell_mode_spec(),
		Spec(
			colors=Spec().unknown_spec(
				color_spec(),
				color_spec(),
			).optional(),
			groups=Spec().unknown_spec(
				group_name_spec().func(check_translated_group_name),
				group_spec(),
			).optional(),
		),
	).context_message('Error while loading mode translations (key {key})'),
).context_message('Error while loading shell colorscheme'))


generic_keys = set(('exclude_modes', 'include_modes', 'width', 'align', 'name', 'draw_soft_divider', 'draw_hard_divider', 'priority', 'after', 'before'))
type_keys = {
		'function': set(('args', 'module', 'draw_inner_divider')),
		'string': set(('contents', 'type', 'highlight_group', 'divider_highlight_group')),
		'filler': set(('type', 'highlight_group', 'divider_highlight_group')),
		}
required_keys = {
		'function': set(),
		'string': set(('contents',)),
		'filler': set(),
		}
function_keys = set(('args', 'module'))
highlight_keys = set(('highlight_group', 'name'))


def check_key_compatibility(segment, data, context, echoerr):
	segment_type = segment.get('type', 'function')

	if segment_type not in type_keys:
		echoerr(context='Error while checking segments (key {key})'.format(key=context_key(context)),
				problem='found segment with unknown type {0}'.format(segment_type),
				problem_mark=segment_type.mark)
		return False, False, True

	hadproblem = False

	keys = set(segment)
	if not ((keys - generic_keys) < type_keys[segment_type]):
		unknown_keys = keys - generic_keys - type_keys[segment_type]
		echoerr(context='Error while checking segments (key {key})'.format(key=context_key(context)),
				context_mark=context[-1][1].mark,
				problem='found keys not used with the current segment type: {0}'.format(
					list_sep.join(unknown_keys)),
				problem_mark=list(unknown_keys)[0].mark)
		hadproblem = True

	if not (keys > required_keys[segment_type]):
		missing_keys = required_keys[segment_type] - keys
		echoerr(context='Error while checking segments (key {key})'.format(key=context_key(context)),
				context_mark=context[-1][1].mark,
				problem='found missing required keys: {0}'.format(
					list_sep.join(missing_keys)))
		hadproblem = True

	if not (segment_type == 'function' or (keys & highlight_keys)):
		echoerr(context='Error while checking segments (key {key})'.format(key=context_key(context)),
				context_mark=context[-1][1].mark,
				problem='found missing keys required to determine highlight group. Either highlight_group or name key must be present')
		hadproblem = True

	return True, False, hadproblem


def check_segment_module(module, data, context, echoerr):
	with WithPath(data['import_paths']):
		try:
			__import__(unicode(module))
		except ImportError as e:
			if echoerr.logger.level >= logging.DEBUG:
				echoerr.logger.exception(e)
			echoerr(context='Error while checking segments (key {key})'.format(key=context_key(context)),
					problem='failed to import module {0}'.format(module),
					problem_mark=module.mark)
			return True, False, True
	return True, False, False


def check_full_segment_data(segment, data, context, echoerr):
	if 'name' not in segment:
		return True, False, False

	ext = data['ext']
	theme_segment_data = context[0][1].get('segment_data', {})
	top_theme_name = data['main_config'].get('ext', {}).get(ext, {}).get('theme', None)
	if not top_theme_name or data['theme'] == top_theme_name:
		top_segment_data = {}
	else:
		top_segment_data = data['ext_theme_configs'].get(top_theme_name, {}).get('segment_data', {})

	names = [segment['name']]
	if segment.get('type', 'function') == 'function':
		module = segment.get('module', context[0][1].get('default_module', 'powerline.segments.' + ext))
		names.insert(0, unicode(module) + '.' + unicode(names[0]))

	segment_copy = segment.copy()

	for key in ('before', 'after', 'args', 'contents'):
		if key not in segment_copy:
			for segment_data in [theme_segment_data, top_segment_data]:
				for name in names:
					try:
						val = segment_data[name][key]
						# HACK to keep marks
						l = list(segment_data[name])
						k = l[l.index(key)]
						segment_copy[k] = val
					except KeyError:
						pass

	return check_key_compatibility(segment_copy, data, context, echoerr)


def import_segment(name, data, context, echoerr, module=None):
	if not module:
		module = context[-2][1].get('module', context[0][1].get('default_module', 'powerline.segments.' + data['ext']))

	with WithPath(data['import_paths']):
		try:
			func = getattr(__import__(unicode(module), fromlist=[unicode(name)]), unicode(name))
		except ImportError:
			echoerr(context='Error while checking segments (key {key})'.format(key=context_key(context)),
					problem='failed to import module {0}'.format(module),
					problem_mark=module.mark)
			return None
		except AttributeError:
			echoerr(context='Error while loading segment function (key {key})'.format(key=context_key(context)),
					problem='failed to load function {0} from module {1}'.format(name, module),
					problem_mark=name.mark)
			return None

	if not callable(func):
		echoerr(context='Error while checking segments (key {key})'.format(key=context_key(context)),
				problem='imported "function" {0} from module {1} is not callable'.format(name, module),
				problem_mark=module.mark)
		return None

	return func


def check_segment_name(name, data, context, echoerr):
	ext = data['ext']
	if context[-2][1].get('type', 'function') == 'function':
		func = import_segment(name, data, context, echoerr)

		if not func:
			return True, False, True

		hl_groups = []
		divider_hl_group = None

		if func.__doc__:
			H_G_USED_STR = 'Highlight groups used: '
			D_H_G_USED_STR = 'Divider highlight group used: '
			for line in func.__doc__.split('\n'):
				if H_G_USED_STR in line:
					hl_groups.append(line[line.index(H_G_USED_STR) + len(H_G_USED_STR):])
				elif D_H_G_USED_STR in line:
					divider_hl_group = line[line.index(D_H_G_USED_STR) + len(D_H_G_USED_STR) + 2:-3]

		hadproblem = False

		if divider_hl_group:
			r = hl_exists(divider_hl_group, data, context, echoerr, allow_gradients=True)
			if r:
				echoerr(context='Error while checking theme (key {key})'.format(key=context_key(context)),
						problem='found highlight group {0} not defined in the following colorschemes: {1}\n(Group name was obtained from function documentation.)'.format(
							divider_hl_group, list_sep.join(r)),
						problem_mark=name.mark)
				hadproblem = True

		if hl_groups:
			greg = re.compile(r'``([^`]+)``( \(gradient\))?')
			hl_groups = [[greg.match(subs).groups() for subs in s.split(' or ')] for s in (list_sep.join(hl_groups)).split(', ')]
			for required_pack in hl_groups:
				rs = [hl_exists(hl_group, data, context, echoerr, allow_gradients=('force' if gradient else False))
						for hl_group, gradient in required_pack]
				if all(rs):
					echoerr(context='Error while checking theme (key {key})'.format(key=context_key(context)),
							problem='found highlight groups list ({0}) with all groups not defined in some colorschemes\n(Group names were taken from function documentation.)'.format(
								list_sep.join((h[0] for h in required_pack))),
							problem_mark=name.mark)
					for r, h in zip(rs, required_pack):
						echoerr(context='Error while checking theme (key {key})'.format(key=context_key(context)),
								problem='found highlight group {0} not defined in the following colorschemes: {1}'.format(
								h[0], list_sep.join(r)))
					hadproblem = True
		else:
			r = hl_exists(name, data, context, echoerr, allow_gradients=True)
			if r:
				echoerr(context='Error while checking theme (key {key})'.format(key=context_key(context)),
						problem='found highlight group {0} not defined in the following colorschemes: {1}\n(If not specified otherwise in documentation, highlight group for function segments\nis the same as the function name.)'.format(
							name, list_sep.join(r)),
						problem_mark=name.mark)
				hadproblem = True

		return True, False, hadproblem
	else:
		if name not in context[0][1].get('segment_data', {}):
			top_theme_name = data['main_config'].get('ext', {}).get(ext, {}).get('theme', None)
			if data['theme'] == top_theme_name:
				top_theme = {}
			else:
				top_theme = data['ext_theme_configs'].get(top_theme_name, {})
			if name not in top_theme.get('segment_data', {}):
				echoerr(context='Error while checking segments (key {key})'.format(key=context_key(context)),
						problem='found useless use of name key (such name is not present in theme/segment_data)',
						problem_mark=name.mark)

	return True, False, False


def hl_exists(hl_group, data, context, echoerr, allow_gradients=False):
	ext = data['ext']
	if ext not in data['colorscheme_configs']:
		# No colorschemes. Error was already reported, no need to report it 
		# twice
		return []
	r = []
	for colorscheme, cconfig in data['colorscheme_configs'][ext].items():
		if hl_group not in cconfig.get('groups', {}):
			r.append(colorscheme)
		elif not allow_gradients or allow_gradients == 'force':
			group_config = cconfig['groups'][hl_group]
			hadgradient = False
			for ckey in ('fg', 'bg'):
				color = group_config.get(ckey)
				if not color:
					# No color. Error was already reported.
					continue
				# Gradients are only allowed for function segments. Note that 
				# whether *either* color or gradient exists should have been 
				# already checked
				hascolor = color in data['colors_config'].get('colors', {})
				hasgradient = color in data['colors_config'].get('gradients', {})
				if hasgradient:
					hadgradient = True
				if allow_gradients is False and not hascolor and hasgradient:
					echoerr(context='Error while checking highlight group in theme (key {key})'.format(key=context_key(context)),
							context_mark=getattr(hl_group, 'mark', None),
							problem='group {0} is using gradient {1} instead of a color'.format(hl_group, color),
							problem_mark=color.mark)
					r.append(colorscheme)
					continue
			if allow_gradients == 'force' and not hadgradient:
					echoerr(context='Error while checking highlight group in theme (key {key})'.format(key=context_key(context)),
							context_mark=getattr(hl_group, 'mark', None),
							problem='group {0} should have at least one gradient color, but it has no'.format(hl_group),
							problem_mark=group_config.mark)
					r.append(colorscheme)
	return r


def check_highlight_group(hl_group, data, context, echoerr):
	r = hl_exists(hl_group, data, context, echoerr)
	if r:
		echoerr(context='Error while checking theme (key {key})'.format(key=context_key(context)),
				problem='found highlight group {0} not defined in the following colorschemes: {1}'.format(
					hl_group, list_sep.join(r)),
				problem_mark=hl_group.mark)
		return True, False, True
	return True, False, False


def check_highlight_groups(hl_groups, data, context, echoerr):
	rs = [hl_exists(hl_group, data, context, echoerr) for hl_group in hl_groups]
	if all(rs):
		echoerr(context='Error while checking theme (key {key})'.format(key=context_key(context)),
				problem='found highlight groups list ({0}) with all groups not defined in some colorschemes'.format(
					list_sep.join((unicode(h) for h in hl_groups))),
				problem_mark=hl_groups.mark)
		for r, hl_group in zip(rs, hl_groups):
			echoerr(context='Error while checking theme (key {key})'.format(key=context_key(context)),
					problem='found highlight group {0} not defined in the following colorschemes: {1}'.format(
					hl_group, list_sep.join(r)),
					problem_mark=hl_group.mark)
		return True, False, True
	return True, False, False


def check_segment_data_key(key, data, context, echoerr):
	ext = data['ext']
	top_theme_name = data['main_config'].get('ext', {}).get(ext, {}).get('theme', None)
	is_top_theme = (data['theme'] == top_theme_name)
	if is_top_theme:
		themes = data['ext_theme_configs'].values()
	else:
		themes = [context[0][1]]

	for theme in themes:
		for segments in theme.get('segments', {}).values():
			found = False
			for segment in segments:
				if 'name' in segment:
					if key == segment['name']:
						found = True
					module = segment.get('module', theme.get('default_module', 'powerline.segments.' + ext))
					if key == unicode(module) + '.' + unicode(segment['name']):
						found = True
			if found:
				break
		if found:
			break
	else:
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


def check_args_variant(segment, args, data, context, echoerr):
	argspec = getconfigargspec(segment)
	present_args = set(args)
	all_args = set(argspec.args)
	required_args = set(argspec.args[:-len(argspec.defaults)])

	hadproblem = False

	if required_args - present_args:
		echoerr(context='Error while checking segment arguments (key {key})'.format(key=context_key(context)),
				context_mark=args.mark,
				problem='some of the required keys are missing: {0}'.format(list_sep.join(required_args - present_args)))
		hadproblem = True

	if not all_args >= present_args:
		echoerr(context='Error while checking segment arguments (key {key})'.format(key=context_key(context)),
				context_mark=args.mark,
				problem='found unknown keys: {0}'.format(list_sep.join(present_args - all_args)),
				problem_mark=next(iter(present_args - all_args)).mark)
		hadproblem = True

	if isinstance(segment, ThreadedSegment):
		for key in set(threaded_args_specs) & present_args:
			proceed, khadproblem = threaded_args_specs[key].match(args[key], args.mark, data, context + ((key, args[key]),), echoerr)
			if khadproblem:
				hadproblem = True
			if not proceed:
				return hadproblem

	return hadproblem


def check_args(get_segment_variants, args, data, context, echoerr):
	new_echoerr = DelayedEchoErr(echoerr)
	count = 0
	hadproblem = False
	for segment in get_segment_variants(data, context, new_echoerr):
		count += 1
		shadproblem = check_args_variant(segment, args, data, context, echoerr)
		if shadproblem:
			hadproblem = True

	if not count:
		hadproblem = True
		if new_echoerr:
			new_echoerr.echo_all()
		else:
			echoerr(context='Error while checking segment arguments (key {key})'.format(key=context_key(context)),
					context_mark=context[-2][1].mark,
					problem='no suitable segments found')

	return True, False, hadproblem


def get_one_segment_variant(data, context, echoerr):
	name = context[-2][1].get('name')
	if name:
		func = import_segment(name, data, context, echoerr)
		if func:
			yield func


def get_all_possible_segments(data, context, echoerr):
	name = context[-2][0]
	module, name = name.rpartition('.')[::2]
	if module:
		func = import_segment(name, data, context, echoerr, module=module)
		if func:
			yield func
	else:
		for theme_config in data['ext_theme_configs'].values():
			for segments in theme_config.get('segments', {}).values():
				for segment in segments:
					if segment.get('type', 'function') == 'function':
						module = segment.get('module', context[0][1].get('default_module', 'powerline.segments.' + data['ext']))
						func = import_segment(name, data, context, echoerr, module=module)
						if func:
							yield func


args_spec = Spec(
	pl=Spec().error('pl object must be set by powerline').optional(),
	segment_info=Spec().error('Segment info dictionary must be set by powerline').optional(),
).unknown_spec(Spec(), Spec()).optional().copy
highlight_group_spec = Spec().type(unicode).copy
segment_module_spec = Spec().type(unicode).func(check_segment_module).optional().copy
segments_spec = Spec().optional().list(
	Spec(
		type=Spec().oneof(type_keys).optional(),
		name=Spec().re('^[a-zA-Z_]\w+$').func(check_segment_name).optional(),
		exclude_modes=Spec().list(vim_mode_spec()).optional(),
		include_modes=Spec().list(vim_mode_spec()).optional(),
		draw_hard_divider=Spec().type(bool).optional(),
		draw_soft_divider=Spec().type(bool).optional(),
		draw_inner_divider=Spec().type(bool).optional(),
		module=segment_module_spec(),
		priority=Spec().type(int, float, type(None)).optional(),
		after=Spec().type(unicode).optional(),
		before=Spec().type(unicode).optional(),
		width=Spec().either(Spec().unsigned(), Spec().cmp('eq', 'auto')).optional(),
		align=Spec().oneof(set('lr')).optional(),
		args=args_spec().func(lambda *args, **kwargs: check_args(get_one_segment_variant, *args, **kwargs)),
		contents=Spec().type(unicode).optional(),
		highlight_group=Spec().list(
			highlight_group_spec().re('^(?:(?!:divider$).)+$',
						lambda value: 'it is recommended that only divider highlight group names end with ":divider"')
		).func(check_highlight_groups).optional(),
		divider_highlight_group=highlight_group_spec().func(check_highlight_group).re(':divider$',
			lambda value: 'it is recommended that divider highlight group names end with ":divider"').optional(),
	).func(check_full_segment_data),
).copy
theme_spec = (Spec(
	default_module=segment_module_spec(),
	segment_data=Spec().unknown_spec(
		Spec().func(check_segment_data_key),
		Spec(
			after=Spec().type(unicode).optional(),
			before=Spec().type(unicode).optional(),
			args=args_spec().func(lambda *args, **kwargs: check_args(get_all_possible_segments, *args, **kwargs)),
			contents=Spec().type(unicode).optional(),
		),
	).optional().context_message('Error while loading segment data (key {key})'),
	segments=Spec(
		left=segments_spec().context_message('Error while loading segments from left side (key {key})'),
		right=segments_spec().context_message('Error while loading segments from right side (key {key})'),
	).func(
		lambda value, *args: (True, True, not (('left' in value) or ('right' in value))),
		lambda value: 'segments dictionary must contain either left, right or both keys'
	).context_message('Error while loading segments (key {key})'),
).context_message('Error while loading theme'))


def check(path=None, debug=False):
	search_paths = [path] if path else Powerline.get_config_paths()

	logger = logging.getLogger('powerline-lint')
	logger.setLevel(logging.DEBUG if debug else logging.ERROR)
	logger.addHandler(logging.StreamHandler())

	ee = EchoErr(echoerr, logger)

	dirs = {
		'themes': defaultdict(lambda: []),
		'colorschemes': defaultdict(lambda: [])
	}
	for path in reversed(search_paths):
		for subdir in ('themes', 'colorschemes'):
			d = os.path.join(path, subdir)
			if os.path.isdir(d):
				for ext in os.listdir(d):
					extd = os.path.join(d, ext)
					if os.path.isdir(extd):
						dirs[subdir][ext].append(extd)
			elif os.path.exists(d):
				hadproblem = True
				sys.stderr.write('Path {0} is supposed to be a directory, but it is not\n'.format(d))

	configs = {
		'themes': defaultdict(lambda: {}),
		'colorschemes': defaultdict(lambda: {})
	}
	for subdir in ('themes', 'colorschemes'):
		for ext in dirs[subdir]:
			for d in dirs[subdir][ext]:
				for config in os.listdir(d):
					if os.path.isdir(os.path.join(d, config)):
						dirs[subdir][ext].append(os.path.join(d, config))
					elif config.endswith('.json'):
						configs[subdir][ext][config[:-5]] = os.path.join(d, config)

	diff = set(configs['themes']) ^ set(configs['colorschemes'])
	if diff:
		hadproblem = True
		for ext in diff:
			sys.stderr.write('{0} extension {1} present only in {2}\n'.format(
				ext,
				'configuration' if (ext in dirs['themes'] and ext in dirs['colorschemes']) else 'directory',
				'themes' if ext in configs['themes'] else 'colorschemes',
			))

	lhadproblem = [False]

	def load_config(stream):
		r, hadproblem = load(stream)
		if hadproblem:
			lhadproblem[0] = True
		return r

	hadproblem = False
	try:
		main_config = load_json_config(find_config_file(search_paths, 'config'), load=load_config, open_file=open_file)
	except IOError:
		main_config = {}
		sys.stderr.write('\nConfiguration file not found: config.json\n')
		hadproblem = True
	except MarkedError as e:
		main_config = {}
		sys.stderr.write(str(e) + '\n')
		hadproblem = True
	else:
		if main_spec.match(main_config, data={'configs': configs}, context=(('', main_config),), echoerr=ee)[1]:
			hadproblem = True

	import_paths = [os.path.expanduser(path) for path in main_config.get('common', {}).get('paths', [])]

	try:
		colors_config = load_json_config(find_config_file(search_paths, 'colors'), load=load_config, open_file=open_file)
	except IOError:
		colors_config = {}
		sys.stderr.write('\nConfiguration file not found: colors.json\n')
		hadproblem = True
	except MarkedError as e:
		colors_config = {}
		sys.stderr.write(str(e) + '\n')
		hadproblem = True
	else:
		if colors_spec.match(colors_config, context=(('', colors_config),), echoerr=ee)[1]:
			hadproblem = True

	if lhadproblem[0]:
		hadproblem = True

	colorscheme_configs = defaultdict(lambda: {})
	for ext in configs['colorschemes']:
		data = {'ext': ext, 'colors_config': colors_config}
		for colorscheme, cfile in configs['colorschemes'][ext].items():
			with open_file(cfile) as config_file_fp:
				try:
					config, lhadproblem = load(config_file_fp)
				except MarkedError as e:
					sys.stderr.write(str(e) + '\n')
					hadproblem = True
					continue
			if lhadproblem:
				hadproblem = True
			colorscheme_configs[ext][colorscheme] = config
			if ext == 'vim':
				spec = vim_colorscheme_spec
			elif ext == 'shell':
				spec = shell_colorscheme_spec
			else:
				spec = colorscheme_spec
			if spec.match(config, context=(('', config),), data=data, echoerr=ee)[1]:
				hadproblem = True

	theme_configs = defaultdict(lambda: {})
	for ext in configs['themes']:
		for theme, sfile in configs['themes'][ext].items():
			with open_file(sfile) as config_file_fp:
				try:
					config, lhadproblem = load(config_file_fp)
				except MarkedError as e:
					sys.stderr.write(str(e) + '\n')
					hadproblem = True
					continue
			if lhadproblem:
				hadproblem = True
			theme_configs[ext][theme] = config
	for ext, configs in theme_configs.items():
		data = {'ext': ext, 'colorscheme_configs': colorscheme_configs, 'import_paths': import_paths,
				'main_config': main_config, 'ext_theme_configs': configs, 'colors_config': colors_config}
		for theme, config in configs.items():
			data['theme'] = theme
			if theme_spec.match(config, context=(('', config),), data=data, echoerr=ee)[1]:
				hadproblem = True
	return hadproblem
