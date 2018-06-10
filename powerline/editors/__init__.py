# vim:fileencoding=utf-8:noet
'''Base module for editors support

Terminology (derived from Vim):

	Buffer
		Opened file (editor in-memory representation of file contents).
	Window
		Screen area displaying one buffer.
	Tabpage
		Collection of non-overlapping windows.
	Visual range
		Selection area.
	Column
		Byte offset from the start of the line.
	Virtual column
		Visual offset from the start of the line, counted in display cells.
'''

from __future__ import (unicode_literals, division, absolute_import, print_function)

from itertools import chain
from collections import namedtuple

from powerline.lib.dict import updated
from powerline.lib.unicode import unicode
from powerline.theme import requires_segment_info


def with_input(*reqs):
	'''Attach a list of requirements to the given object

	Each requirement is either a name (e.g. ``buffer_name``) or a pair 
	``({name}, {definition})`` where ``{name}`` is random name and 
	``{definition}`` is similar to definitions in one of the :py:class:`Editor` 
	subclasses.

	When requirement is a simple name it must be a name of the attribute of the 
	:py:class:`Editor` subclass of the editors which segment aims to support.
	'''
	def decorator(func):
		try:
			add_to = func.powerline_extensions['editor_input']
		except AttributeError:
			add_to = []
			func.powerline_extensions = {'editor_input': add_to}
		except KeyError:
			add_to = []
			func.powerline_extensions['editor_input'] = add_to
		add_to.extend(reqs)
		return requires_segment_info(func)

	return decorator


def with_list(req):
	'''Attach a requirement that computes to a list to a lister

	:param req:
		Requirement. Same as arguments in :py:func:`with_input`, but can only be 
		specified once. Only requirements that compute to a list are valid.
	'''
	def decorator(func):
		try:
			key_to = func.powerline_extensions
		except AttributeError:
			key_to = {}
			func.powerline_extensions = key_to
		key_to['editor_list'] = req

		return requires_segment_info(func)

	return decorator


def editor_input_addon(*reqs):
	'''Use list of requirements to construct dictionary returned by .startup()

	Using ``.startup()`` attribute is a way to construct requirements list like 
	supplied to :py:func:`with_input`, but based on segment configuration.
	'''
	return {'ext_editor_input': reqs}


def requires_buffer_access(func):
	'''Mark segment as editor segment which requires direct access to the buffer
	'''
	try:
		key_to = func.powerline_extensions
	except AttributeError:
		key_to = {}
		func.powerline_extensions = key_to
	key_to['editor_requires_buffer_access'] = True
	return func


class EditorObj(object):
	'''Base class for all editor expression objects

	Editor objects are needed to construct an abstract syntax tree that 
	represents expression used to be queried from the editor. Data that is 
	needed to transform such expressions into actual code can be found in 
	:py:attr:`Editor.edconverters` mapping, :py:meth:`Editor.toed` class 
	method is responsible for actual conversion.
	'''
	def ternary(self, if_true, if_false):
		'''Describe ternary operator

		:py:class:`EditorObj` instance for which this method is run becomes 
		a condition. First argument is result if condition is true, second is 
		result when condition is false.
		'''
		return EditorTernaryOp(self, if_true, if_false)

	def equals(self, other):
		'''Describe equality operator
		'''
		return EditorBinaryOp('==', self, toedobj(other))

	def startswith(self, start):
		'''Describe startswith
		'''
		return EditorBinaryOp('==', self[:len(start)], start)

	def matches(self, other):
		'''Describe regexp match operator

		``self`` describes a string being matched.
		'''
		return EditorBinaryOp('=~#', self, toedobj(other))

	def joined(self, other):
		'''Describe list join operator
		'''
		return EditorBinaryOp('+l', self, toedobj(other))

	def concat(self, other):
		'''Describe string concatenation operator
		'''
		return EditorBinaryOp('+s', self, toedobj(other))

	def __add__(self, other):
		return EditorBinaryOp('+', self, toedobj(other))

	def __sub__(self, other):
		return EditorBinaryOp('-', self, toedobj(other))

	def __mul__(self, other):
		return EditorBinaryOp('*', self, toedobj(other))

	def __div__(self, other):
		return EditorBinaryOp('/', self, toedobj(other))

	def __and__(self, other):
		return EditorBinaryOp('&', self, toedobj(other))

	def __or__(self, other):
		return EditorBinaryOp('|', self, toedobj(other))

	def __xor__(self, other):
		return EditorBinaryOp('^', self, toedobj(other))

	def __radd__(self, other):
		return EditorBinaryOp('+', toedobj(other), self)

	def __rsub__(self, other):
		return EditorBinaryOp('-', toedobj(other), self)

	def __rdiv__(self, other):
		return EditorBinaryOp('/', toedobj(other), self)

	def __rand__(self, other):
		return EditorBinaryOp('&', toedobj(other), self)

	def __ror__(self, other):
		return EditorBinaryOp('|', toedobj(other), self)

	def __rxor__(self, other):
		return EditorBinaryOp('^', toedobj(other), self)

	def __getitem__(self, index):
		return EditorIndex(self, index)

	def __call__(self, *args):
		return EditorFunc(self, *args)

	def __eq__(self, other):
		return (self is other or (type(self) is type(other) and self.__dict__ == other.__dict__))

	def __neg__(self):
		return EditorUnaryOp('-', self)

	def __repr__(self):
		return '<' + self.__class__.__name__ + '>'


