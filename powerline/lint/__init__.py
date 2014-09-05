# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import itertools
import sys
import os
import re
import logging

from collections import defaultdict
from copy import copy
from functools import partial

from powerline.lint.markedjson import load
from powerline import generate_config_finder, get_config_paths, load_config
from powerline.lib.config import ConfigLoader
from powerline.lint.markedjson.error import echoerr, MarkedError, Mark
from powerline.lint.markedjson.markedvalue import MarkedUnicode
from powerline.segments.vim import vim_modes
from powerline.lint.inspect import getconfigargspec
from powerline.lib.threaded import ThreadedSegment
from powerline.lib import mergedicts_copy
from powerline.lib.unicode import unicode


def open_file(path):
	return open(path, 'rb')


EMPTYTUPLE = tuple()


class JStr(unicode):
	def join(self, iterable):
		return super(JStr, self).join((unicode(item) for item in iterable))


key_sep = JStr('/')
list_sep = JStr(', ')


def init_context(config):
	return ((MarkedUnicode('', config.mark), config),)


def context_key(context):
	return key_sep.join((c[0] for c in context))


def havemarks(*args, **kwargs):
	origin = kwargs.get('origin', '')
	for i, v in enumerate(args):
		if not hasattr(v, 'mark'):
			raise AssertionError('Value #{0}/{1} ({2!r}) has no attribute `mark`'.format(origin, i, v))
		if isinstance(v, dict):
			for key, val in v.items():
				havemarks(key, val, origin=(origin + '[' + unicode(i) + ']/' + unicode(key)))
		elif isinstance(v, list):
			havemarks(*v, origin=(origin + '[' + unicode(i) + ']'))


def context_has_marks(context):
	for i, v in enumerate(context):
		havemarks(v[0], origin='context key')
		havemarks(v[1], origin='context val')


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

	__bool__ = __nonzero__


def new_context_item(key, value):
	return ((value.keydict[key], value[key]),)


