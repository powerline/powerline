# vim:fileencoding=utf-8:noet
_log = []
vars = {}
vvars = {'version': 703}
_tabpage = 0
_mode = 'n'
_buf_purge_events = set()
options = {
	'paste': 0,
	'ambiwidth': 'single',
	'columns': 80,
	'encoding': 'utf-8',
}
_last_bufnr = 0
_highlights = {}
from collections import defaultdict as _defaultdict
_environ = _defaultdict(lambda: '')
del _defaultdict


_thread_id = None


def _set_thread_id():
	global _thread_id
	from threading import current_thread
	_thread_id = current_thread().ident


# Assuming import is done from the main thread
_set_thread_id()


def _print_log():
	for item in _log:
		print (item)
	_log[:] = ()


def _vim(func):
	from functools import wraps
	from threading import current_thread

	@wraps(func)
	def f(*args, **kwargs):
		global _thread_id
		if _thread_id != current_thread().ident:
			raise RuntimeError('Accessing vim from separate threads is not allowed')
		_log.append((func.__name__, args))
		return func(*args, **kwargs)

	return f


def _unicode(func):
	from functools import wraps
	import sys

	if sys.version_info < (3,):
		return func

	@wraps(func)
	def f(*args, **kwargs):
		from powerline.lib.unicode import u
		ret = func(*args, **kwargs)
		if isinstance(ret, bytes):
			ret = u(ret)
		return ret

	return f


class _Buffers(object):
	@_vim
	def __init__(self):
		self.d = {}

	@_vim
	def __len__(self):
		return len(self.d)

	@_vim
	def __getitem__(self, item):
		return self.d[item]

	@_vim
	def __setitem__(self, item, value):
		self.d[item] = value

	@_vim
	def __iter__(self):
		return iter(self.d.values())

	@_vim
	def __contains__(self, item):
		return item in self.d

	@_vim
	def _keys(self):
		return self.d.keys()

	@_vim
	def _pop(self, *args, **kwargs):
		return self.d.pop(*args, **kwargs)


buffers = _Buffers()


class _ObjList(object):
	@_vim
	def __init__(self, objtype):
		self.l = []
		self.objtype = objtype

	@_vim
	def __getitem__(self, item):
		return self.l[item - int(item > 0)]

	@_vim
	def __len__(self):
		return len(self.l)

	@_vim
	def __iter__(self):
		return iter(self.l)

	@_vim
	def _pop(self, idx):
		obj = self.l.pop(idx - 1)
		for moved_obj in self.l[idx - 1:]:
			moved_obj.number -= 1
		return obj

	@_vim
	def _append(self, *args, **kwargs):
		return self.l.append(*args, **kwargs)

	@_vim
	def _new(self, *args, **kwargs):
		number = len(self) + 1
		new_obj = self.objtype(number, *args, **kwargs)
		self._append(new_obj)
		return new_obj


def _construct_result(r):
	import sys
	if sys.version_info < (3,):
		return r
	else:
		if isinstance(r, str):
			return r.encode('utf-8')
		elif isinstance(r, list):
			return [_construct_result(i) for i in r]
		elif isinstance(r, dict):
			return dict((
				(_construct_result(k), _construct_result(v))
				for k, v in r.items()
			))
		return r


def _str_func(func):
	from functools import wraps

	@wraps(func)
	def f(*args, **kwargs):
		return _construct_result(func(*args, **kwargs))
	return f


def _log_print():
	import sys
	for entry in _log:
		sys.stdout.write(repr(entry) + '\n')


_current_group = None
_on_wipeout = []


@_vim
def command(cmd):
	global _current_group
	cmd = cmd.lstrip()
	if cmd.startswith('let g:'):
		import re
		varname, value = re.compile(r'^let g:(\w+)\s*=\s*(.*)').match(cmd).groups()
		vars[varname] = value
	elif cmd.startswith('hi '):
		sp = cmd.split()
		_highlights[sp[1]] = sp[2:]
	elif cmd.startswith('augroup'):
		augroup = cmd.partition(' ')[2]
		if augroup.upper() == 'END':
			_current_group = None
		else:
			_current_group = augroup
	elif cmd.startswith('autocmd'):
		rest = cmd.partition(' ')[2]
		auevent, rest = rest.partition(' ')[::2]
		pattern, aucmd = rest.partition(' ')[::2]
		if auevent != 'BufWipeout' or pattern != '*':
			raise NotImplementedError
		import sys
		if sys.version_info < (3,):
			if not aucmd.startswith(':python '):
				raise NotImplementedError
		else:
			if not aucmd.startswith(':python3 '):
				raise NotImplementedError
		_on_wipeout.append(aucmd.partition(' ')[2])
	elif cmd.startswith('set '):
		if cmd.startswith('set statusline='):
			options['statusline'] = cmd[len('set statusline='):]
		elif cmd.startswith('set tabline='):
			options['tabline'] = cmd[len('set tabline='):]
		else:
			raise NotImplementedError(cmd)
	else:
		raise NotImplementedError(cmd)


