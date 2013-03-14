# vim:fileencoding=utf-8:noet

from __future__ import absolute_import

import os
try:
	import vim
except ImportError:
	vim = {}  # NOQA

from powerline.bindings.vim import vim_get_func, getbufvar
from powerline.theme import requires_segment_info
from powerline.lib import add_divider_highlight_group
from powerline.lib.vcs import guess
from powerline.lib.humanize_bytes import humanize_bytes
from powerline.lib.threaded import KwThreadedSegment
from functools import wraps
from collections import defaultdict

vim_funcs = {
	'virtcol': vim_get_func('virtcol', rettype=int),
	'fnamemodify': vim_get_func('fnamemodify'),
	'expand': vim_get_func('expand'),
	'bufnr': vim_get_func('bufnr', rettype=int),
	'line2byte': vim_get_func('line2byte', rettype=int),
}

vim_modes = {
	'n': 'NORMAL',
	'no': 'N·OPER',
	'v': 'VISUAL',
	'V': 'V·LINE',
	'^V': 'V·BLCK',
	's': 'SELECT',
	'S': 'S·LINE',
	'^S': 'S·BLCK',
	'i': 'INSERT',
	'R': 'REPLACE',
	'Rv': 'V·RPLCE',
	'c': 'COMMND',
	'cv': 'VIM EX',
	'ce': 'EX',
	'r': 'PROMPT',
	'rm': 'MORE',
	'r?': 'CONFIRM',
	'!': 'SHELL',
}


eventcaches = defaultdict(lambda: [])
bufeventcaches = defaultdict(lambda: [])


def purgeonevents_reg(events, eventcaches=bufeventcaches):
	def cache_reg_func(cache):
		for event in events:
			if event not in eventcaches:
				vim.eval('PowerlineRegisterCachePurgerEvent("' + event + '")')
			eventcaches[event].append(cache)
	return cache_reg_func

purgeall_on_shell = purgeonevents_reg(('ShellCmdPost', 'ShellFilterPost', 'FocusGained'), eventcaches=eventcaches)
purgebuf_on_shell_and_write = purgeonevents_reg(('BufWritePost', 'ShellCmdPost', 'ShellFilterPost', 'FocusGained'))


def launchevent(event):
	global eventcaches
	global bufeventcaches
	for cache in eventcaches[event]:
		cache.clear()
	if bufeventcaches[event]:
		buf = int(vim_funcs['expand']('<abuf>'))
		for cache in bufeventcaches[event]:
			try:
				cache.pop(buf)
			except KeyError:
				pass


def bufnr(segment_info, **kwargs):
	'''Used for cache key, returns current buffer number'''
	return segment_info['bufnr']


def bufname(segment_info, **kwargs):
	'''Used for cache key, returns current buffer name'''
	return segment_info['buffer'].name


# TODO Remove cache when needed
def window_cached(func):
	cache = {}

	@requires_segment_info
	@wraps(func)
	def ret(segment_info, *args, **kwargs):
		window_id = segment_info['window_id']
		if segment_info['mode'] == 'nc':
			return cache.get(window_id)
		else:
			r = func(*args, **kwargs)
			cache[window_id] = r
			return r

	return ret


@requires_segment_info
def mode(segment_info, override=None):
	'''Return the current vim mode.

	:param dict override:
		dict for overriding default mode strings, e.g. ``{ 'n': 'NORM' }``
	'''
	mode = segment_info['mode']
	if mode == 'nc':
		return None
	if not override:
		return vim_modes[mode]
	try:
		return override[mode]
	except KeyError:
		return vim_modes[mode]


@requires_segment_info
def modified_indicator(segment_info, text='+'):
	'''Return a file modified indicator.

	:param string text:
		text to display if the current buffer is modified
	'''
	return text if int(getbufvar(segment_info['bufnr'], '&modified')) else None


@requires_segment_info
def paste_indicator(segment_info, text='PASTE'):
	'''Return a paste mode indicator.

	:param string text:
		text to display if paste mode is enabled
	'''
	return text if int(vim.eval('&paste')) else None