class EditorNumber(int, EditorObj):
	'''Class representing integer literal
	'''
	def __repr__(self):
		return '{0}({1})'.format(
			self.__class__.__name__, super(EditorNumber, self).__repr__())


class EditorStr(unicode, EditorObj):
	'''Class representing text string literal

	.. note: Not a binary string.
	'''
	def __repr__(self):
		return '{0}({1})'.format(
			self.__class__.__name__, super(EditorStr, self).__repr__())


class EditorList(EditorObj):
	'''Class representing list literal
	'''
	def __init__(self, *children):
		self.children = [toedobj(child) for child in children]

	def __repr__(self):
		return '<{name}: [{children}]>'.format(
			name=self.__class__.__name__,
			children=','.join((repr(child) for child in self.children))
		)


class EditorDict(EditorObj):
	'''Class representing dictionary literal
	'''
	def __init__(self, *children_seq, **children):
		self.children = [
			(toedobj(k), toedobj(v))
			for k, v in chain(children_seq, children.items())
		]

	def __repr__(self):
		return '<{name}: {{ {children} }}>'.format(
			name=self.__class__.__name__,
			children=','.join((repr(k) + ':' + repr(v) for k, v in self.children))
		)


class EditorNone(EditorObj):
	'''Class representing None
	'''
	pass


class EditorEmpty(EditorObj):
	'''Class representing empty expression

	Used in slices to represent absense of some boundary.
	'''
	pass


def toedobj(obj, none=EditorNone):
	'''Function that converts some objects to :py:class:`EditorObj`

	Used to convert Python built-in object instances :py:class:`int`, 
	:py:class:`str`, :py:class:`tuple`, :py:class:`list` and ``None``. No-op for 
	objects that are already :py:class:`EditorObj` instances.

	:param obj:
		Converted object.
	:param none:
		Class, new instance of which will be returned in place of ``None``.

	:return: :py:class:`EditorObj` instance.
	'''
	if isinstance(obj, EditorObj):
		return obj
	elif isinstance(obj, int):
		return EditorNumber(obj)
	elif isinstance(obj, (unicode, str)):
		return EditorStr(obj)
	elif isinstance(obj, (tuple, list)):
		return EditorList(*obj)
	elif obj is None:
		return none()


class EditorUnaryOp(EditorObj):
	'''Class representing unary operator expression
	'''
	def __init__(self, op, subject):
		self.op = op
		'''Unary operator description'''
		self.subject = subject
		'''Expression that is a subject to this operator'''

	def __repr__(self):
		return '<{name} {op}: {subject}>'.format(
			name=self.__class__.__name__,
			op=self.op,
			subject=repr(self.subject),
		)