@_vim
@_unicode
def eval(expr):
	if expr.startswith('g:'):
		return vars[expr[2:]]
	elif expr.startswith('v:'):
		return vvars[expr[2:]]
	elif expr.startswith('&'):
		return options[expr[1:]]
	elif expr.startswith('$'):
		return _environ[expr[1:]]
	elif expr.startswith('PowerlineRegisterCachePurgerEvent'):
		_buf_purge_events.add(expr[expr.find('"') + 1:expr.rfind('"') - 1])
		return '0'
	elif expr.startswith('exists('):
		return '0'
	elif expr.startswith('getwinvar('):
		import re
		match = re.match(r'^getwinvar\((\d+), "(\w+)"\)$', expr)
		if not match:
			raise NotImplementedError(expr)
		winnr = int(match.group(1))
		varname = match.group(2)
		return _emul_getwinvar(winnr, varname)
	elif expr.startswith('has_key('):
		import re
		match = re.match(r'^has_key\(getwinvar\((\d+), ""\), "(\w+)"\)$', expr)
		if match:
			winnr = int(match.group(1))
			varname = match.group(2)
			return 0 + (varname in current.tabpage.windows[winnr].vars)
		else:
			match = re.match(r'^has_key\(gettabwinvar\((\d+), (\d+), ""\), "(\w+)"\)$', expr)
			if not match:
				raise NotImplementedError(expr)
			tabnr = int(match.group(1))
			winnr = int(match.group(2))
			varname = match.group(3)
			return 0 + (varname in tabpages[tabnr].windows[winnr].vars)
	elif expr == 'getbufvar("%", "NERDTreeRoot").path.str()':
		import os
		assert os.path.basename(current.buffer.name).startswith('NERD_tree_')
		return '/usr/include'
	elif expr == 'tabpagenr()':
		return current.tabpage.number
	elif expr == 'tabpagenr("$")':
		return len(tabpages)
	elif expr.startswith('tabpagewinnr('):
		tabnr = int(expr[len('tabpagewinnr('):-1])
		return tabpages[tabnr].window.number
	elif expr.startswith('tabpagebuflist('):
		import re
		match = re.match(r'tabpagebuflist\((\d+)\)\[(\d+)\]', expr)
		tabnr = int(match.group(1))
		winnr = int(match.group(2)) + 1
		return tabpages[tabnr].windows[winnr].buffer.number
	elif expr.startswith('gettabwinvar('):
		import re
		match = re.match(r'gettabwinvar\((\d+), (\d+), "(\w+)"\)', expr)
		tabnr = int(match.group(1))
		winnr = int(match.group(2))
		varname = match.group(3)
		return tabpages[tabnr].windows[winnr].vars[varname]
	elif expr.startswith('type(function('):
		import re
		match = re.match(r'^type\(function\("([^"]+)"\)\) == 2$', expr)
		if not match:
			raise NotImplementedError(expr)
		return 0
	raise NotImplementedError(expr)


@_vim
def bindeval(expr):
	if expr == 'g:':
		return vars
	elif expr == '{}':
		return {}
	elif expr == '[]':
		return []
	import re
	match = re.compile(r'^function\("([^"\\]+)"\)$').match(expr)
	if match:
		return globals()['_emul_' + match.group(1)]
	else:
		raise NotImplementedError


@_vim
@_str_func
def _emul_mode(*args):
	if args and args[0]:
		return _mode
	else:
		return _mode[0]


@_vim
@_str_func
def _emul_getbufvar(bufnr, varname):
	import re
	if varname[0] == '&':
		if bufnr == '%':
			bufnr = current.buffer.number
		if bufnr not in buffers:
			return ''
		try:
			return buffers[bufnr].options[varname[1:]]
		except KeyError:
			try:
				return options[varname[1:]]
			except KeyError:
				return ''
	elif re.match('^[a-zA-Z_]+$', varname):
		if bufnr == '%':
			bufnr = current.buffer.number
		if bufnr not in buffers:
			return ''
		return buffers[bufnr].vars[varname]
	raise NotImplementedError