@requires_segment_info
def readonly_indicator(segment_info, text=''):
	'''Return a read-only indicator.

	:param string text:
		text to display if the current buffer is read-only
	'''
	return text if int(getbufvar(segment_info['bufnr'], '&readonly')) else None


@requires_segment_info
def file_directory(segment_info, shorten_user=True, shorten_cwd=True, shorten_home=False):
	'''Return file directory (head component of the file path).

	:param bool shorten_user:
		shorten ``$HOME`` directory to :file:`~/`

	:param bool shorten_cwd:
		shorten current directory to :file:`./`

	:param bool shorten_home:
		shorten all directories in :file:`/home/` to :file:`~user/` instead of :file:`/home/user/`.
	'''
	name = segment_info['buffer'].name
	if not name:
		return None
	file_directory = vim_funcs['fnamemodify'](name, (':~' if shorten_user else '')
												+ (':.' if shorten_home else '') + ':h')
	if shorten_home and file_directory.startswith('/home/'):
		file_directory = '~' + file_directory[6:]
	return file_directory + os.sep if file_directory else None


@requires_segment_info
def file_name(segment_info, display_no_file=False, no_file_text='[No file]'):
	'''Return file name (tail component of the file path).

	:param bool display_no_file:
		display a string if the buffer is missing a file name
	:param str no_file_text:
		the string to display if the buffer is missing a file name
	'''
	name = segment_info['buffer'].name
	if not name:
		if display_no_file:
			return [{
				'contents': no_file_text,
				'highlight_group': ['file_name_no_file', 'file_name'],
				}]
		else:
			return None
	file_name = vim_funcs['fnamemodify'](name, ':~:.:t')
	return file_name


@window_cached
def file_size(suffix='B', si_prefix=False):
	'''Return file size in &encoding.

	:param str suffix:
		string appended to the file size
	:param bool si_prefix:
		use SI prefix, e.g. MB instead of MiB
	:return: file size or None if the file isn't saved or if the size is too big to fit in a number
	'''
	# Note: returns file size in &encoding, not in &fileencoding. But returned 
	# size is updated immediately; and it is valid for any buffer
	file_size = vim_funcs['line2byte'](len(vim.current.buffer) + 1) - 1
	return humanize_bytes(file_size, suffix, si_prefix)


@requires_segment_info
@add_divider_highlight_group('background:divider')
def file_format(segment_info):
	'''Return file format (i.e. line ending type).

	:return: file format or None if unknown or missing file format

	Divider highlight group used: ``background:divider``.
	'''
	return getbufvar(segment_info['bufnr'], '&fileformat') or None


@requires_segment_info
@add_divider_highlight_group('background:divider')
def file_encoding(segment_info):
	'''Return file encoding/character set.

	:return: file encoding/character set or None if unknown or missing file encoding

	Divider highlight group used: ``background:divider``.
	'''
	return getbufvar(segment_info['bufnr'], '&fileencoding') or None


@requires_segment_info
@add_divider_highlight_group('background:divider')
def file_type(segment_info):
	'''Return file type.

	:return: file type or None if unknown file type

	Divider highlight group used: ``background:divider``.
	'''
	return getbufvar(segment_info['bufnr'], '&filetype') or None