class EditorNot(EditorUnaryOp):
	'''Class representing negation unary operator expression
	'''
	def __init__(self, subject):
		super(EditorNot, self).__init__('!', subject)


class EditorBinaryOp(EditorObj):
	'''Class representing binary operator expression
	'''
	def __init__(self, op, *children):
		self.op = op
		'''Binary operator description'''
		self.children = [toedobj(child) for child in children]
		'''List of subjects to the binary operation

		.. note::
			If list contains more then one item then this is supposed to be 
			interpreted like ``{child1} {op} {child2} {op} {child3} …``.
		'''

	def __repr__(self):
		return '<{name} {op}: [{children}]>'.format(
			name=self.__class__.__name__,
			op=self.op,
			children=', '.join((repr(child) for child in self.children))
		)


class EditorTernaryOp(EditorObj):
	'''Class representing ternary operator expression
	'''
	def __init__(self, condition, if_true, if_false):
		self.condition = toedobj(condition)
		'''Condition expression'''
		self.if_true = toedobj(if_true)
		'''Result if condition expression is true'''
		self.if_false = toedobj(if_false)
		'''Result if condition expression is false'''

	def __repr__(self):
		return '<{name}: {condition} ? {if_true} : {if_false}>'.format(
			name=self.__class__.__name__,
			condition=repr(self.condition),
			if_true=repr(self.if_true),
			if_false=repr(self.if_false),
		)


class EditorIndex(EditorObj):
	'''Class representing __getitem__ expression: ``obj[idx]``, ``obj[idx:idx]``
	'''
	def __init__(self, obj, index):
		if isinstance(index, slice):
			if not (index.step is None or index.step == 1):
				raise NotImplementedError('Only [a:b] slices are supported')
			self.index = (
				toedobj(index.start, none=EditorEmpty),
				toedobj(index.stop, none=EditorEmpty)
			)
			'''List of indexes

			May contain either two elements (slice) or one (index).
			'''
		else:
			self.index = (toedobj(index),)
		self.obj = obj
		'''Expression being indexed'''

	def __repr__(self):
		return '<{name}: {obj}[{index}]>'.format(
			name=self.__class__.__name__,
			obj=repr(self.obj),
			index=','.join((repr(idx) for idx in self.index))
		)


class EditorFunc(EditorObj):
	'''Class used to describe editor function call expression
	'''
	def __init__(self, name, *args):
		self.name = name
		'''Name of the called function

		.. note: Not an expression.
		'''
		self.args = [toedobj(a) for a in args]
		'''List of expressions that are function arguments'''

	def __repr__(self):
		return '<{name}: {func}[{args}]>'.format(
			name=self.__class__.__name__,
			func=self.name,
			args=','.join((repr(arg) for arg in self.args))
		)


class EditorNamedThing(EditorObj):
	'''Class used to describe some expressions which use a single name
	'''
	def __init__(self, name):
		self.name = name
		'''Used name'''

	def __repr__(self):
		return '<' + self.__class__.__name__ + ': ' + repr(self.name) + '>'


class EditorParameter(EditorNamedThing):
	'''Class used to describe internal parameter

	Parameter may be transformed into any expression, transformation is 
	described in ``parameters`` dictionary which should be one of keyword 
	arguments to :py:meth:`Editor.toed`.
	'''
	pass


class EditorReqss(EditorObj):
	'''Class describing expression which returns requirements dictionary

	See :py:meth:`Editor.reqs_to_reqs_dict` and 
	:py:meth:`Editor.compile_reqs_dict`.
	'''
	pass


class EditorBufferName(EditorObj):
	'''Class describing expression which returns full buffer name
	'''
	pass


class EditorBufferNameBase(EditorBufferName):
	'''Class describing expression which returns buffer name without a directory
	'''
	pass


class EditorLastBufLine(EditorObj):
	'''Class describing expression which returns a number of lines in the buffer
	'''
	pass


