# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import re
import os

from collections import defaultdict
from itertools import chain

from powerline.editors import (Editor,
                               EditorObj, EditorBinaryOp, EditorTernaryOp, EditorEmpty,
                               EditorIndex, EditorFunc, EditorStr, EditorList, EditorNone,
                               EditorNamedThing, EditorBufferName, EditorLastBufLine, EditorParameter,
                               EditorWinPos, EditorAny, EditorUnaryOp, EditorNot, EditorBufferList,
                               EditorFilter, EditorCached, EditorDict, EditorOverrides, EditorEncoding,
                               EditorBufferNameBase, EditorMap, EditorWindowList, EditorTabList,
                               toedobj)


def finish_kwargs(kwargs, vval=None, cache=None, buffer_cache=None, paramfunc=(lambda s: s)):
	'''Create a copy of kwargs with necessary parameters filled

	If ``kwargs`` dictionary contains key ``finished`` with true value then it 
	is returned as-is.

	Modified keys:

	``tabscope``
		Determines whether current argument is to be run in a tab scope. If it 
		is not set this function defaults it to ``False``.
	``parameters``
		Dictionary that contains all parameters. Is copied and modified 
		according to given arguments.

	:param dict kwargs:
		Initial keyword arguments.
	:param str vval:
		Value for an iterator parameter. Defaults to ``i``.
	:param str cache:
		Value for cache. Defaults to ``cache``.
	:param str buffer_cache:
		Value for a buffer cache. Defaults to ``buffer_cache``.
	:param func paramfunc:
		Function that converts parameters ``buffer``, ``window`` and ``tabpage`` 
		to the used strings.

	:return: A modified copy of ``kwargs`` dictionary.
	'''
	if kwargs.get('finished'):
		return kwargs
	kwargs = kwargs.copy()
	kwargs.setdefault('tabscope', False)
	try:
		kwargs['parameters'] = kwargs['parameters'].copy()
	except KeyError:
		kwargs['parameters'] = {}
	kwargs['parameters'].setdefault('buffer', paramfunc('buffer'))
	kwargs['parameters'].setdefault('window', paramfunc('window'))
	kwargs['parameters'].setdefault('tabpage', paramfunc('tabpage'))
	kwargs['parameters'].setdefault('vval', vval or 'i')
	kwargs['parameters'].setdefault('cache', cache or 'cache')
	kwargs['parameters'].setdefault('buffer_cache', buffer_cache or 'buffer_cache')
	kwargs['finished'] = True
	return kwargs


class VimGlobalOption(EditorNamedThing):
	pass


class VimBufferOption(EditorNamedThing):
	pass


class VimWinOption(EditorNamedThing):
	pass


class VimWinVar(EditorNamedThing):
	pass


class VimBufferVar(EditorNamedThing):
	pass


class VimVVar(EditorNamedThing):
	pass


class VimSVar(EditorNamedThing):
	pass


class VimGlobalVar(EditorNamedThing):
	pass


class VimCurrentTabNumber(EditorObj):
	pass


class VimCurrentBufferNumber(EditorObj):
	pass


class VimCurrentWindowNumber(EditorObj):
	pass


class VimOptionalFunc(EditorObj):
	def __init__(self, name, args=(), cond=None, default=EditorNone()):
		self.name = name
		if cond:
			self.cond = toedobj(cond)
		else:
			self.cond = EditorFunc('exists', '*' + self.name)
		self.default = toedobj(cond)
		self.args = [toedobj(arg) for arg in args]


class VimStlWinList(EditorObj):
	pass


class VimTabAmount(EditorObj):
	pass


def updated(d, *args, **kwargs):
	d = d.copy()
	d.update(*args, **kwargs)
	return d