@_vim
@_str_func
def _emul_getwinvar(winnr, varname):
	return current.tabpage.windows[winnr].vars.get(varname, '')


@_vim
def _emul_setwinvar(winnr, varname, value):
	current.tabpage.windows[winnr].vars[varname] = value


@_vim
def _emul_virtcol(expr):
	if expr == '.':
		return current.window.cursor[1] + 1
	if isinstance(expr, list) and len(expr) == 3:
		return expr[-2] + expr[-1]
	raise NotImplementedError


_v_pos = None


@_vim
def _emul_getpos(expr):
	if expr == '.':
		return [0, current.window.cursor[0] + 1, current.window.cursor[1] + 1, 0]
	if expr == 'v':
		return _v_pos or [0, current.window.cursor[0] + 1, current.window.cursor[1] + 1, 0]
	raise NotImplementedError


@_vim
@_str_func
def _emul_fnamemodify(path, modstring):
	import os
	_modifiers = {
		'~': lambda path: path.replace(os.environ['HOME'].encode('utf-8'), b'~') if path.startswith(os.environ['HOME'].encode('utf-8')) else path,
		'.': lambda path: (lambda tpath: path if tpath[:3] == b'..' + os.sep.encode() else tpath)(os.path.relpath(path)),
		't': lambda path: os.path.basename(path),
		'h': lambda path: os.path.dirname(path),
	}

	for mods in modstring.split(':')[1:]:
		path = _modifiers[mods](path)
	return path


@_vim
@_str_func
def _emul_expand(expr):
	global _abuf
	if expr == '<abuf>':
		return _abuf or current.buffer.number
	raise NotImplementedError


@_vim
def _emul_bufnr(expr):
	if expr == '$':
		return _last_bufnr
	raise NotImplementedError


@_vim
def _emul_exists(ident):
	if ident.startswith('g:'):
		return ident[2:] in vars
	elif ident.startswith(':'):
		return 0
	raise NotImplementedError


@_vim
def _emul_line2byte(line):
	buflines = current.buffer._buf_lines
	if line == len(buflines) + 1:
		return sum((len(s) for s in buflines)) + 1
	raise NotImplementedError


@_vim
def _emul_line(expr):
	cursorline = current.window.cursor[0] + 1
	numlines = len(current.buffer._buf_lines)
	if expr == 'w0':
		return max(cursorline - 5, 1)
	if expr == 'w$':
		return min(cursorline + 5, numlines)
	raise NotImplementedError


@_vim
@_str_func
def _emul_strtrans(s):
	# FIXME Do more replaces
	return s.replace(b'\xFF', b'<ff>')


@_vim
@_str_func
def _emul_bufname(bufnr):
	try:
		return buffers[bufnr]._name or b''
	except KeyError:
		return b''


_window_id = 0


class _Window(object):
	def __init__(self, number, buffer=None, cursor=(1, 0), width=80):
		global _window_id
		self.cursor = cursor
		self.width = width
		self.number = number
		if buffer:
			if type(buffer) is _Buffer:
				self.buffer = buffer
			else:
				self.buffer = _Buffer(**buffer)
		else:
			self.buffer = _Buffer()
		_window_id += 1
		self._window_id = _window_id
		self.options = {}
		self.vars = {
			'powerline_window_id': self._window_id,
		}

	def __repr__(self):
		return '<window ' + str(self.number - 1) + '>'


class _Tabpage(object):
	def __init__(self, number):
		self.windows = _ObjList(_Window)
		self.number = number

	def _new_window(self, **kwargs):
		self.window = self.windows._new(**kwargs)
		return self.window

	def _close_window(self, winnr, open_window=True):
		curwinnr = self.window.number
		win = self.windows._pop(winnr)
		if self.windows and winnr == curwinnr:
			self.window = self.windows[-1]
		elif open_window:
			current.tabpage._new_window()
		return win

	def _close(self):
		global _tabpage
		while self.windows:
			self._close_window(1, False)
		tabpages._pop(self.number)
		_tabpage = len(tabpages)


tabpages = _ObjList(_Tabpage)


_abuf = None