class Spec(object):
	def __init__(self, **keys):
		self.specs = []
		self.keys = {}
		self.checks = []
		self.cmsg = ''
		self.isoptional = False
		self.uspecs = []
		self.ufailmsg = lambda key: 'found unknown key: {0}'.format(key)
		self.did_type = False
		self.update(**keys)

	def update(self, **keys):
		for k, v in keys.items():
			self.keys[k] = len(self.specs)
			self.specs.append(v)
		if self.keys and not self.did_type:
			self.type(dict)
			self.did_type = True
		return self

	def copy(self, copied=None):
		copied = copied or {}
		try:
			return copied[id(self)]
		except KeyError:
			instance = self.__class__()
			copied[id(self)] = instance
			return self.__class__()._update(self.__dict__, copied)

	def _update(self, d, copied):
		self.__dict__.update(d)
		self.keys = copy(self.keys)
		self.checks = copy(self.checks)
		self.uspecs = copy(self.uspecs)
		self.specs = [spec.copy(copied) for spec in self.specs]
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
		havemarks(value)
		if type(value.value) not in types:
			echoerr(
				context=self.cmsg.format(key=context_key(context)),
				context_mark=context_mark,
				problem='{0!r} must be a {1} instance, not {2}'.format(
					value,
					list_sep.join((t.__name__ for t in types)),
					type(value.value).__name__
				),
				problem_mark=value.mark
			)
			return False, True
		return True, False

	def check_func(self, value, context_mark, data, context, echoerr, func, msg_func):
		havemarks(value)
		proceed, echo, hadproblem = func(value, data, context, echoerr)
		if echo and hadproblem:
			echoerr(context=self.cmsg.format(key=context_key(context)),
			        context_mark=context_mark,
			        problem=msg_func(value),
			        problem_mark=value.mark)
		return proceed, hadproblem

	def check_list(self, value, context_mark, data, context, echoerr, item_func, msg_func):
		havemarks(value)
		i = 0
		hadproblem = False
		for item in value:
			havemarks(item)
			if isinstance(item_func, int):
				spec = self.specs[item_func]
				proceed, fhadproblem = spec.match(
					item,
					value.mark,
					data,
					context + ((MarkedUnicode('list item ' + unicode(i), item.mark), item),),
					echoerr
				)
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
		havemarks(value)
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
		havemarks(value)
		hadproblem = False
		for (i, item, spec) in zip(itertools.count(), value, self.specs[start:end]):
			proceed, ihadproblem = spec.match(
				item,
				value.mark,
				data,
				context + ((MarkedUnicode('tuple item ' + unicode(i), item.mark), item),),
				echoerr
			)
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
		msg_func = (
			msg_func
			or (lambda value: 'length of {0!r} is not {1} {2}'.format(
				value, self.cmp_msgs[comparison], cint))
		)
		self.checks.append((
			'check_func',
			(lambda value, *args: (True, True, not cmp_func(len(value), cint))),
			msg_func
		))
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
		self.checks.append((
			'check_func',
			(lambda value, *args: (True, True, not cmp_func(value.value, cint))),
			msg_func
		))
		return self

	def unsigned(self, msg_func=None):
		self.type(int)
		self.checks.append((
			'check_func',
			(lambda value, *args: (True, True, value < 0)),
			(lambda value: '{0} must be greater then zero'.format(value))
		))
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
		self.checks.append((
			'check_func',
			(lambda value, *args: (True, True, not compiled.match(value.value))),
			msg_func
		))
		return self

	def ident(self, msg_func=None):
		msg_func = (
			msg_func
			or (lambda value: 'String "{0}" is not an alphanumeric/underscore colon-separated identifier'.format(value))
		)
		return self.re('^\w+(?::\w+)?$', msg_func)

	def oneof(self, collection, msg_func=None):
		msg_func = msg_func or (lambda value: '"{0}" must be one of {1!r}'.format(value, list(collection)))
		self.checks.append((
			'check_func',
			(lambda value, *args: (True, True, value not in collection)),
			msg_func
		))
		return self

	def error(self, msg):
		self.checks.append((
			'check_func',
			(lambda *args: (True, True, True)),
			(lambda value: msg.format(value))
		))
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
		havemarks(value)
		proceed, hadproblem = self.match_checks(value, context_mark, data, context, echoerr)
		if proceed:
			if self.keys or self.uspecs:
				for key, vali in self.keys.items():
					valspec = self.specs[vali]
					if key in value:
						proceed, mhadproblem = valspec.match(
							value[key],
							value.mark,
							data,
							context + new_context_item(key, value),
							echoerr
						)
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
					havemarks(key)
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
								proceed, vhadproblem = valspec.match(
									value[key],
									value.mark,
									data,
									context + new_context_item(key, value),
									echoerr
								)
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
		        problem='loaded "function" {0} is not callable'.format(match_function),
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
	context_has_marks(context)
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
	context_has_marks(context)
	havemarks(theme)
	if theme not in data['configs']['top_themes']:
		echoerr(context='Error while checking extension configuration (key {key})'.format(key=context_key(context)),
		        context_mark=context[-2][0].mark,
		        problem='failed to find top theme {0}'.format(theme),
		        problem_mark=theme.mark)
		return True, False, True
	return True, False, False


function_name_re = '^(\w+\.)*[a-zA-Z_]\w*$'


divider_spec = Spec().type(unicode).len(
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


def check_color(color, data, context, echoerr):
	havemarks(color)
	if (color not in data['colors_config'].get('colors', {})
		and color not in data['colors_config'].get('gradients', {})):
		echoerr(
			context='Error while checking highlight group in colorscheme (key {key})'.format(
				key=context_key(context)),
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
					key=context_key(context)),
				problem='name {0} is not present in {1} {2} colorschemes: {3}'.format(
					group, tofind, ext, ', '.join(not_found)),
				problem_mark=group.mark
			)
	new_echoerr.echo_all()
	return True, False, hadproblem