ED_TO_VIM = {
	EditorObj: {
		'tovim': lambda self, toed, **kw: str(self),
		'tovimpy': lambda self, toed, **kw: repr(self),
	},
	EditorStr: {
		'tovim': lambda self, toed, **kw: (
			"'" + self.replace("'", "''") + "'"
		),
	},
	EditorList: {
		'toed': lambda self, toed, **kw: (
			'[' + ','.join((toed(child, **kw) for child in self.children)) + ']'
		),
	},
	EditorNone: {
		'tovim': lambda self, toed, **kw: '0',
		'tovimpy': lambda self, toed, **kw: 'None',
	},
	EditorBinaryOp: {
		'tovim': lambda self, toed, **kw: (
			'({0}) =~# \'\\v\'.({1})'.format(
				toed(self.children[0], **kw),
				toed(self.children[1], **kw),
			)
			if self.op == '=~#' and len(self.children) == 2 else
			'==#'.join((toed(child, **kw) for child in self.children))
			if self.op == '==' else
			'+'.join((toed(child, **kw) for child in self.children))
			if self.op == '+l' else
			self.op.join((toed(child, **kw) for child in self.children))
		),
		'tovimpy': lambda self, toed, **kw: (
			'bool(re.search({1}, {0}))'.format(
				toed(self.children[0], **kw),
				toed(self.children[1], **kw),
			)
			if self.op == '=~#' and len(self.children) == 2 else
			'"".join((str(i) for i in ({0},)))'.format(
				','.join(toed(child, **kw) for child in self.children)
			)
			if self.op == '.' else
			'list(chain(' + ','.join((toed(child, **kw) for child in self.children)) + '))'
			if self.op == '+l' else
			self.op.join((toed(child, **kw) for child in self.children))
		),
	},
	EditorTernaryOp: {
		'tovim': lambda self, toed, **kw: '({condition})? ({if_true}): ({if_false})'.format(
			condition=toed(self.condition, **kw),
			if_true=toed(self.if_true, **kw),
			if_false=toed(self.if_false, **kw),
		),
		'tovimpy': lambda self, toed, **kw: '({if_true}) if ({condition}) else ({if_false})'.format(
			condition=toed(self.condition, **kw),
			if_true=toed(self.if_true, **kw),
			if_false=toed(self.if_false, **kw),
		),
	},
	EditorEmpty: {
		'toed': lambda self, toed, **kw: '',
	},
	EditorIndex: {
		'toed': lambda self, toed, **kw: (
			toed(self.obj, **kw) + (
				'[' + ' : '.join((toed(i, **kw) for i in self.index)) + ']'
			)
		),
	},
	EditorFunc: {
		'tovim': lambda self, toed, **kw: (
			self.name + '(' + ', '.join((toed(arg, **kw) for arg in self.args)) + ')'
		),
		'tovimpy': lambda self, toed, **kw: (
			'vim_funcs[' + repr(self.name) + ']'
			+ '(' + ', '.join((toed(arg, **kw) for arg in self.args)) + ')'
		),
	},
	VimGlobalOption: {
		'tovim': lambda self, toed, **kw: '&' + self.name,
		'tovimpy': lambda self, toed, **kw: 'vim.options[' + repr(str(self.name)) + ']',
	},
	VimBufferOption: {
		'tovim': lambda self, toed, **kw: (
			toed(EditorFunc('getbufvar', EditorParameter('buffer'), '&' + self.name), **kw)
		),
		'tovimpy': lambda self, toed, **kw: (
			kw['parameters']['buffer'] + '.options[' + repr(str(self.name)) + ']'
		),
	},
	VimWinOption: {
		'tovim': lambda self, toed, **kw: toed(
			EditorFunc('gettabwinvar', EditorParameter('tabpage'), EditorParameter('window'), '&' + self.name)
			if kw['tabscope'] else
			EditorFunc('getwinvar', EditorParameter('window'), '&' + self.name),
			**kw
		),
		'tovimpy': lambda self, toed, **kw: (
			kw['parameters']['window'] + '.options[' + repr(str(self.name)) + ']'
		),
	},
	EditorBufferName: {
		'tovim': lambda self, toed, **kw: toed(
			EditorFunc('fnamemodify', EditorFunc('bufname', EditorParameter('buffer')), ':p'),
			**kw),
		'tovimpy': lambda self, toed, **kw: '{buffer}.name'.format(
			buffer=kw['parameters']['buffer']),
	},
	EditorBufferNameBase: {
		'tovim': lambda self, toed, **kw: toed(
			EditorFunc('fnamemodify', EditorFunc('bufname', EditorParameter('buffer')), ':t'),
			**kw),
		'tovimpy': lambda self, toed, **kw: 'basename({buffer}.name)'.format(
			buffer=kw['parameters']['buffer']),
	},
	EditorLastBufLine: {
		'tovim': lambda self, toed, **kw: toed(EditorFunc('line', '$'), **kw),
		'tovimpy': lambda self, toed, **kw: 'len({buffer})'.format(
			buffer=kw['parameters']['buffer']),
	},
	VimWinVar: {
		'tovim': lambda self, toed, **kw: toed(
			EditorFunc('gettabwinvar', EditorParameter('tabpage'), EditorParameter('window'), self.name)
			if kw['tabscope'] else
			EditorFunc('getwinvar', EditorParameter('window'), self.name),
			**kw
		),
		'tovimpy': lambda self, toed, **kw: '{window}.vars.get({0!r}, "")'.format(
			self.name,
			window=kw['parameters']['window']
		),
	},
	VimBufferVar: {
		'tovim': lambda self, toed, **kw: toed(
			EditorFunc('getbufvar', EditorParameter('buffer'), self.name),
			**kw
		),
		'tovimpy': lambda self, toed, **kw: '{buffer}.vars.get({0!r}, "")'.format(
			self.name,
			buffer=kw['parameters']['buffer']
		),
	},
	EditorWinPos: {
		'tovim': lambda self, toed, **kw: '[line("."), col(".")]',
		'tovimpy': lambda self, toed, **kw: '({window}.cursor[0], {window}.cursor[1]+1)'.format(
			window=kw['parameters']['window']
		),
	},
	EditorParameter: {
		'toed': lambda self, toed, **kw: kw['parameters'][self.name],
	},
	EditorUnaryOp: {
		'toed': lambda self, toed, **kw: '({op}({subject}))'.format(
			op=self.op, subject=toed(self.subject, **kw)),
	},
	EditorNot: {
		'tovimpy': lambda self, toed, **kw: '(not ({subject}))'.format(subject=toed(self.subject, **kw)),
	},
	EditorAny: {
		'tovim': lambda self, toed, **kw: (lambda self, **kw: toed(
			EditorNot(
				EditorFunc(
					'empty', EditorFunc(
						'filter', EditorFunc(
							'map',
							EditorFunc('copy', self.list),
							toed(self.condition, **kw)),
						'v:val'))),
			**kw
		))(self, **updated(
			kw, parameters=updated(
				kw['parameters'], ((self.iterparam, kw['parameters']['vval']),)))),
		'tovimpy': lambda self, toed, **kw: (lambda self, **kw: 'any(({0} for vval in {1}))'.format(
			toed(self.condition, **kw),
			toed(self.list, **kw)))(
				self, **updated(
					kw, parameters=updated(
						kw['parameters'], ((self.iterparam, kw['parameters']['vval']),)))
			),
	},
	EditorFilter: {
		'tovim': lambda self, toed, **kw: (lambda self, **kw: toed(
			EditorFunc(
				'filter',
				EditorFunc('copy', self.list),
				toed(self.condition, **kw)
			),
			**kw
		))(self, **updated(
			kw, parameters=updated(
				kw['parameters'], ((self.iterparam, kw['parameters']['vval']),)))),
		'tovimpy': lambda self, toed, **kw: (lambda self, **kw: '[vval for vval in {1} if {0}]'.format(
			toed(self.condition, **kw),
			toed(self.list, **kw)))(
				self, **updated(
					kw, parameters=updated(
						kw['parameters'], ((self.iterparam, kw['parameters']['vval']),)))
			),
	},
	EditorMap: {
		'tovim': lambda self, toed, **kw: (lambda self, **kw: toed(
			EditorFunc(
				'map',
				EditorFunc('copy', self.list),
				toed(self.expr, **kw)
			),
			**kw
		))(self, **updated(
			kw, parameters=updated(
				kw['parameters'], ((self.iterparam, kw['parameters']['vval']),)))),
		'tovimpy': lambda self, toed, **kw: (lambda self, **kw: '[{0} for vval in {1}]'.format(
			toed(self.expr, **kw),
			toed(self.list, **kw)))(
				self, **updated(
					kw, parameters=updated(
						kw['parameters'], ((self.iterparam, kw['parameters']['vval']),)))
			),
	},
	VimVVar: {
		'tovim': lambda self, toed, **kw: 'v:' + self.name,
		'tovimpy': lambda self, toed, **kw: 'vim.vvars[{0!r}]'.format(self.name),
	},
	VimSVar: {
		'tovim': lambda self, toed, **kw: 's:' + self.name,
		'tovimpy': lambda self, toed, **kw: 'vim.eval({0!r})'.format('s:' + self.name),
	},
	EditorBufferList: {
		'tovim': lambda self, toed, **kw: toed(
			EditorFunc('tabpagebuflist', EditorParameter('tabpage'))
			if kw['tabscope'] else
			EditorFunc('filter', EditorFunc('range', 1, EditorFunc('bufnr', '$')), 'bufexists(v:val)'),
			**kw
		),
		'tovimpy': lambda self, toed, **kw: (
			'[window.buffer for window in ' + kw['parameters']['tabpage'] + '.windows]'
			if kw['tabscope'] else
			'vim.buffers'
		),
	},
	EditorWindowList: {
		'tovim': lambda self, toed, **kw: toed(
			EditorFunc('range', 1, EditorFunc('tabpagewinnr', EditorParameter('tabpage'), '$'))
			if kw['tabscope'] else
			EditorFunc('range', 1, EditorFunc('winnr', '$')),
			**kw
		),
		'tovimpy': lambda self, toed, **kw: (
			kw['parameters']['tabpage'] + '.windows'
			if kw['tabscope'] else
			'vim.windows'
		),
	},
	EditorTabList: {
		'tovim': lambda self, toed, **kw: toed(
			EditorFunc('range', 1, EditorFunc('tabpagenr', '$')),
			**kw
		),
		'tovimpy': lambda self, toed, **kw: (
			'vim.tabpages'
		),
	},
	EditorDict: {
		'toed': lambda self, toed, **kw: (
			'{' + ','.join((':'.join((toed(v, **kw) for v in child)) for child in self.children)) + '}'),
	},
	EditorCached: {
		'tovim': lambda self, toed, **kw: ((lambda cache: (toed(
			EditorTernaryOp(
				cache[self.cache_name][0].equals(self.key),
				cache[self.cache_name][1],
				EditorFunc('extend', cache, EditorDict((self.cache_name, (self.key, self.val))))[
					self.cache_name][1]
			),
			**kw
		)))(cache=(
			EditorParameter(self.cache_type + '_cache')[EditorParameter(self.cache_type)]
			if self.cache_type == 'buffer' else
			EditorParameter(self.cache_type + '_cache')
		))),
		'tovimpy': lambda self, toed, **kw: ((lambda cache: (
			(
				'{cache}[{cache_name!r}][1] '
				'if {cache}[{cache_name!r}][0] == {key} else '
				'updated({cache}, ({cache_name!r}, ({key}, {val})))[{cache_name!r}][1]'
			).format(
				cache=cache,
				cache_name=self.cache_name,
				key=toed(self.key, **kw),
				val=toed(self.key, **kw),
			)
		))(cache=(
			'{0}[{1}]'.format(
				kw['parameters'][self.cache_type + '_cache'],
				'buffer.number')
			if self.cache_type == 'buffer' else
			kw['parameters'][self.cache_type + '_cache']
		))),
	},
	VimCurrentTabNumber: {
		'tovim': lambda self, toed, **kw: toed(EditorFunc('tabpagenr'), **kw),
		'tovimpy': lambda self, toed, **kw: 'vim.current.tabpage.number',
	},
	VimCurrentBufferNumber: {
		'tovim': lambda self, toed, **kw: toed(EditorFunc('bufnr', '%'), **kw),
		'tovimpy': lambda self, toed, **kw: 'vim.current.buffer.number',
	},
	VimCurrentWindowNumber: {
		'tovim': lambda self, toed, **kw: toed(EditorFunc('winnr'), **kw),
		'tovimpy': lambda self, toed, **kw: 'vim.current.window.number',
	},
	VimOptionalFunc: {
		'toed': lambda self, toed, **kw: toed(
			EditorTernaryOp(self.cond, EditorFunc(self.name, *self.args), self.default),
			**kw
		),
	},
	VimStlWinList: {
		'tovim': lambda self, toed, **kw: toed(
			EditorFunc(
				'map',
				EditorFunc('range', 1, EditorFunc('winnr', '$')),
				toed(
					EditorList(
						EditorParameter('window'),
						VimWinVar('_powerline_window_id'),
						VimWinOption('statusline'),
					),
					**updated(kw, {'parameters': updated(kw['parameters'], window=toed(VimVVar('val'), **kw))})
				)
			),
			**kw
		),
		'tovimpy': lambda self, toed, **kw: (
			'[({window}, window.vars.get("_powerline_window_id", None), window.options["statusline"])'
			' for window in vim.windows]'.format(
				**kw['parameters']
			)
		),
	},
	VimGlobalVar: {
		'tovim': lambda self, toed, **kw: 'g:' + self.name,
		'tovimpy': lambda self, toed, **kw: 'vim.vars.get({0!r}, "")'.format(self.name),
	},
	EditorOverrides: {
		'tovim': lambda self, toed, **kw: toed(
			EditorDict(
				config_paths=VimGlobalVar('powerline_config_paths'),
				theme_overrides=VimGlobalVar('powerline_theme_overrides'),
				config_overrides=VimGlobalVar('powerline_config_overrides'),
			),
			**kw
		),
		'tovimpy': lambda self, toed, **kw: (
			'{' + (
				'"config_paths": vim.vars.get("powerline_config_paths", None),'
				'"theme_overrides": vim.vars.get("powerline_theme_overrides", None),'
				'"config_overrides": vim.vars.get("powerline_config_overrides", None),'
			) + '}'
		),
	},
	EditorEncoding: {
		'toed': lambda self, toed, **kw: toed(VimGlobalOption('encoding'), **kw),
	},
	VimTabAmount: {
		'tovim': lambda self, toed, **kw: toed(EditorFunc('tabpagenr', '$'), **kw),
		'tovimpy': lambda self, toed, **kw: 'len(vim.tabpages)',
	},
}