class _Buffer(object):
	def __init__(self, name=None):
		global _last_bufnr
		_last_bufnr += 1
		bufnr = _last_bufnr
		self.number = bufnr
		# FIXME Use unicode() for python-3
		self.name = name
		self.vars = {'changedtick': 1}
		self.options = {
			'modified': 0,
			'readonly': 0,
			'fileformat': 'unix',
			'filetype': '',
			'buftype': '',
			'fileencoding': 'utf-8',
			'textwidth': 80,
		}
		self._buf_lines = ['']
		self._undostate = [self._buf_lines[:]]
		self._undo_written = len(self._undostate)
		buffers[bufnr] = self

	@property
	def name(self):
		import sys
		if sys.version_info < (3,):
			return self._name
		else:
			return str(self._name, 'utf-8') if self._name else None

	@name.setter
	def name(self, name):
		if name is None:
			self._name = None
		else:
			import os
			if type(name) is not bytes:
				name = name.encode('utf-8')
			if b':/' in name:
				self._name = name
			else:
				self._name = os.path.abspath(name)

	def __getitem__(self, line):
		return self._buf_lines[line]

	def __setitem__(self, line, value):
		self.options['modified'] = 1
		self.vars['changedtick'] += 1
		self._buf_lines[line] = value
		from copy import copy
		self._undostate.append(copy(self._buf_lines))

	def __setslice__(self, *args):
		self.options['modified'] = 1
		self.vars['changedtick'] += 1
		self._buf_lines.__setslice__(*args)
		from copy import copy
		self._undostate.append(copy(self._buf_lines))

	def __getslice__(self, *args):
		return self._buf_lines.__getslice__(*args)

	def __len__(self):
		return len(self._buf_lines)

	def __repr__(self):
		return '<buffer ' + str(self.name) + '>'

	def __del__(self):
		global _abuf
		bufnr = self.number
		try:
			import __main__
		except ImportError:
			pass
		except RuntimeError:
			# Module may have already been garbage-collected
			pass
		else:
			if _on_wipeout:
				_abuf = bufnr
				try:
					for event in _on_wipeout:
						exec(event, __main__.__dict__)
				finally:
					_abuf = None


class _Current(object):
	@property
	def buffer(self):
		return self.window.buffer

	@property
	def window(self):
		return self.tabpage.window

	@property
	def tabpage(self):
		return tabpages[_tabpage - 1]


current = _Current()


_dict = None


@_vim
def _init():
	global _dict

	if _dict:
		return _dict

	_dict = {}
	for varname, value in globals().items():
		if varname[0] != '_':
			_dict[varname] = value
	_tabnew()
	return _dict


@_vim
def _get_segment_info():
	mode_translations = {
		chr(ord('V') - 0x40): '^V',
		chr(ord('S') - 0x40): '^S',
	}
	mode = _mode
	mode = mode_translations.get(mode, mode)
	window = current.window
	buffer = current.buffer
	tabpage = current.tabpage
	return {
		'window': window,
		'winnr': window.number,
		'buffer': buffer,
		'bufnr': buffer.number,
		'tabpage': tabpage,
		'tabnr': tabpage.number,
		'window_id': window._window_id,
		'mode': mode,
		'encoding': options['encoding'],
	}


@_vim
def _launch_event(event):
	pass


@_vim
def _start_mode(mode):
	global _mode
	if mode == 'i':
		_launch_event('InsertEnter')
	elif _mode == 'i':
		_launch_event('InsertLeave')
	_mode = mode


@_vim
def _undo():
	if len(current.buffer._undostate) == 1:
		return
	buffer = current.buffer
	buffer._undostate.pop(-1)
	buffer._buf_lines = buffer._undostate[-1]
	if buffer._undo_written == len(buffer._undostate):
		buffer.options['modified'] = 0


@_vim
def _edit(name=None):
	if current.buffer.name is None:
		buffer = current.buffer
		buffer.name = name
	else:
		buffer = _Buffer(name)
		current.window.buffer = buffer


@_vim
def _tabnew(name=None):
	global windows
	global _tabpage
	tabpage = tabpages._new()
	windows = tabpage.windows
	_tabpage = len(tabpages)
	_new(name)
	return tabpage


@_vim
def _new(name=None):
	current.tabpage._new_window(buffer={'name': name})


@_vim
def _split():
	current.tabpage._new_window(buffer=current.buffer)


@_vim
def _close(winnr, wipe=True):
	win = current.tabpage._close_window(winnr)
	if wipe:
		for w in current.tabpage.windows:
			if w.buffer.number == win.buffer.number:
				break
		else:
			_bw(win.buffer.number)