class EditorWinPos(EditorObj):
	'''Class describing expression which returns a cursor position in a window
	'''
	pass


class EditorIter(EditorObj):
	'''Parent class for classes that describes iterating functions

	E.g. :py:func:`any` or :py:func:`filter`.
	'''
	iterparam = None
	'''Name of the parameter that is being iterated on

	May either be a :py:class:`powerline.lib.unicode.unicode` instance or a list 
	containing either tuples ``(iterparam, expr)`` or just a single string. 
	Values that are single strings are identical to values which are lists with 
	this string. ``expr`` is a :py:class:`EditorObj` instance which describes 
	expression used to obtain value for ``iterparam``. Note that it must be run 
	fast because it will be placed everywhere where parameter is needed.

	String values are like tuple values ``(string, kw['parameters']['vval'])`` 
	where ``kw`` is a kwargs dictionary passed to :py:meth:`Editor.toed`.
	'''


class EditorAny(EditorIter):
	'''Class that describes :py:func:`any` function run on a list

	EditorAny(condition, lst, iterparam) is like:

	.. code-block:: python

		any((iterparam for iterparam in lst if condition))
	'''
	def __init__(self, condition, lst, iterparam='vval'):
		self.condition = toedobj(condition)
		'''Filter condition expression'''
		self.list = toedobj(lst)
		'''Expression that returns a list being checked'''
		self.iterparam = iterparam

	def __repr__(self):
		return '<{name}: any({param} for {param} in {list} if {condition})>'.format(
			name=self.__class__.__name__,
			param=self.iterparam,
			list=repr(self.list),
			condition=repr(self.condition),
		)


class EditorFilter(EditorIter):
	'''Class that describes :py:func:`filter` function run on a list

	EditorFilter(condition, lst, iterparam) is like:

	.. code-block:: python

		[iterparam for iterparam in lst if condition]
	'''
	def __init__(self, condition, lst, iterparam='vval'):
		self.condition = toedobj(condition)
		'''Filter condition expression'''
		self.list = toedobj(lst)
		'''Expression that returns a list being filtered'''
		self.iterparam = iterparam

	def __repr__(self):
		return '<{name}: ({param} for {param} in {list} if {condition})>'.format(
			name=self.__class__.__name__,
			param=self.iterparam,
			list=repr(self.list),
			condition=repr(self.condition),
		)


class EditorMap(EditorIter):
	'''Class that describes :py:func:`map` function run on a list

	EditorMap(expr, lst, iterparam) is like:

	.. code-block:: python

		[iterparam for iterparam in lst if condition]

	if ``iterparam`` is a string. It may also be a list, in which case first 
	parameter is expected to be a string for the same purposes as in the above 
	expression and others are tuples containing a name of the parameter and 
	:py:class:`EditorObj` instances containing expressions used to determine 
	parameter value. Note that expressions will be recomputed each time used.
	'''
	def __init__(self, expr, lst, iterparam='vval'):
		self.expr = toedobj(expr)
		'''Item expression'''
		self.list = toedobj(lst)
		'''Expression that returns a list being used'''
		self.iterparam = iterparam

	def __repr__(self):
		return '<{name}: ({expr} for {param} in {list})>'.format(
			name=self.__class__.__name__,
			param=self.iterparam,
			list=repr(self.list),
			expr=repr(self.expr),
		)


class EditorIterable(EditorObj):
	'''Class describing expression which returns a list of something

	Used for buffer, tabpage and window lists.
	'''
	pass


class EditorTabAmount(EditorObj):
	'''Class describing expression which returns a number of tabpages
	'''
	pass


class EditorBufferList(EditorIterable):
	'''Class describing expression which returns a list of buffers
	'''
	pass


class EditorTabList(EditorIterable):
	'''Class describing expression which returns a list of tabpages
	'''
	pass


class EditorWindowList(EditorIterable):
	'''Class describing expression which returns a list of windows
	'''
	pass


class EditorWindowBuffer(EditorObj):
	'''Class describing expression which returns current window’s buffer
	'''
	pass