class VimEditor(Editor):
	'''Definition of the Vim editor
	'''
	mode = (EditorFunc('mode', 1), EditorStr('nc'))
	_pos_to_pos_and_col = lambda pos: pos[1:].joined(EditorList(EditorFunc('virtcol', pos[1:])))
	visual_range = (
		EditorList(
			_pos_to_pos_and_col(EditorFunc('getpos', 'v')),
			_pos_to_pos_and_col(EditorFunc('getpos', '.'))
		),
		EditorNone()
	)
	del _pos_to_pos_and_col
	modified_indicator = (VimBufferOption('modified'),)
	tab_modified_indicator = (EditorAny(VimBufferOption('modified'), EditorBufferList(), 'buffer'),)
	paste_indicator = (VimGlobalOption('paste'), EditorNone())
	buffer_name = (EditorBufferName(),)
	buffer_len = (EditorLastBufLine(),)
	buffer_type = (VimBufferOption('buftype'),)
	file_size = (EditorFunc('line2byte', buffer_len[0] + 1) - 1, EditorNone())
	file_format = (VimBufferOption('fileformat'),)
	file_encoding = (VimBufferOption('fileencoding'),)
	file_type = (VimBufferOption('filetype'),)
	window_title = (VimWinVar('quickfix_title'),)
	window_position = (EditorWinPos(),)
	displayed_lines = (EditorList(EditorFunc('line', 'w0'), EditorFunc('line', 'w$')), EditorNone())
	virtcol = (EditorFunc('virtcol', '.'), EditorNone())
	readonly_indicator = (VimBufferOption('readonly'),)
	modified_buffers = (EditorFilter(VimBufferOption('modified'), EditorBufferList(), 'buffer'),)
	trailing_whitespace = (
		EditorCached(
			'trailing_whitespace',
			VimBufferVar('changedtick'),
			EditorFunc('search', '\\m\\C\\s$', 'nw'),
			cache_type='buffer',
		),
	)
	current_tab_number = (VimCurrentTabNumber(),)
	current_buffer_number = (VimCurrentBufferNumber(),)
	current_window_number = (VimCurrentWindowNumber(),)
	tab_amount = (VimTabAmount(),)
	textwidth = (VimBufferOption('textwidth'),)
	stl_winlist = (VimStlWinList(),)
	editor_overrides = (EditorOverrides(),)
	editor_encoding = (EditorEncoding(),)
	list_buffers = (EditorBufferList(),)
	list_tabs = (EditorTabList(),)
	list_windows = (EditorWindowList(),)

	types = Editor.types.copy()
	types.update(
		paste_indicator='bool',
		buffer_type='ascii',
		window_title='str',
		readonly_indicator='bool',
		current_tab_number='int',
		current_buffer_number='int',
		current_window_number='int',
		textwidth='int',
		stl_winlist='intintstrlistlist',
	)

	converters = Editor.converters.copy()
	converters.update(
		intintstrlistlist=lambda l: [[[int(a), int(b), VimEditor.converters['str'](c)] for a, b, c in i]
		                             for i in l],
	)