@requires_segment_info
def line_percent(segment_info, gradient=False):
	'''Return the cursor position in the file as a percentage.

	:param bool gradient:
		highlight the percentage with a color gradient (by default a green to red gradient)

	Highlight groups used: ``line_percent_gradient`` (gradient) or ``line_percent``.
	'''
	line_current = segment_info['window'].cursor[0]
	line_last = len(segment_info['buffer'])
	percentage = int(line_current * 100 // line_last)
	if not gradient:
		return str(percentage)
	return [{
		'contents': str(percentage),
		'highlight_group': ['line_percent_gradient', 'line_percent'],
		'gradient_level': percentage,
		}]


@requires_segment_info
def line_current(segment_info):
	'''Return the current cursor line.'''
	return str(segment_info['window'].cursor[0])


@requires_segment_info
def col_current(segment_info):
	'''Return the current cursor column.
	'''
	return str(segment_info['window'].cursor[1] + 1)


@window_cached
def virtcol_current():
	'''Return current visual column with concealed characters ingored

	Highlight groups used: ``virtcol_current`` or ``col_current``.
	'''
	return [{'contents': str(vim_funcs['virtcol']('.')),
			'highlight_group': ['virtcol_current', 'col_current']}]


def modified_buffers(text='+ ', join_str=','):
	'''Return a comma-separated list of modified buffers.

	:param str text:
		text to display before the modified buffer list
	:param str join_str:
		string to use for joining the modified buffer list
	'''
	buffer_len = vim_funcs['bufnr']('$')
	buffer_mod = [str(bufnr) for bufnr in range(1, buffer_len + 1) if int(getbufvar(bufnr, '&modified') or 0)]
	if buffer_mod:
		return text + join_str.join(buffer_mod)
	return None


class KwWindowThreadedSegment(KwThreadedSegment):
	def set_state(self, **kwargs):
		for window in vim.windows:
			buffer = window.buffer
			kwargs['segment_info'] = {'bufnr': buffer.number, 'buffer': buffer}
			super(KwWindowThreadedSegment, self).set_state(**kwargs)


class RepositorySegment(KwWindowThreadedSegment):
	def __init__(self):
		super(RepositorySegment, self).__init__()
		self.directories = {}

	@staticmethod
	def key(segment_info, **kwargs):
		# FIXME os.getcwd() is not a proper variant for non-current buffers
		return segment_info['buffer'].name or os.getcwd()

	def update(self):
		# .compute_state() is running only in this method, and only in one 
		# thread, thus operations with .directories do not need write locks 
		# (.render() method is not using .directories). If this is changed 
		# .directories needs redesigning
		self.directories.clear()
		super(RepositorySegment, self).update()

	def compute_state(self, path):
		repo = guess(path=path)
		if repo:
			if repo.directory in self.directories:
				return self.directories[repo.directory]
			else:
				r = self.process_repo(repo)
				self.directories[repo.directory] = r
				return r


@requires_segment_info
class RepositoryStatusSegment(RepositorySegment):
	'''Return the status for the current repo.'''

	interval = 2

	@staticmethod
	def process_repo(repo):
		return repo.status()


repository_status = RepositoryStatusSegment()


@requires_segment_info
class BranchSegment(RepositorySegment):
	'''Return the current working branch.

	:param bool status_colors:
		determines whether repository status will be used to determine highlighting. Default: False.

	Highlight groups used: ``branch_clean``, ``branch_dirty``, ``branch``.

	Divider highlight group used: ``branch:divider``.
	'''

	interval = 0.2
	started_repository_status = False

	@staticmethod
	def process_repo(repo):
		return repo.branch()

	def render_one(self, update_state, segment_info, status_colors=False, **kwargs):
		if not update_state:
			return None

		if status_colors:
			self.started_repository_status = True

		return [{
			'contents': update_state,
			'highlight_group': (['branch_dirty' if repository_status(segment_info=segment_info) else 'branch_clean']
								if status_colors else []) + ['branch'],
			'divider_highlight_group': 'branch:divider',
			}]

	def startup(self, **kwargs):
		super(BranchSegment, self).startup()
		if kwargs.get('status_colors', False):
			self.started_repository_status = True
			repository_status.startup()

	def shutdown(self):
		if self.started_repository_status:
			repository_status.shutdown()
		super(BranchSegment, self).shutdown()


branch = BranchSegment()


@requires_segment_info
class FileVCSStatusSegment(KwWindowThreadedSegment):
	'''Return the VCS status for this buffer.

	Highlight groups used: ``file_vcs_status``.
	'''

	interval = 0.2

	@staticmethod
	def key(segment_info, **kwargs):
		name = segment_info['buffer'].name
		skip = not (name and (not getbufvar(segment_info['bufnr'], '&buftype')))
		return name, skip

	@staticmethod
	def compute_state(key):
		name, skip = key
		if not skip:
			repo = guess(path=name)
			if repo:
				status = repo.status(os.path.relpath(name, repo.directory))
				if not status:
					return None
				status = status.strip()
				ret = []
				for status in status:
					ret.append({
						'contents': status,
						'highlight_group': ['file_vcs_status_' + status, 'file_vcs_status'],
						})
				return ret
		return None


file_vcs_status = FileVCSStatusSegment()