color_spec = Spec().type(unicode).func(check_color).copy
name_spec = Spec().type(unicode).len('gt', 0).optional().copy
group_name_spec = Spec().ident().copy
group_spec = Spec().either(Spec(
	fg=color_spec(),
	bg=color_spec(),
	attr=Spec().list(Spec().type(unicode).oneof(set(('bold', 'italic', 'underline')))),
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
	'string': set(('contents', 'type', 'highlight_group', 'divider_highlight_group')),
	'segment_list': set(('function', 'segments', 'args', 'type')),
}
required_keys = {
	'function': set(('function',)),
	'string': set(()),
	'segment_list': set(('function', 'segments',)),
}
highlight_keys = set(('highlight_group', 'name'))


def check_key_compatibility(segment, data, context, echoerr):
	context_has_marks(context)
	havemarks(segment)
	segment_type = segment.get('type', MarkedUnicode('function', None))
	havemarks(segment_type)

	if segment_type not in type_keys:
		echoerr(context='Error while checking segments (key {key})'.format(key=context_key(context)),
		        problem='found segment with unknown type {0}'.format(segment_type),
		        problem_mark=segment_type.mark)
		return False, False, True

	hadproblem = False

	keys = set(segment)
	if not ((keys - generic_keys) < type_keys[segment_type]):
		unknown_keys = keys - generic_keys - type_keys[segment_type]
		echoerr(
			context='Error while checking segments (key {key})'.format(key=context_key(context)),
			context_mark=context[-1][1].mark,
			problem='found keys not used with the current segment type: {0}'.format(
				list_sep.join(unknown_keys)),
			problem_mark=list(unknown_keys)[0].mark
		)
		hadproblem = True

	if not (keys >= required_keys[segment_type]):
		missing_keys = required_keys[segment_type] - keys
		echoerr(
			context='Error while checking segments (key {key})'.format(key=context_key(context)),
			context_mark=context[-1][1].mark,
			problem='found missing required keys: {0}'.format(
				list_sep.join(missing_keys))
		)
		hadproblem = True

	if not (segment_type == 'function' or (keys & highlight_keys)):
		echoerr(
			context='Error while checking segments (key {key})'.format(key=context_key(context)),
			context_mark=context[-1][1].mark,
			problem=(
				'found missing keys required to determine highlight group. '
				'Either highlight_group or name key must be present'
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
			echoerr(context='Error while checking segments (key {key})'.format(key=context_key(context)),
			        problem='failed to import module {0}'.format(module),
			        problem_mark=module.mark)
			return True, False, True
	return True, False, False


def get_function_strings(function_name, context, ext):
	if '.' in function_name:
		module, function_name = function_name.rpartition('.')[::2]
	else:
		module = context[0][1].get(
			'default_module', MarkedUnicode('powerline.segments.' + ext, None))
	return module, function_name


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


def import_function(function_type, name, data, context, echoerr, module):
	context_has_marks(context)
	havemarks(name, module)

	with WithPath(data['import_paths']):
		try:
			func = getattr(__import__(str(module), fromlist=[str(name)]), str(name))
		except ImportError:
			echoerr(context='Error while checking segments (key {key})'.format(key=context_key(context)),
			        context_mark=name.mark,
			        problem='failed to import module {0}'.format(module),
			        problem_mark=module.mark)
			return None
		except AttributeError:
			echoerr(context='Error while loading {0} function (key {key})'.format(function_type, key=context_key(context)),
			        problem='failed to load function {0} from module {1}'.format(name, module),
			        problem_mark=name.mark)
			return None

	if not callable(func):
		echoerr(context='Error while checking segments (key {key})'.format(key=context_key(context)),
		        context_mark=name.mark,
		        problem='imported "function" {0} from module {1} is not callable'.format(name, module),
		        problem_mark=module.mark)
		return None

	return func


def import_segment(*args, **kwargs):
	return import_function('segment', *args, **kwargs)


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
					context='Error while checking theme (key {key})'.format(key=context_key(context)),
					problem=(
						'found highlight group {0} not defined in the following colorschemes: {1}\n'
						'(Group name was obtained from function documentation.)'
					).format(divider_hl_group, list_sep.join(r)),
					problem_mark=function_name.mark
				)
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
						context='Error while checking theme (key {key})'.format(key=context_key(context)),
						problem=(
							'found highlight groups list ({0}) with all groups not defined in some colorschemes\n'
							'(Group names were taken from function documentation.)'
						).format(list_sep.join((h[0] for h in required_pack))),
						problem_mark=function_name.mark
					)
					for r, h in zip(rs, required_pack):
						echoerr(
							context='Error while checking theme (key {key})'.format(key=context_key(context)),
							problem='found highlight group {0} not defined in the following colorschemes: {1}'.format(
								h[0], list_sep.join(r))
						)
					hadproblem = True
		else:
			r = hl_exists(function_name, data, context, echoerr, allow_gradients=True)
			if r:
				echoerr(
					context='Error while checking theme (key {key})'.format(key=context_key(context)),
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
				echoerr(context='Error while checking segments (key {key})'.format(key=context_key(context)),
				        problem='found useless use of name key (such name is not present in theme/segment_data)',
				        problem_mark=function_name.mark)

	return True, False, False


def hl_exists(hl_group, data, context, echoerr, allow_gradients=False):
	havemarks(hl_group)
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
			havemarks(group_config)
			hadgradient = False
			for ckey in ('fg', 'bg'):
				color = group_config.get(ckey)
				if not color:
					# No color. Error was already reported.
					continue
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
							key=context_key(context)),
						context_mark=hl_group.mark,
						problem='group {0} is using gradient {1} instead of a color'.format(hl_group, color),
						problem_mark=color.mark
					)
					r.append(colorscheme)
					continue
			if allow_gradients == 'force' and not hadgradient:
				echoerr(
					context='Error while checking highlight group in theme (key {key})'.format(
						key=context_key(context)),
					context_mark=hl_group.mark,
					problem='group {0} should have at least one gradient color, but it has no'.format(hl_group),
					problem_mark=group_config.mark
				)
				r.append(colorscheme)
	return r