class EditorTabWindowBuffer(EditorObj):
	'''Class describing expression which returns tab’s window’s buffer

	Uses current window for the current tab.
	'''
	pass


class EditorTabWindow(EditorObj):
	'''Class describing expression which returns current tab’s window
	'''
	pass


class EditorCached(EditorObj):
	'''Class that describes expression which returns a cached value
	'''
	def __init__(self, cache_name, key, val, cache_type):
		self.cache_name = cache_name
		'''Name of the cache (not an expression)'''
		self.key = toedobj(key)
		'''Key expression in this cache

		If key expression changes then cache is invalidated.
		'''
		self.val = toedobj(val)
		'''Expression used to generate value in case it is missing in cache'''
		self.cache_type = cache_type
		'''Type of the cache

		Currently the only supported type is ``buffer``. This is like having key 
		consist of :py:attr:`EditorCached.key` attribute and buffer identifier.
		'''

	def __repr__(self):
		return '<{name}: {cache_type}/{cache_name}[{key}] : {val}>'.format(
			name=self.__class__.__name__,
			cache_type=self.cache_type,
			cache_name=self.cache_name,
			key=self.key,
			val=repr(self.val),
		)


class EditorOverrides(EditorObj):
	'''Class describing expression which returns override descriptions
	'''
	pass


class EditorEncoding(EditorObj):
	'''Class describing expression which returns internal editor encoding

	I.e. encoding in which powerline needs to return string to be understood 
	correctly. It is also assumed that all incoming strings are strings in this 
	encoding.
	'''
	pass


class EditorAvailableWidth(EditorObj):
	'''Class describing expression which returns available width

	Should be used by renderers to determine how much space they may consume 
	in statusline.
	'''
	pass


Range = namedtuple('Range', ('start', 'end'))
VisualPosition = namedtuple('VisualPosition', ('line', 'col', 'virtcol', 'virtoff'))
WindowPosition = namedtuple('WindowPosition', ('line', 'col'))
WindowLines = namedtuple('WindowLines', ('first', 'last'))


def param_updated(kw, *args, **kwargs):
	'''Return a copy of kw with a copy of kw['parameters'] updated with kwargs

	:param dict kw:
		Dictionary to update.

	:return:
		Copy of kw with copy of ``kw['parameters']`` updated using ``args`` and 
		``kwargs``.
	'''
	return updated(kw, parameters=updated(kw['parameters'], *args, **kwargs))


def iterparam_updated(kw, obj, toed):
	'''Copy and update kw['parameters'] for iterating over

	:param dict kw:
		Dictionary to update.
	:param poweline.editors.EditorIter obj:
		What to update with. Uses 
		:py:attr:`powerline.editors.EditorIter.iterparam` to decide which 
		parameters to update.

		In addition to parameters which were listed updating ``window`` 
		parameter triggers updating ``buffer`` and updating ``tabpage`` updates 
		``window`` and ``buffer`` parameters. In these cases ``window`` is set 
		to converted by ``toed`` :py:class:`EditorTabWindow` instance and 
		``buffer`` is set to converted :py:class:`EditorTabWindowBuffer` 
		instance.
	:param func toed:
		Bound method :py:meth:`Editor.toed` or something similar.

	:return:
		Copy of ``kw`` with copy of ``kw['parameters']`` updated according to 
		the description.
	'''
	kw = kw.copy()
	params = kw['parameters'] = kw['parameters'].copy()
	iterparam = obj.iterparam
	if not isinstance(iterparam, list):
		iterparam = [iterparam]
	for val in iterparam:
		if isinstance(val, tuple):
			name, expr = val
			params[name] = toed(expr, **kw)
		else:
			name = val
			params[name] = params['vval']
		if name == 'tabpage':
			name = 'window'
			kw['tabscope'] = True
			params[name] = toed(EditorTabWindow(), **kw)
		if name == 'window':
			name = 'buffer'
			params[name] = toed(EditorTabWindowBuffer(), **kw)
	return kw