class VimVimEditor(VimEditor):
	converters = VimEditor.converters.copy()
	converters.update(
		bool=lambda b: bool(int(b)),
		int=lambda n: int(n),
	)

	edconverters = dict((
		(k, v.get('tovim', None) or v['toed'])
		for k, v in ED_TO_VIM.items()
		if 'tovim' in v or 'toed' in v
	))

	@classmethod
	def toed(cls, obj, **kwargs):
		'''Convert given :py:class:`powerline.editors.EditorObj` to VimL

		See :py:func:`finish_kwargs` for a list of ``kwargs`` parameters.

		:return: VimL string obtained from given AST.
		'''
		if not kwargs.get('finished'):
			finkwargs = updated(kwargs, finished=True)
			kwargs = finish_kwargs(
				kwargs,
				vval=cls.toed(VimVVar('val'), **finkwargs),
				cache=cls.toed(VimGlobalVar('_powerline_cache'), **finkwargs),
				buffer_cache=cls.toed(VimGlobalVar('_powerline_buffer_cache'), **finkwargs),
			)
		return super(VimVimEditor, cls).toed(obj, **kwargs)

	@classmethod
	def compile_reqs_dict(cls, reqs_dict, **kwargs):
		'''Convert a dictionary with requirements to a VimL expression

		:param list reqs_dict:
			List of requirements. See 
			:py:func:`powerline.editors.reqss_to_reqs_dict` for more details.
		:param dict kwargs:
			Whatever keyword arguments need to be passed to 
			:py:meth:`powerline.editors.Editor.toed`.

		:return:
			A tuple with two items:

			#. VimL expression which evaluates to a dictionary ``{req_name: 
			   req_value}``. Callable requirements are skipped and need to be 
			   checked separately if possible.
			#. Python function which takes the resulting object and converts it to 
			   proper types.
		'''
		code = ['{']
		conv_code = ['lambda d: {']
		gvars = {}
		for k, v in reqs_dict.items():
			code += [
				cls.toed(EditorStr(k), **kwargs)
				+ ':'
				+ cls.toed(v[0][0], **kwargs),
				','
			]
			conv_code += [
				repr(k) + ':'
			]
			if v[1] in cls.converters:
				gvars['conv_' + v[1]] = cls.converters[v[1]]
				conv_code.append('conv_{0}(d[{1!r}])'.format(v[1], k))
			else:
				conv_code.append('d[{0!r}]'.format(k))
			conv_code.append(',')
		code[-1] = '}'
		conv_code[-1] = '}'
		return ''.join(code), eval('\n'.join(code), gvars)

	@classmethod
	def compile_themes_getter(cls, local_themes, **kwargs):
		'''Convert a list of local themes to a VimL expression

		:param list local_themes:
			List of local themes. Each local theme is a 2-tuple: ``(matcher, 
			theme_desc)``, where ``matcher`` is either 
			a :py:class:`powerline.editors.EditorObj` instance or a callable that 
			takes two keyword arguments: ``matcher_info`` and ``pl`` and returns 
			a boolean value.

			``theme_desc`` is a dictionary at least with the ``theme`` key which 
			contains :py:class:`powerline.theme.Theme` object.
		:param dict kwargs:
			Whatever keyword arguments need to be passed to :py:func:`tovim`.

		:return:
			Tuple with two values:

			#. VimL expression which evaluates to an index in ``local_themes`` 
			   list. This index starts with 1, 0 will be returned in case 
			   nothing was matched successfully.
			#. Python lambda object which returns the same thing. Is to be used 
			   in case VimL expression evaluated to zero.
		'''
		code = []
		pycode = ['lambda pl, matcher_info: (']
		for i, m in enumerate(local_themes):
			matcher = m[0]
			if callable(matcher):
				pycode += [
					'{i} if local_themes[{i}][0](pl, matcher_info) else'.format(i=i)
				]
			elif matcher is None:
				pass
			else:
				code += [cls.toed(matcher, **kwargs) + '?' + str(i + 1) + ':']
		pycode += ['0)']
		code += ['0']
		return ''.join(code), eval('\n'.join(pycode), {'local_themes': local_themes})