def check_highlight_group(hl_group, data, context, echoerr):
	havemarks(hl_group)
	r = hl_exists(hl_group, data, context, echoerr)
	if r:
		echoerr(
			context='Error while checking theme (key {key})'.format(key=context_key(context)),
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
			context='Error while checking theme (key {key})'.format(key=context_key(context)),
			problem='found highlight groups list ({0}) with all groups not defined in some colorschemes'.format(
				list_sep.join((unicode(h) for h in hl_groups))),
			problem_mark=hl_groups.mark
		)
		for r, hl_group in zip(rs, hl_groups):
			echoerr(
				context='Error while checking theme (key {key})'.format(key=context_key(context)),
				problem='found highlight group {0} not defined in the following colorschemes: {1}'.format(
					hl_group, list_sep.join(r)),
				problem_mark=hl_group.mark
			)
		return True, False, True
	return True, False, False


def list_themes(data, context):
	theme_type = data['theme_type']
	ext = data['ext']
	main_theme_name = data['main_config'].get('ext', {}).get(ext, {}).get('theme', None)
	is_main_theme = (data['theme'] == main_theme_name)
	if theme_type == 'top':
		return list(itertools.chain(*[
			[(theme_ext, theme) for theme in theme_configs.values()]
			for theme_ext, theme_configs in data['theme_configs'].items()
		]))
	elif theme_type == 'main' or is_main_theme:
		return [(ext, theme) for theme in data['ext_theme_configs'].values()]
	else:
		return [(ext, context[0][1])]


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
			context='Error while checking segment arguments (key {key})'.format(key=context_key(context)),
			context_mark=args.mark,
			problem='some of the required keys are missing: {0}'.format(list_sep.join(required_args - present_args))
		)
		hadproblem = True

	if not all_args >= present_args:
		echoerr(context='Error while checking segment arguments (key {key})'.format(key=context_key(context)),
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
				context + new_context_item(key, args),
				echoerr
			)
			if khadproblem:
				hadproblem = True
			if not proceed:
				return hadproblem

	return hadproblem