@_vim
def _bw(bufnr=None):
	bufnr = bufnr or current.buffer.number
	winnr = 1
	for win in current.tabpage.windows:
		if win.buffer.number == bufnr:
			_close(winnr, wipe=False)
		winnr += 1
	buffers._pop(bufnr)
	if not buffers:
		_Buffer()
	_b(max(buffers._keys()))


@_vim
def _b(bufnr):
	current.window.buffer = buffers[bufnr]


@_vim
def _set_cursor(line, col):
	current.window.cursor = (line, col)
	if _mode == 'n':
		_launch_event('CursorMoved')
	elif _mode == 'i':
		_launch_event('CursorMovedI')


@_vim
def _get_buffer():
	return current.buffer


@_vim
def _set_bufoption(option, value, bufnr=None):
	buffers[bufnr or current.buffer.number].options[option] = value
	if option == 'filetype':
		_launch_event('FileType')


class _WithNewBuffer(object):
	def __init__(self, func, *args, **kwargs):
		self.call = lambda: func(*args, **kwargs)

	def __enter__(self):
		self.call()
		self.bufnr = current.buffer.number
		return _get_segment_info()

	def __exit__(self, *args):
		_bw(self.bufnr)


@_vim
def _set_dict(d, new, setfunc=None):
	if not setfunc:
		def setfunc(k, v):
			d[k] = v

	old = {}
	na = []
	for k, v in new.items():
		try:
			old[k] = d[k]
		except KeyError:
			na.append(k)
		setfunc(k, v)
	return old, na


class _WithBufOption(object):
	def __init__(self, **new):
		self.new = new

	def __enter__(self):
		self.buffer = current.buffer
		self.old = _set_dict(self.buffer.options, self.new, _set_bufoption)[0]

	def __exit__(self, *args):
		self.buffer.options.update(self.old)


class _WithMode(object):
	def __init__(self, new):
		self.new = new

	def __enter__(self):
		self.old = _mode
		_start_mode(self.new)
		return _get_segment_info()

	def __exit__(self, *args):
		_start_mode(self.old)


class _WithDict(object):
	def __init__(self, d, **new):
		self.new = new
		self.d = d

	def __enter__(self):
		self.old, self.na = _set_dict(self.d, self.new)

	def __exit__(self, *args):
		self.d.update(self.old)
		for k in self.na:
			self.d.pop(k)


class _WithSplit(object):
	def __enter__(self):
		_split()

	def __exit__(self, *args):
		_close(2, wipe=False)


class _WithBufName(object):
	def __init__(self, new):
		self.new = new

	def __enter__(self):
		import os
		buffer = current.buffer
		self.buffer = buffer
		self.old = buffer.name
		buffer.name = self.new

	def __exit__(self, *args):
		self.buffer.name = self.old


class _WithNewTabPage(object):
	def __init__(self, *args, **kwargs):
		self.args = args
		self.kwargs = kwargs

	def __enter__(self):
		self.tab = _tabnew(*self.args, **self.kwargs)

	def __exit__(self, *args):
		self.tab._close()


class _WithGlobal(object):
	def __init__(self, **kwargs):
		self.kwargs = kwargs

	def __enter__(self):
		self.empty = object()
		self.old = dict(((key, globals().get(key, self.empty)) for key in self.kwargs))
		globals().update(self.kwargs)

	def __exit__(self, *args):
		for k, v in self.old.items():
			if v is self.empty:
				globals().pop(k, None)
			else:
				globals()[k] = v


@_vim
def _with(key, *args, **kwargs):
	if key == 'buffer':
		return _WithNewBuffer(_edit, *args, **kwargs)
	elif key == 'bufname':
		return _WithBufName(*args, **kwargs)
	elif key == 'mode':
		return _WithMode(*args, **kwargs)
	elif key == 'bufoptions':
		return _WithBufOption(**kwargs)
	elif key == 'options':
		return _WithDict(options, **kwargs)
	elif key == 'globals':
		return _WithDict(vars, **kwargs)
	elif key == 'wvars':
		return _WithDict(current.window.vars, **kwargs)
	elif key == 'environ':
		return _WithDict(_environ, **kwargs)
	elif key == 'split':
		return _WithSplit()
	elif key == 'tabpage':
		return _WithNewTabPage(*args, **kwargs)
	elif key == 'vpos':
		return _WithGlobal(_v_pos=[0, kwargs['line'], kwargs['col'], kwargs['off']])


class error(Exception):
	pass