class VimPyEditor(VimEditor):
	edconverters = dict((
		(k, v.get('tovimpy', None) or v['toed'])
		for k, v in ED_TO_VIM.items()
		if 'tovimpy' in v or 'toed' in v
	))

	@classmethod
	def toed(cls, obj, **kwargs):
		'''Convert given :py:class:`powerline.editors.EditorObj` to Python

		See :py:func:`finish_kwargs` for a list of ``kwargs`` parameters.

		:return: Python code (string) obtained from given AST.
		'''
		kwargs = finish_kwargs(kwargs)
		return super(VimPyEditor, cls).toed(obj, **kwargs)

	@classmethod
	def compile_reqs_dict(cls, reqs_dict, vim_funcs, vim, **kwargs):
		'''Convert a dictionary with requirements to a Python lambda object

		:param list reqs_dict:
			List of requirements. See 
			:py:func:`powerline.editors.reqss_to_reqs_dict` for more details.
		:param VimFuncsDict vim_funcs:
			:py:class:`VimFuncsDict` instance. Needed to provide ``vim_funcs`` 
			global value to the generated lambda.
		:param module vim:
			Vim module.
		:param dict kwargs:
			Whatever keyword arguments need to be passed to 
			:py:meth:`powerline.editors.Editor.toed`.

		:return:
			Lambda object with all of the necessary globals attached. Returned 
			lambda takes three arguments: ``buffer``, ``window`` and ``tabpage``. 
			Supplied objects must have :py:class:`vim.Buffer`, 
			:py:class:`vim.Window` and :py:class:`vim.TabPage` types respectively.

			Returned lambda returns a dictionary ``{req_name: req_value}``.
		'''
		code = ['lambda buffer, window, tabpage: {', '']
		gvars = updated(init_globals, {
			'vim': vim,
			'vim_funcs': vim_funcs,
		})
		for k, v in reqs_dict.items():
			pyexpr = cls.toed(v[0][0], **kwargs)
			if v[1] in cls.converters:
				pyexpr = 'conv_' + v[1] + '(' + pyexpr + ')'
				gvars['conv_' + v[1]] = cls.converters[v[1]]
			code += [
				repr(k)
				+ ':'
				+ pyexpr,
				','
			]
		code[-1] = '}'
		ret = eval('\n'.join(code), gvars)
		ret.source = code
		return ret

	@classmethod
	def compile_themes_getter(cls, local_themes, vim_funcs, vim, **kwargs):
		'''Convert a list of local themes to a Python lambda object

		:param list local_themes:
			List of local themes. Each local theme is a 2-tuple: ``(matcher, 
			theme_desc)``, where ``matcher`` is either 
			a :py:class:`powerline.editors.EditorObj` instance or a callable that 
			takes two keyword arguments: ``matcher_info`` and ``pl`` and returns 
			a boolean value.

			``theme_desc`` is a dictionary at least with the ``theme`` key which 
			contains :py:class:`powerline.theme.Theme` object.
		:param VimFuncsDict vim_funcs:
			:py:class:`VimFuncsDict` instance. Needed to provide ``vim_funcs`` 
			global value to the generated lambda.
		:param module vim:
			Vim module.
		:param dict kwargs:
			Whatever keyword arguments need to be passed to :py:func:`tovimpy`.

		:return:
			Lambda object with all of the necessary globals attached. Returned 
			lambda takes six arguments: ``pl``, ``matcher_info``, ``theme``, 
			``buffer``, ``window`` and ``tabpage``. Last three arguments must have 
			:py:class:`vim.Buffer`, :py:class:`vim.Window` and 
			:py:class:`vim.TabPage` types respectively. ``pl`` and ``matcher_info`` 
			are keys used only for callable matcher objects. ``theme`` is the 
			default :py:class:`powerline.theme.Theme` object that will be returned 
			in case nothing was matched.

			Returned lambda returns matched theme object 
			(:py:class:`powerline.theme.Theme`). ``local_themes`` list copy is saved 
			in lambda globals.
		'''
		code = ['lambda pl, matcher_info, theme, buffer, window, tabpage: (']
		for i, m in enumerate(local_themes):
			matcher, theme = m
			if callable(matcher):
				code += [
					'local_themes[{0}][1]'.format(i),
					'if local_themes[i][0](pl=pl, matcher_info=matcher_info) else',
				]
			elif matcher is not None:
				code += [
					'local_themes[{0}][1]'.format(i),
					'if ' + cls.toed(matcher, **kwargs) + ' else',
				]
		code += ['theme', ')']
		return eval('\n'.join(code), updated(init_globals, {
			'vim': vim,
			'vim_funcs': vim_funcs,
			'local_themes': local_themes[:],
		}))


