_log = []
_g = {}
_window = 0
_mode = 'n'
_buf_purge_events = set()
_options = {
		'paste': 0,
		}
_last_bufnr = 0
_highlights = {}

buffers = {}

windows = []


def _buffer():
	return windows[_window - 1].buffer.number


def _logged(func):
	from functools import wraps

	@wraps(func)
	def f(*args):
		_log.append((func.__name__, args))
		return func(*args)

	return f


@_logged
def command(cmd):
	if cmd.startswith('let g:'):
		import re
		varname, value = re.compile(r'^let g:(\w+)\s*=\s*(.*)').match(cmd).groups()
		_g[varname] = value
	elif cmd.startswith('hi '):
		sp = cmd.split()
		_highlights[sp[1]] = sp[2:]
	else:
		raise NotImplementedError


@_logged
def eval(expr):
	if expr.startswith('g:'):
		return _g[expr[2:]]
	elif expr.startswith('&'):
		return _options[expr[1:]]
	elif expr.startswith('PowerlineRegisterCachePurgerEvent'):
		_buf_purge_events.add(expr[expr.find('"') + 1:expr.rfind('"') - 1])
		return "0"
	raise NotImplementedError


@_logged
def bindeval(expr):
	if expr == 'g:':
		return _g
	import re
	match = re.compile(r'^function\("([^"\\]+)"\)$').match(expr)
	if match:
		return globals()['_emul_' + match.group(1)]
	else:
		raise NotImplementedError


@_logged
def _emul_mode(*args):
	if args and args[0]:
		return _mode
	else:
		return _mode[0]


@_logged
def _emul_getbufvar(bufnr, varname):
	if varname[0] == '&':
		if bufnr not in _buf_options:
			return ''
		try:
			return _buf_options[bufnr][varname[1:]]
		except KeyError:
			try:
				return _options[varname[1:]]
			except KeyError:
				return ''
	raise NotImplementedError


@_logged
def _emul_getwinvar(winnr, varname):
	return _win_scopes[winnr][varname]


@_logged
def _emul_setwinvar(winnr, varname, value):
	_win_scopes[winnr][varname] = value


@_logged
def _emul_virtcol(expr):
	if expr == '.':
		return windows[_window - 1].cursor[1] + 1
	raise NotImplementedError


@_logged
def _emul_fnamemodify(path, modstring):
	import os
	_modifiers = {
		'~': lambda path: path.replace(os.environ['HOME'], '~') if path.startswith(os.environ['HOME']) else path,
		'.': lambda path: (lambda tpath: path if tpath[:3] == '..' + os.sep else tpath)(os.path.relpath(path)),
		't': lambda path: os.path.basename(path),
		'h': lambda path: os.path.dirname(path),
	}

	for mods in modstring.split(':')[1:]:
		path = _modifiers[mods](path)
	return path


@_logged
def _emul_expand(expr):
	if expr == '<abuf>':
		return _buffer()
	raise NotImplementedError


@_logged
def _emul_bufnr(expr):
	if expr == '$':
		return _last_bufnr
	raise NotImplementedError


@_logged
def _emul_exists(varname):
	if varname.startswith('g:'):
		return varname[2:] in _g
	raise NotImplementedError


_window_ids = [None]
_window_id = 0
_win_scopes = [None]
_win_options = [None]


class _Window(object):
	def __init__(self, buffer=None, cursor=(1, 0), width=80):
		global _window_id
		self.cursor = cursor
		self.width = width
		if buffer:
			if type(buffer) is _Buffer:
				self.buffer = buffer
			else:
				self.buffer = _Buffer(**buffer)
		else:
			self.buffer = _Buffer()
		windows.append(self)
		_window_id += 1
		_window_ids.append(_window_id)
		_win_scopes.append({})
		_win_options.append({})

	def __repr__(self):
		return '<window ' + str(windows.index(self)) + '>'


_buf_scopes = {}
_buf_options = {}
_buf_lines = {}
_undostate = {}
_undo_written = {}


class _Buffer(object):
	def __init__(self, name=None):
		global _last_bufnr
		import os
		_last_bufnr += 1
		bufnr = _last_bufnr
		self.number = bufnr
		self.name = os.path.abspath(name) if name else None
		_buf_scopes[bufnr] = {}
		_buf_options[bufnr] = {
				'modified': 0,
				'readonly': 0,
				'fileformat': 'unix',
				'filetype': '',
				'buftype': '',
				'fileencoding': 'utf-8',
				}
		_buf_lines[bufnr] = ['']
		from copy import copy
		_undostate[bufnr] = [copy(_buf_lines[bufnr])]
		_undo_written[bufnr] = len(_undostate[bufnr])
		buffers[bufnr] = self

	def __getitem__(self, line):
		return _buf_lines[self.number][line]

	def __setitem__(self, line, value):
		_buf_options[self.number]['modified'] = 1
		_buf_lines[self.number][line] = value
		from copy import copy
		_undostate[self.number].append(copy(_buf_lines[self.number]))

	def __setslice__(self, *args):
		_buf_options[self.number]['modified'] = 1
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
		bufnr = self.number
		if _buf_options:
			_buf_options.pop(bufnr)
			_buf_lines.pop(bufnr)
			_undostate.pop(bufnr)
			_undo_written.pop(bufnr)
			_buf_scopes.pop(bufnr)


_dict = None


def _init():
	global _dict

	if _dict:
		return _dict

	import imp
	_dict = {}
	for varname, value in globals().items():
		if varname[0] != '_':
			_dict[varname] = value
	_new()
	return _dict


def _get_segment_info():
	mode_translations = {
			chr(ord('V') - 0x40): '^V',
			chr(ord('S') - 0x40): '^S',
			}
	mode = _mode
	mode = mode_translations.get(mode, mode)
	return {
		'window': windows[_window - 1],
		'buffer': buffers[_buffer()],
		'bufnr': _buffer(),
		'window_id': _window_ids[_window],
		'mode': mode,
	}


def _launch_event(event):
	pass


def _start_mode(mode):
	global _mode
	if mode == 'i':
		_launch_event('InsertEnter')
	elif _mode == 'i':
		_launch_event('InsertLeave')
	_mode = mode


def _undo():
	if len(_undostate[_buffer()]) == 1:
		return
	_undostate[_buffer()].pop(-1)
	_buf_lines[_buffer()] = _undostate[_buffer()][-1]
	if _undo_written[_buffer()] == len(_undostate[_buffer()]):
		_buf_options[_buffer()]['modified'] = 0


def _edit(name=None):
	global _last_bufnr
	if _buffer() and buffers[_buffer()].name is None:
		buf = buffers[_buffer()]
		buf.name = name
	else:
		buf = _Buffer(name)
		windows[_window - 1].buffer = buf


def _new(name=None):
	global _window
	_Window(buffer={'name': name})
	_window = len(windows)


def _del_window(winnr):
	win = windows.pop(winnr - 1)
	_win_scopes.pop(winnr)
	_win_options.pop(winnr)
	_window_ids.pop(winnr)
	return win


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


def _b(bufnr):
	windows[_window - 1].buffer = buffers[bufnr]


def _set_filetype(ft):
	_buf_options[_buffer()]['filetype'] = ft
	_launch_event('FileType')


def _set_cursor(line, col):
	windows[_window - 1].cursor = (line, col)
	if _mode == 'n':
		_launch_event('CursorMoved')
	elif _mode == 'i':
		_launch_event('CursorMovedI')


def _get_buffer():
	return buffers[_buffer()]


def _set_bufoption(option, value, bufnr=None):
	_buf_options[bufnr or _buffer()][option] = value
