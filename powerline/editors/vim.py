# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import re
import os

from collections import defaultdict
from itertools import chain

from powerline.lib.dict import updated
from powerline.lib.unicode import unicode
from powerline.editors import (Editor, param_updated, iterparam_updated,
                               EditorObj, EditorBinaryOp, EditorTernaryOp,
                               EditorEmpty, EditorIndex, EditorFunc, EditorStr,
                               EditorList, EditorNone, EditorNamedThing,
                               EditorBufferName, EditorLastBufLine,
                               EditorParameter, EditorWinPos, EditorAny,
                               EditorUnaryOp, EditorNot, EditorBufferList,
                               EditorFilter, EditorCached, EditorDict,
                               EditorOverrides, EditorEncoding,
                               EditorBufferNameBase, EditorMap,
                               EditorWindowList, EditorTabList,
                               EditorWindowBuffer, EditorTabWindowBuffer,
                               EditorTabWindow, EditorTabAmount, EditorNumber,
                               toedobj)


def finish_kwargs(kwargs, vval=None, cache=None, buffer_cache=None, paramfunc=(lambda s: s), toed=None):
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
	:param func toed:
		Function used to convert :py:class:`powerline.editors.EditorObj` 
		instances to strings suitable for ``kwargs['parameters']`` dictionary.

	:return:
		A modified copy of ``kwargs`` dictionary or ``kwargs`` dictionary 
		itself if it was already finished.
	'''
	if kwargs.get('finished'):
		return kwargs
	kwargs = kwargs.copy()
	kwargs.setdefault('tabscope', False)
	kwargs['finished'] = True
	try:
		kwargs['parameters'] = kwargs['parameters'].copy()
	except KeyError:
		kwargs['parameters'] = {}
	kwargs['parameters'].setdefault('vval', vval or 'i')
	kwargs['parameters'].setdefault('cache', cache or 'cache')
	kwargs['parameters'].setdefault('buffer_cache', buffer_cache or 'buffer_cache')
	kwargs['parameters'].setdefault('tabpage', paramfunc('tabpage'))
	if kwargs['tabscope'] and 'window' not in kwargs['parameters']:
		kwargs['parameters']['window'] = toed(EditorTabWindow(), **kwargs)
	else:
		kwargs['parameters'].setdefault('window', paramfunc('window'))
	if kwargs['tabscope'] and 'buffer' not in kwargs['parameters']:
		kwargs['parameters']['buffer'] = toed(EditorTabWindowBuffer(), **kwargs)
	else:
		kwargs['parameters'].setdefault('buffer', paramfunc('buffer'))
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


class VimTabNumber(EditorObj):
	pass


class VimBufferNumber(EditorObj):
	pass


class VimWindowNumber(EditorObj):
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


def raising(exc):
	raise exc


VIM_VIM_OP_DEFAULT = (lambda self, toed, **kw:
	self.op.join((toed(child, **kw) for child in self.children)))
VIM_VIM_OPS = defaultdict(lambda: VIM_VIM_OP_DEFAULT, {
	'=~#': (lambda self, toed, **kw: r"(({0}) =~# '\v'.({1}))".format(
		toed(self.children[0], **kw),
		toed(self.children[1], **kw),
	)),
	'==': (lambda self, toed, **kw:
		'(' + ('==#'.join((toed(child, **kw) for child in self.children))) + ')'),
	'+l': (lambda self, toed, **kw:
		'(' + '+'.join((toed(child, **kw) for child in self.children)) + ')'),
	'|': (lambda self, toed, **kw:
		'(' + '||'.join((toed(child, **kw) for child in self.children)) + ')'),
	'&': (lambda self, toed, **kw:
		'(' + '&&'.join((toed(child, **kw) for child in self.children)) + ')'),
	'^': (lambda self, toed, **kw:
		'xor(' + ','.join((toed(child, **kw) for child in self.children)) + ')'),
})


VIM_PY_OP_DEFAULT = VIM_VIM_OP_DEFAULT
VIM_PY_OPS = defaultdict(lambda: VIM_PY_OP_DEFAULT, {
	'=~#': (lambda self, toed, **kw: 'bool(re.search({1}, {0}))'.format(
		toed(self.children[0], **kw),
		toed(self.children[1], **kw),
	)),
	'.': (lambda self, toed, **kw:
		'"".join((str(i) for i in ({0},)))'.format(
			','.join(toed(child, **kw) for child in self.children)
		)
	),
	'+l': (lambda self, toed, **kw: (
		'list(chain(' + ','.join((toed(child, **kw) for child in self.children)) + '))'
	)),
	'|': (lambda self, toed, **kw:
		' or '.join((toed(child, **kw) for child in self.children))),
	'&': (lambda self, toed, **kw:
		' and '.join((toed(child, **kw) for child in self.children))),
	'^': (lambda self, toed, **kw:
		raising(NotImplementedError('Logical xor is not implemented'))),
})


ED_TO_VIM = {
	EditorObj: {
		'tovim': lambda self, toed, **kw: str(self),
		'tovimpy': lambda self, toed, **kw: repr(self),
	},
	EditorStr: {
		'tovim': lambda self, toed, **kw: (
			"'" + self.replace("'", "''") + "'"
		),
		'tovimpy': lambda self, toed, **kw: unicode.__repr__(self),
	},
	EditorNumber: {
		'tovim': lambda self, toed, **kw: int.__repr__(self),
		'tovimpy': lambda self, toed, **kw: int.__repr__(self),
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
		'tovim': lambda self, toed, **kw: VIM_VIM_OPS[self.op](self, toed, **kw),
		'tovimpy': lambda self, toed, **kw: VIM_PY_OPS[self.op](self, toed, **kw),
	},
	EditorTernaryOp: {
		'tovim': lambda self, toed, **kw: '({condition})? ({if_true}): ({if_false})'.format(
			condition=toed(self.condition, **kw),
			if_true=toed(self.if_true, **kw),
			if_false=toed(self.if_false, **kw),
		),
		'tovimpy': lambda self, toed, **kw: '(({if_true}) if ({condition}) else ({if_false}))'.format(
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
				'[' + ' : '.join((toed(idx if i == 0 else toedobj(idx - 1), **kw)
				                  for i, idx in enumerate(self.index))) + ']'
			)
		),
	},
	EditorFunc: {
		'tovim': lambda self, toed, **kw: (
			(
				'(' + toed(self.name, **kw) + ')'
				if isinstance(self.name, EditorObj) else
				self.name
			) + '(' + ', '.join((toed(arg, **kw) for arg in self.args)) + ')'
		),
		'tovimpy': lambda self, toed, **kw: (
			(
				'(' + toed(self.name, **kw) + ')'
				if isinstance(self.name, EditorObj) else
				'vim_funcs[' + repr(self.name) + ']'
			) + '(' + ', '.join((toed(arg, **kw) for arg in self.args)) + ')'
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
			EditorTernaryOp(
				EditorFunc('empty', EditorFunc('bufname', EditorParameter('buffer'))),
				b'',
				EditorFunc('fnamemodify', EditorFunc('bufname', EditorParameter('buffer')), ':p'),
			), **kw),
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
		))(self, **iterparam_updated(kw, self, toed)),
		'tovimpy': lambda self, toed, **kw: (lambda self, **kw: 'any(({0} for vval in {1}))'.format(
			toed(self.condition, **kw),
			toed(self.list, **kw)))(
				self, **iterparam_updated(kw, self, toed)
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
		))(self, **iterparam_updated(kw, self, toed)),
		'tovimpy': lambda self, toed, **kw: (lambda self, **kw: '[vval for vval in {1} if {0}]'.format(
			toed(self.condition, **kw),
			toed(self.list, **kw)))(
				self, **iterparam_updated(kw, self, toed)
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
		))(self, **iterparam_updated(kw, self, toed)),
		'tovimpy': lambda self, toed, **kw: (lambda self, **kw: '[{0} for vval in {1}]'.format(
			toed(self.expr, **kw),
			toed(self.list, **kw)))(
				self, **iterparam_updated(kw, self, toed)
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
	VimBufferNumber: {
		'tovim': lambda self, toed, **kw: kw['parameters']['buffer'],
		'tovimpy': lambda self, toed, **kw: '{buffer}.number'.format(**kw['parameters']),
	},
	VimWindowNumber: {
		'tovim': lambda self, toed, **kw: kw['parameters']['window'],
		'tovimpy': lambda self, toed, **kw: '{window}.number'.format(**kw['parameters']),
	},
	VimTabNumber: {
		'tovim': lambda self, toed, **kw: kw['parameters']['tabpage'],
		'tovimpy': lambda self, toed, **kw: '{tabpage}.number'.format(**kw['parameters']),
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
					**param_updated(kw, window=toed(VimVVar('val'), **kw))
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
		'tovim': lambda self, toed, **kw: 'get(g:, "' + self.name + '", "")',
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
	EditorTabAmount: {
		'tovim': lambda self, toed, **kw: toed(EditorFunc('tabpagenr', '$'), **kw),
		'tovimpy': lambda self, toed, **kw: 'len(vim.tabpages)',
	},
	EditorTabWindow: {
		'tovim': lambda self, toed, **kw: 'tabpagewinnr({tabpage})'.format(**kw['parameters']),
		'tovimpy': lambda self, toed, **kw: '{tabpage}.window'.format(**kw['parameters']),
	},
	EditorTabWindowBuffer: {
		'tovim': lambda self, toed, **kw: 'tabpagebuflist({tabpage})[{window}-1]'.format(**kw['parameters']),
		'tovimpy': lambda self, toed, **kw: '{window}.buffer'.format(**kw['parameters']),
	},
	EditorWindowBuffer: {
		'tovim': lambda self, toed, **kw: 'winbufnr({window})'.format(**kw['parameters']),
		'tovimpy': lambda self, toed, **kw: '{window}.buffer'.format(**kw['parameters']),
	},
}


class VimEditor(Editor):
	'''Definition of the Vim editor
	'''
	mode = (EditorFunc('mode', 1), EditorStr('nc'))
	visual_range = (
		EditorList(
			EditorFunc('getpos', 'v'),
			EditorFunc('getpos', '.')
		),
		EditorNone()
	)
	modified_indicator = (VimBufferOption('modified'),)
	# We can't use vim_getbufoption(segment_info, 'buflisted')
	# here for performance reasons. Querying the buffer options
	# through the vim python module's option attribute caused
	# vim to think it needed to update the tabline for every
	# keystroke after any event that changed the buffer's
	# options.
	listed_indicator = (EditorFunc('buflisted', VimBufferNumber()),)
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
	tab_number = (VimTabNumber(),)
	buffer_number = (VimBufferNumber(),)
	window_number = (VimWindowNumber(),)
	tab_amount = (EditorTabAmount(),)
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
		tab_amount='int',
		stl_winlist='intintbyteslistlist',
	)

	converters = Editor.converters.copy()
	converters.update(
		intintbyteslistlist=lambda l: [[int(a), int(b), c] for a, b, c in l],
	)

	const_reqs = ('mode', 'current_window_number')

	@staticmethod
	def req_to_edobj(req):
		'''Convert requirement to :py:class:`EditorObj`

		Used by :py:meth:`segments_to_reqs` to convert lister requirements 
		(values of req_dict).

		:param tuple req: Requirement to convert.

		:return: Converted requirement.
		'''
		return req[0]


class VimVimEditor(VimEditor):
	converters = VimEditor.converters.copy()
	converters.update(
		bool=lambda b: b and bool(int(b)),
		int=lambda n: int(n) if n else 0,
	)

	edconverters = dict((
		(k, v.get('tovim', None) or v['toed'])
		for k, v in ED_TO_VIM.items()
		if 'tovim' in v or 'toed' in v
	))

	const_reqs = VimEditor.const_reqs + ('stl_winlist',)

	@classmethod
	def finish_kwargs(cls, kwargs):
		'''Finish kwargs by creating a copy of it and adding necessary data

		If kwargs does not require finishing it is returned without copying.

		:param dict kwargs:
			Keyword arguments to finish.

		:return:
			New dictionary with values from kwargs and some new or kwargs 
			itself.
		'''
		if not kwargs.get('finished'):
			finkwargs = updated(kwargs, finished=True)
			kwargs = finish_kwargs(
				kwargs,
				vval=cls.toed(VimVVar('val'), **finkwargs),
				cache=cls.toed(VimGlobalVar('_powerline_cache'), **finkwargs),
				buffer_cache=cls.toed(VimGlobalVar('_powerline_buffer_cache'), **finkwargs),
				toed=cls.toed,
			)
		return kwargs

	@classmethod
	def toed(cls, obj, **kwargs):
		'''Convert given :py:class:`powerline.editors.EditorObj` to VimL

		See :py:func:`finish_kwargs` for a list of ``kwargs`` parameters.

		:return: VimL string obtained from given AST.
		'''
		return super(VimVimEditor, cls).toed(obj, **cls.finish_kwargs(kwargs))

	@classmethod
	def compile_req_type(cls, req_type, req_var, gvars, conv_code):
		'''Convert requirement type to the Python code which does the conversion

		:param req_type:
			Requirement type, string or dictionary.
		:param req_var:
			Variable which may be used to access the requirement value.
		:param dict gvars:
			Global variables. Modified to add converters there.
		:param list conv_code:
			Converted code. Modified to add code ther.
		'''
		if isinstance(req_type, dict):
			conv_code.append('    {')
			for subk, subv in req_type.items():
				conv_code.append(repr(subk) + ':')
				cls.compile_req_type(subv, '{0}[{1!r}]'.format(req_var, subk),
				                     gvars, conv_code)
				conv_code.append(',')
			conv_code[-1] += '}'
		else:
			if req_type in cls.converters:
				gvars['conv_' + req_type] = cls.converters[req_type]
				conv_code.append('    conv_{0}({1})'.format(req_type, req_var))
			else:
				conv_code.append('    ' + req_var)

	@classmethod
	def compile_reqs_dict(cls, reqs_dict, **kwargs):
		'''Convert a dictionary with requirements to a VimL expression

		:param list reqs_dict:
			List of requirements. See 
			:py:func:`powerline.editors.reqs_to_reqs_dict` for more details.
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
		kwargs = cls.finish_kwargs(kwargs)
		code = ['{']
		conv_code = ['lambda input: {']
		gvars = {}
		for k, v in reqs_dict.items():
			code.append(
				'  '
				+ cls.toed(EditorStr(k), **kwargs)
				+ ': '
				+ cls.toed(v[0][0], **kwargs)
				+ ','
			)
			conv_code.append('  ' + repr(k) + ':')
			cls.compile_req_type(v[1], 'input[{0!r}]'.format(k), gvars, conv_code)
			conv_code[-1] += ','
		code[-1] += '}'
		conv_code[-1] += '}'
		# for i, v in enumerate(conv_code):
		# 	print(i + 1, v)
		conv_code_s = '\n'.join(conv_code)
		converter = eval(conv_code_s, gvars)
		converter.source = conv_code_s
		return ''.join(code), converter

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
		kwargs = cls.finish_kwargs(kwargs)
		code = []
		pycode = ['lambda pl, matcher_info: (']
		for i, m in enumerate(local_themes):
			matcher = m[0]
			if isinstance(matcher, EditorObj):
				code += [cls.toed(matcher, **kwargs) + '?' + str(i + 1) + ':']
			elif matcher is not None:
				pycode += [
					'{i} if local_themes[{i}][0](pl=pl, matcher_info=matcher_info) else'.format(i=i)
				]
		pycode += ['0)']
		code += ['0']
		pycode_s = '\n'.join(pycode)
		themes_getter = eval(pycode_s, {'local_themes': local_themes})
		themes_getter.source = pycode_s
		return ''.join(code), themes_getter


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
		kwargs = finish_kwargs(kwargs, vval='vval', toed=cls.toed)
		return super(VimPyEditor, cls).toed(obj, **kwargs)

	@classmethod
	def compile_req_type(cls, req_type, pyexpr, gvars):
		'''Convert requirement type to the Python code which does the conversion

		:param req_type:
			Requirement type, string or dictionary.
		:param str pyexpr:
			Converted code. Modified to add code ther.
		:param dict gvars:
			Global variables. Modified to add converters there.

		:return:
			Modified pyexpr.
		'''
		if isinstance(req_type, dict):
			subexpr = ['{']
			subpyexpr = 'input'
			for subk, subv in req_type.items():
				subexpr.append('{0!r}: {1},'.format(
					subk, cls.compile_req_type(subv, subpyexpr, gvars)))
			subexpr.append('}')
			pyexpr = '(lambda input: {0})({1})'.format(' '.join(subexpr), pyexpr)
		else:
			if req_type in cls.converters:
				pyexpr = 'conv_' + req_type + '(' + pyexpr + ')'
				gvars['conv_' + req_type] = cls.converters[req_type]
		return pyexpr

	@classmethod
	def compile_reqs_dict(cls, reqs_dict, vim_funcs, vim, **kwargs):
		'''Convert a dictionary with requirements to a Python lambda object

		:param list reqs_dict:
			List of requirements. See 
			:py:func:`powerline.editors.reqs_to_reqs_dict` for more details.
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
			pyexpr = cls.compile_req_type(v[1], pyexpr, gvars)
			code.append(
				repr(k)
				+ ':'
				+ pyexpr
				+ ','
			)
		code[-1] += '}'
		# for i, v in enumerate(code):
		# 	print(i + 1, v)
		code_s = '\n'.join(code)
		ret = eval(code_s, gvars)
		ret.source = code_s
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
			if isinstance(matcher, EditorObj):
				code += [
					'local_themes[{0}][1]'.format(i),
					'if ' + cls.toed(matcher, **kwargs) + ' else',
				]
			elif matcher is not None:
				code += [
					'local_themes[{0}][1]'.format(i),
					'if local_themes[{0}][0](pl=pl, matcher_info=matcher_info) else'.format(i),
				]
		code += ['theme', ')']
		code_s = '\n'.join(code)
		ret = eval(code_s, updated(init_globals, {
			'vim': vim,
			'vim_funcs': vim_funcs,
			'local_themes': local_themes[:],
		}))
		ret.source = code_s
		return ret


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
			sys.stdout.write('{0:<23} v: '.format(attr))
			sys.stdout.flush()
			print(VimVimEditor.toed(aval[0], tabscope=True, parameters={}))
			sys.stdout.write('{0:<23} p: '.format(''))
			print(VimPyEditor.toed(aval[0], tabscope=True, parameters={}))
			if len(aval) > 1:
				sys.stdout.write('{0:<23} v: '.format(''))
				print(VimVimEditor.toed(aval[-1], tabscope=True, parameters={}))
				sys.stdout.write('{0:<23} p: '.format(''))
				print(VimPyEditor.toed(aval[-1], tabscope=True, parameters={}))
