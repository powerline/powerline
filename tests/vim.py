# vim:fileencoding=utf-8:noet
_log = []
vars = {}
vvars = {'version': 703}
_window = 0
_mode = 'n'
_buf_purge_events = set()
options = {
	'paste': 0,
	'ambiwidth': 'single',
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
	def __getitem__(self, item):
		return self.d[item]

	@_vim
	def __setitem__(self, item, value):
		self.d[item] = value

	@_vim
	def __contains__(self, item):
		return item in self.d

	@_vim
	def __nonzero__(self):
		return bool(self.d)

	@_vim
	def keys(self):
		return self.d.keys()

	@_vim
	def pop(self, *args, **kwargs):
		return self.d.pop(*args, **kwargs)


buffers = _Buffers()


class _Windows(object):
	@_vim
	def __init__(self):
		self.l = []

	@_vim
	def __getitem__(self, item):
		return self.l[item]

	@_vim
	def __setitem__(self, item, value):
		self.l[item] = value

	@_vim
	def __len__(self):
		return len(self.l)

	@_vim
	def __iter__(self):
		return iter(self.l)

	@_vim
	def __nonzero__(self):
		return not not self.l

	@_vim
	def _pop(self, *args, **kwargs):
		return self.l.pop(*args, **kwargs)

	@_vim
	def _append(self, *args, **kwargs):
		return self.l.append(*args, **kwargs)


windows = _Windows()


@_vim
def _buffer():
	return windows[_window - 1].buffer.number


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
			return dict(((_construct_result(k), _construct_result(v))
						for k, v in r.items()))
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
	elif cmd.startswith('function! Powerline_plugin_ctrlp'):
		# Ignore CtrlP updating functions
		pass
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
	else:
		raise NotImplementedError


@_vim
@_unicode
def eval(expr):
	if expr.startswith('g:'):
		return vars[expr[2:]]
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
			raise NotImplementedError
		winnr = int(match.group(1))
		varname = match.group(2)
		return _emul_getwinvar(winnr, varname)
	elif expr.startswith('has_key('):
		import re
		match = re.match(r'^has_key\(getwinvar\((\d+), ""\), "(\w+)"\)$', expr)
		if not match:
			raise NotImplementedError
		winnr = int(match.group(1))
		varname = match.group(2)
		return 0 + (varname in windows[winnr - 1].vars)
	elif expr == 'getbufvar("%", "NERDTreeRoot").path.str()':
		import os
		assert os.path.basename(buffers[_buffer()].name).startswith('NERD_tree_')
		return '/usr/include'
	raise NotImplementedError


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
			bufnr = buffers[_buffer()].number
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
			bufnr = buffers[_buffer()].number
		if bufnr not in buffers:
			return ''
		return buffers[bufnr].vars[varname]
	raise NotImplementedError


@_vim
@_str_func
def _emul_getwinvar(winnr, varname):
	return windows[winnr - 1].vars.get(varname, '')


@_vim
def _emul_setwinvar(winnr, varname, value):
	windows[winnr - 1].vars[varname] = value


@_vim
def _emul_virtcol(expr):
	if expr == '.' or isinstance(expr, list):
		return windows[_window - 1].cursor[1] + 1
	raise NotImplementedError


@_vim
def _emul_getpos(expr):
	if expr == '.' or expr == 'v':
		return [0, windows[_window - 1].cursor[0] + 1, windows[_window - 1].cursor[1] + 1, 0]
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
		return _abuf or _buffer()
	raise NotImplementedError


@_vim
def _emul_bufnr(expr):
	if expr == '$':
		return _last_bufnr
	raise NotImplementedError


@_vim
def _emul_exists(varname):
	if varname.startswith('g:'):
		return varname[2:] in vars
	raise NotImplementedError


@_vim
def _emul_line2byte(line):
	buflines = _buf_lines[_buffer()]
	if line == len(buflines) + 1:
		return sum((len(s) for s in buflines)) + 1
	raise NotImplementedError


@_vim
def _emul_line(expr):
	cursorline = windows[_window - 1].cursor[0] + 1
	numlines = len(_buf_lines[_buffer()])
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


_window_ids = [None]
_window_id = 0


class _Window(object):
	def __init__(self, buffer=None, cursor=(1, 0), width=80):
		global _window_id
		self.cursor = cursor
		self.width = width
		self.number = len(windows) + 1
		if buffer:
			if type(buffer) is _Buffer:
				self.buffer = buffer
			else:
				self.buffer = _Buffer(**buffer)
		else:
			self.buffer = _Buffer()
		windows._append(self)
		_window_id += 1
		_window_ids.append(_window_id)
		self.options = {}
		self.vars = {}

	def __repr__(self):
		return '<window ' + str(self.number - 1) + '>'


_buf_lines = {}
_undostate = {}
_undo_written = {}
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
		_buf_lines[bufnr] = ['']
		from copy import copy
		_undostate[bufnr] = [copy(_buf_lines[bufnr])]
		_undo_written[bufnr] = len(_undostate[bufnr])
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
			self._name = os.path.abspath(name)

	def __getitem__(self, line):
		return _buf_lines[self.number][line]

	def __setitem__(self, line, value):
		self.options['modified'] = 1
		self.vars['changedtick'] += 1
		_buf_lines[self.number][line] = value
		from copy import copy
		_undostate[self.number].append(copy(_buf_lines[self.number]))

	def __setslice__(self, *args):
		self.options['modified'] = 1
		self.vars['changedtick'] += 1
		_buf_lines[self.number].__setslice__(*args)
		from copy import copy
		_undostate[self.number].append(copy(_buf_lines[self.number]))

	def __getslice__(self, *args):
		return _buf_lines[self.number].__getslice__(*args)

	def __len__(self):
		return len(_buf_lines[self.number])

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
		if _buf_lines:
			_buf_lines.pop(bufnr)
		if _undostate:
			_undostate.pop(bufnr)
		if _undo_written:
			_undo_written.pop(bufnr)


class _Current(object):
	@property
	def buffer(self):
		return buffers[_buffer()]

	@property
	def window(self):
		return windows[_window - 1]


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
	_new()
	return _dict


@_vim
def _get_segment_info():
	mode_translations = {
		chr(ord('V') - 0x40): '^V',
		chr(ord('S') - 0x40): '^S',
	}
	mode = _mode
	mode = mode_translations.get(mode, mode)
	return {
		'window': windows[_window - 1],
		'winnr': _window,
		'buffer': buffers[_buffer()],
		'bufnr': _buffer(),
		'window_id': _window_ids[_window],
		'mode': mode,
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
	if len(_undostate[_buffer()]) == 1:
		return
	_undostate[_buffer()].pop(-1)
	_buf_lines[_buffer()] = _undostate[_buffer()][-1]
	buf = current.buffer
	if _undo_written[_buffer()] == len(_undostate[_buffer()]):
		buf.options['modified'] = 0


@_vim
def _edit(name=None):
	global _last_bufnr
	if _buffer() and buffers[_buffer()].name is None:
		buf = buffers[_buffer()]
		buf.name = name
	else:
		buf = _Buffer(name)
		windows[_window - 1].buffer = buf


@_vim
def _new(name=None):
	global _window
	_Window(buffer={'name': name})
	_window = len(windows)


@_vim
def _split():
	global _window
	_Window(buffer=buffers[_buffer()])
	_window = len(windows)


@_vim
def _del_window(winnr):
	win = windows._pop(winnr - 1)
	_window_ids.pop(winnr)
	return win


@_vim
def _close(winnr, wipe=True):
	global _window
	win = _del_window(winnr)
	if _window == winnr:
		_window = len(windows)
	if wipe:
		for w in windows:
			if w.buffer.number == win.buffer.number:
				break
		else:
			_bw(win.buffer.number)
	if not windows:
		_Window()


@_vim
def _bw(bufnr=None):
	bufnr = bufnr or _buffer()
	winnr = 1
	for win in windows:
		if win.buffer.number == bufnr:
			_close(winnr, wipe=False)
		winnr += 1
	buffers.pop(bufnr)
	if not buffers:
		_Buffer()
	_b(max(buffers.keys()))


@_vim
def _b(bufnr):
	windows[_window - 1].buffer = buffers[bufnr]


@_vim
def _set_cursor(line, col):
	windows[_window - 1].cursor = (line, col)
	if _mode == 'n':
		_launch_event('CursorMoved')
	elif _mode == 'i':
		_launch_event('CursorMovedI')


@_vim
def _get_buffer():
	return buffers[_buffer()]


@_vim
def _set_bufoption(option, value, bufnr=None):
	buffers[bufnr or _buffer()].options[option] = value
	if option == 'filetype':
		_launch_event('FileType')


class _WithNewBuffer(object):
	def __init__(self, func, *args, **kwargs):
		self.call = lambda: func(*args, **kwargs)

	def __enter__(self):
		self.call()
		self.bufnr = _buffer()
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
		self.buffer = buffers[_buffer()]
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
		buffer = buffers[_buffer()]
		self.buffer = buffer
		self.old = buffer.name
		buffer.name = self.new
		if buffer.name and os.path.basename(buffer.name) == 'ControlP':
			buffer.vars['powerline_ctrlp_type'] = 'main'
			buffer.vars['powerline_ctrlp_args'] = ['focus', 'byfname', '0', 'prev', 'item', 'next', 'marked']

	def __exit__(self, *args):
		self.buffer.name = self.old


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
		return _WithDict(windows[_window - 1].vars, **kwargs)
	elif key == 'environ':
		return _WithDict(_environ, **kwargs)
	elif key == 'split':
		return _WithSplit()


class error(Exception):
	pass