def check_args(get_functions, args, data, context, echoerr):
	context_has_marks(context)
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
			echoerr(context='Error while checking segment arguments (key {key})'.format(key=context_key(context)),
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


def get_all_possible_functions(data, context, echoerr):
	name = context[-2][0]
	module, name = name.rpartition('.')[::2]
	if module:
		func = import_segment(name, data, context, echoerr, module=module)
		if func:
			yield func
	else:
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


args_spec = Spec(
	pl=Spec().error('pl object must be set by powerline').optional(),
	segment_info=Spec().error('Segment info dictionary must be set by powerline').optional(),
).unknown_spec(Spec(), Spec()).optional().copy
highlight_group_spec = Spec().type(unicode).copy
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
	after=Spec().type(unicode).optional(),
	before=Spec().type(unicode).optional(),
	width=Spec().either(Spec().unsigned(), Spec().cmp('eq', 'auto')).optional(),
	align=Spec().oneof(set('lr')).optional(),
	args=args_spec().func(lambda *args, **kwargs: check_args(get_one_segment_function, *args, **kwargs)),
	contents=Spec().type(unicode).optional(),
	highlight_group=Spec().list(
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
	after=Spec().type(unicode).optional(),
	before=Spec().type(unicode).optional(),
	display=Spec().type(bool).optional(),
	args=args_spec().func(lambda *args, **kwargs: check_args(get_all_possible_functions, *args, **kwargs)),
	contents=Spec().type(unicode).optional(),
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


def generate_json_config_loader(lhadproblem):
	def load_json_config(config_file_path, load=load, open_file=open_file):
		with open_file(config_file_path) as config_file_fp:
			r, hadproblem = load(config_file_fp)
			if hadproblem:
				lhadproblem[0] = True
			return r
	return load_json_config


def check(paths=None, debug=False):
	search_paths = paths or get_config_paths()
	find_config_files = generate_config_finder(lambda: search_paths)

	logger = logging.getLogger('powerline-lint')
	logger.setLevel(logging.DEBUG if debug else logging.ERROR)
	logger.addHandler(logging.StreamHandler())

	ee = EchoErr(echoerr, logger)

	lhadproblem = [False]
	load_json_config = generate_json_config_loader(lhadproblem)

	config_loader = ConfigLoader(run_once=True, load=load_json_config)

	paths = {
		'themes': defaultdict(lambda: []),
		'colorschemes': defaultdict(lambda: []),
		'top_colorschemes': [],
		'top_themes': [],
	}
	lists = {
		'colorschemes': set(),
		'themes': set(),
		'exts': set(),
	}
	for path in reversed(search_paths):
		for typ in ('themes', 'colorschemes'):
			d = os.path.join(path, typ)
			if os.path.isdir(d):
				for subp in os.listdir(d):
					extpath = os.path.join(d, subp)
					if os.path.isdir(extpath):
						lists['exts'].add(subp)
						paths[typ][subp].append(extpath)
					elif extpath.endswith('.json'):
						name = subp[:-5]
						if name != '__main__':
							lists[typ].add(name)
						paths['top_' + typ].append(extpath)
			else:
				hadproblem = True
				sys.stderr.write('Path {0} is supposed to be a directory, but it is not\n'.format(d))

	hadproblem = False

	configs = defaultdict(lambda: defaultdict(lambda: {}))
	for typ in ('themes', 'colorschemes'):
		for ext in paths[typ]:
			for d in paths[typ][ext]:
				for subp in os.listdir(d):
					if subp.endswith('.json'):
						name = subp[:-5]
						if name != '__main__':
							lists[typ].add(name)
							if name.startswith('__') or name.endswith('__'):
								hadproblem = True
								sys.stderr.write('File name is not supposed to start or end with “__”: {0}'.format(
									os.path.join(d, subp)
								))
						configs[typ][ext][name] = os.path.join(d, subp)
		for path in paths['top_' + typ]:
			name = os.path.basename(path)[:-5]
			configs['top_' + typ][name] = path

	diff = set(configs['colorschemes']) - set(configs['themes'])
	if diff:
		hadproblem = True
		for ext in diff:
			typ = 'colorschemes' if ext in configs['themes'] else 'themes'
			if not configs['top_' + typ] or typ == 'themes':
				sys.stderr.write('{0} extension {1} not present in {2}\n'.format(
					ext,
					'configuration' if (ext in paths['themes'] and ext in paths['colorschemes']) else 'directory',
					typ,
				))

	try:
		main_config = load_config('config', find_config_files, config_loader)
	except IOError:
		main_config = {}
		sys.stderr.write('\nConfiguration file not found: config.json\n')
		hadproblem = True
	except MarkedError as e:
		main_config = {}
		sys.stderr.write(str(e) + '\n')
		hadproblem = True
	else:
		if main_spec.match(
			main_config,
			data={'configs': configs, 'lists': lists},
			context=init_context(main_config),
			echoerr=ee
		)[1]:
			hadproblem = True

	import_paths = [os.path.expanduser(path) for path in main_config.get('common', {}).get('paths', [])]

	try:
		colors_config = load_config('colors', find_config_files, config_loader)
	except IOError:
		colors_config = {}
		sys.stderr.write('\nConfiguration file not found: colors.json\n')
		hadproblem = True
	except MarkedError as e:
		colors_config = {}
		sys.stderr.write(str(e) + '\n')
		hadproblem = True
	else:
		if colors_spec.match(colors_config, context=init_context(colors_config), echoerr=ee)[1]:
			hadproblem = True

	if lhadproblem[0]:
		hadproblem = True

	top_colorscheme_configs = {}
	data = {
		'ext': None,
		'top_colorscheme_configs': top_colorscheme_configs,
		'ext_colorscheme_configs': {},
		'colors_config': colors_config
	}
	for colorscheme, cfile in configs['top_colorschemes'].items():
		with open_file(cfile) as config_file_fp:
			try:
				config, lhadproblem = load(config_file_fp)
			except MarkedError as e:
				sys.stderr.write(str(e) + '\n')
				hadproblem = True
				continue
		if lhadproblem:
			hadproblem = True
		top_colorscheme_configs[colorscheme] = config
		data['colorscheme'] = colorscheme
		if top_colorscheme_spec.match(config, context=init_context(config), data=data, echoerr=ee)[1]:
			hadproblem = True

	ext_colorscheme_configs = defaultdict(lambda: {})
	for ext in configs['colorschemes']:
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
			ext_colorscheme_configs[ext][colorscheme] = config

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
			if spec.match(config, context=init_context(config), data=data, echoerr=ee)[1]:
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
			config = None
			for mconfig in mconfigs:
				if not mconfig:
					continue
				if config:
					config = mergedicts_copy(config, mconfig)
				else:
					config = mconfig
			colorscheme_configs[colorscheme] = config

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

	top_theme_configs = {}
	for top_theme, top_theme_file in configs['top_themes'].items():
		with open_file(top_theme_file) as config_file_fp:
			try:
				config, lhadproblem = load(config_file_fp)
			except MarkedError as e:
				sys.stderr.write(str(e) + '\n')
				hadproblem = True
				continue
			if lhadproblem:
				hadproblem = True
			top_theme_configs[top_theme] = config

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
			if spec.match(config, context=init_context(config), data=data, echoerr=ee)[1]:
				hadproblem = True

	for top_theme, config in top_theme_configs.items():
		data = {
			'ext': ext,
			'colorscheme_configs': colorscheme_configs,
			'import_paths': import_paths,
			'main_config': main_config,
			'theme_configs': theme_configs,
			'ext_theme_configs': configs,
			'colors_config': colors_config
		}
		data['theme_type'] = 'top'
		data['theme'] = top_theme
		if top_theme_spec.match(config, context=init_context(config), data=data, echoerr=ee)[1]:
			hadproblem = True

	return hadproblem