init_globals = {
	're': re,
	'updated': updated,
	'list': list,
	'str': str,
	'chain': chain,
	'basename': os.path.basename,
}


class VimFuncsDict(defaultdict):
	'''Dictionary that contains references to Vim functions

	References are automatically generated: if ``vim_funcs[key]`` is not present 
	(none are present by default) then it is created using :py:class:`vim.Function`(key).

	:param module vim:
		Vim module.
	'''

	def __new__(cls, vim, *args, **kwargs):
		self = defaultdict.__new__(cls, None, *args, **kwargs)
		self.vim = vim
		return self

	def __init__(self, vim, *args, **kwargs):
		super(VimFuncsDict, self).__init__(None, *args, **kwargs)

	def __missing__(self, name):
		self[name] = func = self.vim.Function(name)
		return func


if __name__ == '__main__':
	import sys

	for attr in dir(VimEditor):
		aval = getattr(VimEditor, attr)
		if isinstance(aval, tuple) and aval:
			sys.stdout.write('{0:<23} vi: '.format(attr))
			sys.stdout.flush()
			print(VimVimEditor.toed(aval[0], tabscope=True, parameters={}))
			sys.stdout.write('{0:<23} py: '.format(''))
			print(VimPyEditor.toed(aval[0], tabscope=True, parameters={}))
			if len(aval) > 1:
				sys.stdout.write('{0:<23} vi: '.format(''))
				print(VimVimEditor.toed(aval[-1], tabscope=True, parameters={}))
				sys.stdout.write('{0:<23} py: '.format(''))
				print(VimPyEditor.toed(aval[-1], tabscope=True, parameters={}))
