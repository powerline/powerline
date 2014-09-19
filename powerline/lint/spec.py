# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import itertools
import re

from copy import copy

from powerline.lib.unicode import unicode
from powerline.lint.markedjson.error import echoerr, DelayedEchoErr
from powerline.lint.markedjson.markedvalue import MarkedUnicode
from powerline.lint.selfcheck import havemarks
from powerline.lint.context import context_key, list_sep, new_context_item


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

	def required(self):
		self.isoptional = False
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

	def match(self, value, context_mark=None, data=None, context=(), echoerr=echoerr):
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

	def __getitem__(self, key):
		return self.specs[self.keys[key]]

	def __setitem__(self, key, value):
		return self.update(**{key: value})