class Editor(object):
	'''Base class for editor support

	This class defines abstract methods and is used for documentation purposes.
	'''
	mode = ()
	'''Definition of how to obtain current mode
	'''

	visual_range = ()
	'''Definition of how to get currently selected visual range from the editor

	Expected to have no parameters.
	'''

	modified_indicator = ()
	'''Definition of how to get whether given buffer was modified

	Expected to depend on the buffer.
	'''

	tab_modified_indicator = ()
	'''Definition of how to get whether any buffer in given tabpage was modified

	Expected to depend on the tabpage.
	'''

	buffer_name = ()
	'''Definition of how to get given buffer name

	Expected to depend on the buffer.
	'''

	buffer_len = ()
	'''Definition of how to get number of lines in the given buffer

	Expected to depend on the buffer.
	'''

	file_size = ()
	'''Definition of how to get amount of bytes given buffer occupies

	Expected to depend on the buffer.
	'''

	file_format = ()
	'''Definition of how to get line ending format for the given buffer

	Expected to depend on the buffer.
	'''

	file_encoding = ()
	'''Definition of how to get encoding of the given buffer

	Expected to depend on the buffer.
	'''

	file_type = ()
	'''Definition of how to get file type of the given buffer

	Expected to depend on the buffer.
	'''

	window_position = ()
	'''Definition of how to get cursor position in the given window

	Expected to depend on the window.
	'''

	displayed_lines = ()
	'''Definition of how to get range of lines displayed in the given window

	Expected to depend on the window.
	'''

	virtcol = ()
	'''Definition of how to get virtual cursor column in the given window

	Expected to depend on the window.
	'''

	modified_buffers = ()
	'''Definition of how to get list of modified buffers
	'''

	trailing_whitespace = ()
	'''Definition of how to get a line which has trailing whitespace

	Expected to depend on the buffer.
	'''

	editor_overrides = ()
	'''Definition of how to get editor override dictionaries

	Expected to have no parameters.
	'''

	editor_encoding = ()
	'''Definition of how to get editor effective encoding

	Expected to have no parameters.
	'''

	available_width = ()
	'''Definition of how to get available width

	Expected to have no parameters.
	'''

	list_buffers = ()
	'''Definition of how to list buffers

	Expected to have no parameters.
	'''

	list_windows = ()
	'''Definition of how to list windows

	Expected to have no parameters. Listed window is expected to contain 
	information about buffer displayed in the window.
	'''

	list_tabs = ()
	'''Definition of how to list tab pages

	Expected to have no parameters. Listed tabpage is expected to contain at 
	least list of windows and some identifier.
	'''

	types = {
		'mode': 'ascii',
		'visual_range': 'visrange',
		'modified_indicator': 'bool',
		'tab_modified_indicator': 'bool',
		'buffer_name': 'str',
		'buffer_len': 'int',
		'file_size': 'int',
		'file_format': 'ascii',
		'file_encoding': 'ascii',
		'file_type': 'str',
		'window_position': 'winpos',
		'displayed_lines': 'winlines',
		'virtcol': 'int',
		'trailing_whitespace': 'int',
		'editor_overrides': 'overridesdict',
		'editor_encoding': 'ascii',
		'available_width': 'int',
	}
	'''Types for editor properties

	Must be a :py:class:`dict` instance where keys are names of the above 
	attributes and values are their types. All types must be present in 
	:py:attr:`converters` attribute. Is used in case editor returns invalid 
	types.

	It is not allowed to modify types when subclassing: subclass can add new 
	types, but not modify existing.
	'''

	converters = {
		'visrange': lambda l: Range(*[VisualPosition(*[int(j) for j in i]) for i in l]),
		'winpos': lambda l: WindowPosition(*[int(i) for i in l]),
		'winlines': lambda l: WindowLines(*[int(i) for i in l]),
	}
	'''Converters for editor properties

	Must be a :py:class:`dict` instance where keys are values from 
	:py:attr:`types` attribute. Default converter is “do nothing”.

	Values are function that accept one argument and return it converted to the 
	proper type. Subclasses may supply different converters, but converted 
	values must be instances of the same type as documented here.

	Types:

	=============  =======================================================
	Type name      Type
	=============  =======================================================
	ascii          :py:class:`powerline.lib.unicode.unicode`.
	str            :py:class:`powerline.lib.unicode.unicode`.
	visrange       :py:class:`Range` with :py:class:`VisualRange` inside.
	bool           :py:class:`bool`.
	int            :py:class:`int`.
	winpos         :py:class:`WindowPosition`.
	winlines       :py:class:`WindowLines`.
	overridesdict  :py:class:`dict`.
	=============  =======================================================
	'''

	edconverters = ()
	'''Editor-specific converters

	Must be a :py:class:`dict` instance where keys are :py:class:`EditorObj` 
	subclasses (or this class itself) and values are functions with two 
	positional and any number of keyword arguments that return a string.

	Positional parameters to converter functions are:

	#. :py:class:`EditorObj` instance that is being converted.
	#. :py:meth:`Editor.toed` bound class method used to convert objects.

	Keyword parameters are editor-specific.
	'''

	@classmethod
	def toed(cls, obj, **kwargs):
		'''Convert :py:class:`powerline.editors.EditorObj` instance to a string

		Returned string is editor-specific and serves the purpose of helping to 
		obtain a proper value from the editor.

		When converting this method queries :py:attr:`Editor.edconverters` for 
		each object’s subclass in MRO (method resolution order) table in order 
		to find conversion function.

		:param EditorObj obj:
			Converted object.

		:return: A string. May raise :py:class:`NotImplementedError`.
		'''
		for objcls in obj.__class__.__mro__:
			try:
				converter = cls.edconverters[objcls]
			except KeyError:
				pass
			else:
				return converter(obj, cls.toed, **kwargs)
		raise NotImplementedError('No converter found for class {0!r} of object {1!r}'.format(type(obj), obj))

	@classmethod
	def reqs_to_reqs_dict(cls, reqs):
		'''Convert list of requirements to requirements dictionary

		Requirements list is described in :py:func:`with_input`. Requirements 
		dictionary looks like ``{{requirement_name}: ({requirement_desc}, 
		{requirement_type})}``. ``{requirement_desc}`` is described in relevant 
		:py:class:`Editor` subclass, ``{requirement_type}`` is either a string 
		or a dictionary which maps requirement subkeys to actual types (used for 
		listers). In case of string type, these strings may appear in 
		:py:attr:`converters` attribute.

		:param list reqs:
			List of requirements.

		:return: Dictionary.
		'''
		reqs_dict = {}

		for req in reqs:
			reqname, reqdef, reqtype = cls.normalize_req(req)
			try:
				existing_reqdef, existing_reqtype = reqs_dict[reqname]
			except KeyError:
				reqs_dict[reqname] = (reqdef, reqtype)
			else:
				assert(existing_reqdef == reqdef)
				assert(existing_reqtype == reqtype)

		return reqs_dict

	@classmethod
	def compile_reqs_dict(cls, reqs_dict):
		'''Compile reqs dict to something which will eventually return a dict

		``reqs_dict`` is a dictionary returned by 
		:py:meth:`Editor.reqs_to_reqs_dict`. Result of the compilation must 
		somehow (defined by editor-specific bindings) return :ref:`input 
		dictionary <dev-segment_info-vim-input>`.
		'''
		raise NotImplementedError

	@classmethod
	def compile_themes_getter(cls, local_themes, **kwargs):
		'''Compile local themes list to something used to return one theme

		:param list local_themes:
			List of local themes. Each local theme is a 2-tuple: ``(matcher, 
			theme_desc)``, where ``matcher`` is either 
			a :py:class:`powerline.editors.EditorObj` instance or a callable that 
			takes two keyword arguments: ``matcher_info`` and ``pl`` and returns 
			a boolean value.

			``theme_desc`` is a dictionary at least with the ``theme`` key which 
			contains :py:class:`powerline.theme.Theme` object.
		:param dict kwargs:
			Whatever keyword arguments need to be passed to :py:func:`tovimpy`.
		'''
		raise NotImplementedError

	const_reqs = ('available_width',)
	'''Requirements which are always needed

	These requirements will be requested always, regardless of what was 
	requested by segments.
	'''

	list_objects = {
		'list_tabs': EditorTabList,
		'list_buffers': EditorBufferList,
		'list_windows': EditorWindowList,
	}
	'''Dictionary mapping lister names to 
	:py:class:`powerline.editors.EditorIterable` subclasses
	'''

	list_parameter_names = {
		'list_tabs': 'tabpage',
		'list_buffers': 'buffer',
		'list_windows': 'window',
	}
	'''Dictionary mapping lister names to 
	:py:attr:`powerline.editors.EditorIter.iterparam` values
	'''

	@classmethod
	def req_to_edobj(cls, req):
		'''Convert requirement to :py:class:`EditorObj`

		Used by :py:meth:`segments_to_reqs` to convert lister requirements 
		(values of req_dict).

		:param req: Requirement to convert.

		:return: Converted requirement.
		'''
		return req

	@classmethod
	def segments_to_reqs(cls, seglist):
		'''Transform a list of segments into a list of requirements

		Takes into account requirements requested by segment itself and also by 
		:ref:`include and exclude functions 
		<config-themes-seg-exclude_function>`.

		:param list seglist:
			List of segments. Handles lister segments speciall.

		:yield: ()
		'''
		for segment in seglist:
			for key in ['ext_editor_input', 'inc_ext_editor_input',
			            'exc_ext_editor_input']:
				try:
					reqs = segment[key]
				except KeyError:
					pass
				else:
					for req in reqs:
						yield req
			if segment['type'] == 'segment_list' and 'ext_editor_list' in segment:
				lname, lreqs = segment['ext_editor_list']
				yield lname
				lobj = cls.list_objects[lname]()
				iterparam = cls.list_parameter_names[lname]
				reqs_dict = cls.reqs_to_reqs_dict(chain(
					cls.segments_to_reqs(segment['segments']),
					lreqs,
				))
				reqs_types_dict = dict((
					(k, v[1])
					for k, v in reqs_dict.items()
				))
				reqs_vals_dict = dict((
					(k, cls.req_to_edobj(v[0]))
					for k, v in reqs_dict.items()
				))
				inputs = EditorDict(**reqs_vals_dict)
				yield (
					lname + '_inputs',
					(EditorMap(inputs, lobj, iterparam),),
					reqs_types_dict,
				)

	@classmethod
	def normalize_req(cls, req):
		'''Transform req which is a name into (name, def, type)

		:param unicode|tuple req:
			Requirement to transform.

		:return: (name, def, type).
		'''
		if isinstance(req, tuple):
			return req
		else:
			return (
				req,
				getattr(cls, req),
				cls.types.get(req, None)
			)

	@classmethod
	def theme_to_reqs(cls, theme, const_reqs_override=None):
		'''Transform theme into an iterable of requirements

		:param powerline.theme.Theme theme:
			Transformed theme.
		:param tuple const_reqs_override:
			Override for :py:attr:`const_reqs`.

		:yield: All requirements, in a form (name, def, type).
		'''
		for line in theme.segments:
			for seglist in line.values():
				for req in cls.segments_to_reqs(seglist):
					yield cls.normalize_req(req)
		const_reqs = (
			const_reqs_override
			if const_reqs_override is not None
			else cls.const_reqs)
		for const_req in const_reqs:
			yield cls.normalize_req(const_req)

	@classmethod
	def theme_to_reqs_dict(cls, theme, const_reqs_override=None):
		'''Transform theme into a requirements dictionary

		See :py:meth:`reqs_to_reqs_dict`.

		:param powerline.theme.Theme theme:
			Transformed theme.
		:param tuple const_reqs_override:
			Override for :py:attr:`const_reqs`.

		:return: Requirements dictionary.
		'''
		return cls.reqs_to_reqs_dict(cls.theme_to_reqs(theme))
