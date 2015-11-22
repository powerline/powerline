# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import itertools
import re

from copy import copy

from powerline.lib.unicode import unicode
from powerline.lint.markedjson.error import echoerr, DelayedEchoErr, NON_PRINTABLE_STR
from powerline.lint.selfcheck import havemarks


NON_PRINTABLE_RE = re.compile(
	NON_PRINTABLE_STR.translate({
		ord('\t'): None,
		ord('\n'): None,
		0x0085: None,
	})
)


class Spec(object):
	'''Class that describes some JSON value

	In powerline it is only used to describe JSON values stored in powerline 
	configuration.

	:param dict keys:
		Dictionary that maps keys that may be present in the given JSON 
		dictionary to their descriptions. If this parameter is not empty it 
		implies that described value has dictionary type. Non-dictionary types 
		must be described using ``Spec()``: without arguments.

	.. note::
		Methods that create the specifications return ``self``, so calls to them 
		may be chained: ``Spec().type(unicode).re('^\w+$')``. This does not 
		apply to functions that *apply* specification like :py:meth`Spec.match`.

	.. note::
		Methods starting with ``check_`` return two values: first determines 
		whether caller should proceed on running other checks, second 
		determines whether there were any problems (i.e. whether error was 
		reported). One should not call these methods directly: there is 
		:py:meth:`Spec.match` method for checking values.

	.. note::
		In ``check_`` and ``match`` methods specifications are identified by 
		their indexes for the purpose of simplyfying :py:meth:`Spec.copy` 
		method.

	Some common parameters:

	``data``:
		Whatever data supplied by the first caller for checker functions. Is not 
		processed by :py:class:`Spec` methods in any fashion.
	``context``:
		:py:class:`powerline.lint.context.Context` instance, describes context 
		of the value. :py:class:`Spec` methods only use its ``.key`` methods for 
		error messages.
	``echoerr``:
		Callable that should be used to echo errors. Is supposed to take four 
		optional keyword arguments: ``problem``, ``problem_mark``, ``context``, 
		``context_mark``.
	``value``:
		Checked value.
	'''

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
		'''Describe additional keys that may be present in given JSON value

		If called with some keyword arguments implies that described value is 
		a dictionary. If called without keyword parameters it is no-op.

		:return: self.
		'''
		for k, v in keys.items():
			self.keys[k] = len(self.specs)
			self.specs.append(v)
		if self.keys and not self.did_type:
			self.type(dict)
			self.did_type = True
		return self

	def copy(self, copied=None):
		'''Deep copy the spec

		:param dict copied:
			Internal dictionary used for storing already copied values. This 
			parameter should not be used.

		:return: New :py:class:`Spec` object that is a deep copy of ``self``.
		'''
		copied = copied or {}
		try:
			return copied[id(self)]
		except KeyError:
			instance = self.__class__()
			copied[id(self)] = instance
			return self.__class__()._update(self.__dict__, copied)

	def _update(self, d, copied):
		'''Helper for the :py:meth:`Spec.copy` function

		Populates new instance with values taken from the old one.

		:param dict d:
			``__dict__`` of the old instance.
		:param dict copied:
			Storage for already copied values.
		'''
		self.__dict__.update(d)
		self.keys = copy(self.keys)
		self.checks = copy(self.checks)
		self.uspecs = copy(self.uspecs)
		self.specs = [spec.copy(copied) for spec in self.specs]
		return self

	def unknown_spec(self, keyfunc, spec):
		'''Define specification for non-static keys

		This method should be used if key names cannot be determined at runtime 
		or if a number of keys share identical spec (in order to not repeat it). 
		:py:meth:`Spec.match` method processes dictionary in the given order:

		* First it tries to use specifications provided at the initialization or 
		  by the :py:meth:`Spec.update` method.
		* If no specification for given key was provided it processes 
		  specifications from ``keyfunc`` argument in order they were supplied. 
		  Once some key matches specification supplied second ``spec`` argument 
		  is used to determine correctness of the value.

		:param Spec keyfunc:
			:py:class:`Spec` instance or a regular function that returns two 
			values (the same :py:meth:`Spec.match` returns). This argument is 
			used to match keys that were not provided at initialization or via 
			:py:meth:`Spec.update`.
		:param Spec spec:
			:py:class:`Spec` instance that will be used to check keys matched by 
			``keyfunc``.

		:return: self.
		'''
		if isinstance(keyfunc, Spec):
			self.specs.append(keyfunc)
			keyfunc = len(self.specs) - 1
		self.specs.append(spec)
		self.uspecs.append((keyfunc, len(self.specs) - 1))
		return self

	def unknown_msg(self, msgfunc):
		'''Define message which will be used when unknown key was found

		“Unknown” is a key that was not provided at the initialization and via 
		:py:meth:`Spec.update` and did not match any ``keyfunc`` proided via 
		:py:meth:`Spec.unknown_spec`.

		:param msgfunc:
			Function that takes that unknown key as an argument and returns the 
			message text. Text will appear at the top (start of the sentence).

		:return: self.
		'''
		self.ufailmsg = msgfunc
		return self

	def context_message(self, msg):
		'''Define message that describes context

		:param str msg:
			Message that describes context. Is written using the 
			:py:meth:`str.format` syntax and is expected to display keyword 
			parameter ``key``.

		:return: self.
		'''
		self.cmsg = msg
		for spec in self.specs:
			if not spec.cmsg:
				spec.context_message(msg)
		return self

	def check_type(self, value, context_mark, data, context, echoerr, types):
		'''Check that given value matches given type(s)

		:param tuple types:
			List of accepted types. Since :py:class:`Spec` is supposed to 
			describe JSON values only ``dict``, ``list``, ``unicode``, ``bool``, 
			``float`` and ``NoneType`` types make any sense.

		:return: proceed, hadproblem.
		'''
		havemarks(value)
		if type(value.value) not in types:
			echoerr(
				context=self.cmsg.format(key=context.key),
				context_mark=context_mark,
				problem='{0!r} must be a {1} instance, not {2}'.format(
					value,
					', '.join((t.__name__ for t in types)),
					type(value.value).__name__
				),
				problem_mark=value.mark
			)
			return False, True
		return True, False

	def check_func(self, value, context_mark, data, context, echoerr, func, msg_func):
		'''Check value using given function

		:param function func:
			Callable that should accept four positional parameters:

			#. checked value,
			#. ``data`` parameter with arbitrary data (supplied by top-level 
			   caller),
			#. current context and
			#. function used for echoing errors.

			This callable should return three values:

			#. determines whether ``check_func`` caller should proceed 
			   calling other checks,
			#. determines whether ``check_func`` should echo error on its own 
			   (it should be set to False if ``func`` echoes error itself) and
			#. determines whether function has found some errors in the checked 
			   value.

		:param function msg_func:
			Callable that takes checked value as the only positional parameter 
			and returns a string that describes the problem. Only useful for 
			small checker functions since it is ignored when second returned 
			value is false.

		:return: proceed, hadproblem.
		'''
		havemarks(value)
		proceed, echo, hadproblem = func(value, data, context, echoerr)
		if echo and hadproblem:
			echoerr(context=self.cmsg.format(key=context.key),
			        context_mark=context_mark,
			        problem=msg_func(value),
			        problem_mark=value.mark)
		return proceed, hadproblem

	def check_list(self, value, context_mark, data, context, echoerr, item_func, msg_func):
		'''Check that each value in the list matches given specification

		:param function item_func:
			Callable like ``func`` from :py:meth:`Spec.check_func`. Unlike 
			``func`` this callable is called for each value in the list and may 
			be a :py:class:`Spec` object index.
		:param func msg_func:
			Callable like ``msg_func`` from :py:meth:`Spec.check_func`. Should 
			accept one problematic item and is not used for :py:class:`Spec` 
			object indicies in ``item_func`` method.

		:return: proceed, hadproblem.
		'''
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
					context.enter_item('list item ' + unicode(i), item),
					echoerr
				)
			else:
				proceed, echo, fhadproblem = item_func(item, data, context, echoerr)
				if echo and fhadproblem:
					echoerr(context=self.cmsg.format(key=context.key + '/list item ' + unicode(i)),
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
		'''Check that given value matches one of the given specifications

		:param int start:
			First specification index.
		:param int end:
			Specification index that is greater by 1 then last specification 
			index.

		This method does not give an error if any specification from 
		``self.specs[start:end]`` is matched by the given value.
		'''
		havemarks(value)
		new_echoerr = DelayedEchoErr(
			echoerr,
			'One of the either variants failed. Messages from the first variant:',
			'messages from the next variant:'
		)

		hadproblem = False
		for spec in self.specs[start:end]:
			proceed, hadproblem = spec.match(value, value.mark, data, context, new_echoerr)
			new_echoerr.next_variant()
			if not proceed:
				break
			if not hadproblem:
				return True, False

		new_echoerr.echo_all()

		return False, hadproblem

	def check_tuple(self, value, context_mark, data, context, echoerr, start, end):
		'''Check that given value is a list with items matching specifications

		:param int start:
			First specification index.
		:param int end:
			Specification index that is greater by 1 then last specification 
			index.

		This method checks that each item in the value list matches 
		specification with index ``start + item_number``.
		'''
		havemarks(value)
		hadproblem = False
		for (i, item, spec) in zip(itertools.count(), value, self.specs[start:end]):
			proceed, ihadproblem = spec.match(
				item,
				value.mark,
				data,
				context.enter_item('tuple item ' + unicode(i), item),
				echoerr
			)
			if ihadproblem:
				hadproblem = True
			if not proceed:
				return False, hadproblem
		return True, hadproblem

	def check_printable(self, value, context_mark, data, context, echoerr, _):
		'''Check that given unicode string contains only printable characters
		'''
		hadproblem = False
		for match in NON_PRINTABLE_RE.finditer(value):
			hadproblem = True
			echoerr(
				context=self.cmsg.format(key=context.key),
				context_mark=value.mark,
				problem='found not printable character U+{0:04x} in a configuration string'.format(
					ord(match.group(0))),
				problem_mark=value.mark.advance_string(match.start() + 1)
			)
		return True, hadproblem

	def printable(self, *args):
		self.type(unicode)
		self.checks.append(('check_printable', args))
		return self

	def type(self, *args):
		'''Describe value that has one of the types given in arguments

		:param args:
			List of accepted types. Since :py:class:`Spec` is supposed to 
			describe JSON values only ``dict``, ``list``, ``unicode``, ``bool``, 
			``float`` and ``NoneType`` types make any sense.

		:return: self.
		'''
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
		'''Describe value that has given length

		:param str comparison:
			Type of the comparison. Valid values: ``le``, ``lt``, ``ge``, 
			``gt``, ``eq``.
		:param int cint:
			Integer with which length is compared.
		:param function msg_func:
			Function that should accept checked value and return message that 
			describes the problem with this value. Default value will emit 
			something like “length of ['foo', 'bar'] is not greater then 10”.

		:return: self.
		'''
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
		'''Describe value that is a number or string that has given property

		:param str comparison:
			Type of the comparison. Valid values: ``le``, ``lt``, ``ge``, 
			``gt``, ``eq``. This argument will restrict the number or string to 
			emit True on the given comparison.
		:param cint:
			Number or string with which value is compared. Type of this 
			parameter affects required type of the checked value: ``str`` and 
			``unicode`` types imply ``unicode`` values, ``float`` type implies 
			that value can be either ``int`` or ``float``, ``int`` type implies 
			``int`` value and for any other type the behavior is undefined.
		:param function msg_func:
			Function that should accept checked value and return message that 
			describes the problem with this value. Default value will emit 
			something like “10 is not greater then 10”.

		:return: self.
		'''
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
		'''Describe unsigned integer value

		:param function msg_func:
			Function that should accept checked value and return message that 
			describes the problem with this value.

		:return: self.
		'''
		self.type(int)
		self.checks.append((
			'check_func',
			(lambda value, *args: (True, True, value < 0)),
			(lambda value: '{0} must be greater then zero'.format(value))
		))
		return self

	def list(self, item_func, msg_func=None):
		'''Describe list with any number of elements, each matching given spec

		:param item_func:
			:py:class:`Spec` instance or a callable. Check out 
			:py:meth:`Spec.check_list` documentation for more details. Note that 
			in :py:meth:`Spec.check_list` description :py:class:`Spec` instance 
			is replaced with its index in ``self.specs``.
		:param function msg_func:
			Function that should accept checked value and return message that 
			describes the problem with this value. Default value will emit just 
			“failed check”, which is rather indescriptive.

		:return: self.
		'''
		self.type(list)
		if isinstance(item_func, Spec):
			self.specs.append(item_func)
			item_func = len(self.specs) - 1
		self.checks.append(('check_list', item_func, msg_func or (lambda item: 'failed check')))
		return self

	def tuple(self, *specs):
		'''Describe list with the given number of elements, each matching corresponding spec

		:param (Spec,) specs:
			List of specifications. Last element(s) in this list may be 
			optional. Each element in this list describes element with the same 
			index in the checked value. Check out :py:meth:`Spec.check_tuple` 
			for more details, but note that there list of specifications is 
			replaced with start and end indicies in ``self.specs``.

		:return: self.
		'''
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
			if min_len > 0:
				self.len('ge', min_len)
			self.len('le', max_len)

		start = len(self.specs)
		for i, spec in zip(itertools.count(), specs):
			self.specs.append(spec)
		self.checks.append(('check_tuple', start, len(self.specs)))
		return self

	def func(self, func, msg_func=None):
		'''Describe value that is checked by the given function

		Check out :py:meth:`Spec.check_func` documentation for more details.
		'''
		self.checks.append(('check_func', func, msg_func or (lambda value: 'failed check')))
		return self

	def re(self, regex, msg_func=None):
		'''Describe value that is a string that matches given regular expression

		:param str regex:
			Regular expression that should be matched by the value.
		:param function msg_func:
			Function that should accept checked value and return message that 
			describes the problem with this value. Default value will emit 
			something like “String "xyz" does not match "[a-f]+"”.

		:return: self.
		'''
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
		'''Describe value that is an identifier like ``foo:bar`` or ``foo``

		:param function msg_func:
			Function that should accept checked value and return message that 
			describes the problem with this value. Default value will emit 
			something like “String "xyz" is not an … identifier”.

		:return: self.
		'''
		msg_func = (
			msg_func
			or (lambda value: 'String "{0}" is not an alphanumeric/underscore colon-separated identifier'.format(value))
		)
		return self.re('^\w+(?::\w+)?$', msg_func)

	def oneof(self, collection, msg_func=None):
		'''Describe value that is equal to one of the value in the collection

		:param set collection:
			A collection of possible values.
		:param function msg_func:
			Function that should accept checked value and return message that 
			describes the problem with this value. Default value will emit 
			something like “"xyz" must be one of {'abc', 'def', 'ghi'}”.

		:return: self.
		'''
		msg_func = msg_func or (lambda value: '"{0}" must be one of {1!r}'.format(value, list(collection)))
		self.checks.append((
			'check_func',
			(lambda value, *args: (True, True, value not in collection)),
			msg_func
		))
		return self

	def error(self, msg):
		'''Describe value that must not be there

		Useful for giving more descriptive errors for some specific keys then 
		just “found unknown key: shutdown_event” or for forbidding certain 
		values when :py:meth:`Spec.unknown_spec` was used.

		:param str msg:
			Message given for the offending value. It is formatted using 
			:py:meth:`str.format` with the only positional parameter which is 
			the value itself.

		:return: self.
		'''
		self.checks.append((
			'check_func',
			(lambda *args: (True, True, True)),
			(lambda value: msg.format(value))
		))
		return self

	def either(self, *specs):
		'''Describes value that matches one of the given specs

		Check out :py:meth:`Spec.check_either` method documentation for more 
		details, but note that there a list of specs was replaced by start and 
		end indicies in ``self.specs``.

		:return: self.
		'''
		start = len(self.specs)
		self.specs.extend(specs)
		self.checks.append(('check_either', start, len(self.specs)))
		return self

	def optional(self):
		'''Mark value as optional

		Only useful for key specs in :py:meth:`Spec.__init__` and 
		:py:meth:`Spec.update` and some last supplied to :py:meth:`Spec.tuple`.

		:return: self.
		'''
		self.isoptional = True
		return self

	def required(self):
		'''Mark value as required

		Only useful for key specs in :py:meth:`Spec.__init__` and 
		:py:meth:`Spec.update` and some last supplied to :py:meth:`Spec.tuple`.

		.. note::
			Value is required by default. This method is only useful for 
			altering existing specification (or rather its copy).

		:return: self.
		'''
		self.isoptional = False
		return self

	def match_checks(self, *args):
		'''Process checks registered for the given value

		Processes only “top-level” checks: key specifications given using at the 
		initialization or via :py:meth:`Spec.unknown_spec` are processed by 
		:py:meth:`Spec.match`.

		:return: proceed, hadproblem.
		'''
		hadproblem = False
		for check in self.checks:
			proceed, chadproblem = getattr(self, check[0])(*(args + check[1:]))
			if chadproblem:
				hadproblem = True
			if not proceed:
				return False, hadproblem
		return True, hadproblem

	def match(self, value, context_mark=None, data=None, context=(), echoerr=echoerr):
		'''Check that given value matches this specification

		:return: proceed, hadproblem.
		'''
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
							context.enter_key(value, key),
							echoerr
						)
						if mhadproblem:
							hadproblem = True
						if not proceed:
							return False, hadproblem
					else:
						if not valspec.isoptional:
							hadproblem = True
							echoerr(context=self.cmsg.format(key=context.key),
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
									context.enter_key(value, key),
									echoerr
								)
								if vhadproblem:
									hadproblem = True
								break
						else:
							hadproblem = True
							if self.ufailmsg:
								echoerr(context=self.cmsg.format(key=context.key),
								        context_mark=None,
								        problem=self.ufailmsg(key),
								        problem_mark=key.mark)
		return True, hadproblem

	def __getitem__(self, key):
		'''Get specification for the given key
		'''
		return self.specs[self.keys[key]]

	def __setitem__(self, key, value):
		'''Set specification for the given key
		'''
		self.update(**{key: value})
