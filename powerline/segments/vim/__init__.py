# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os
import re
import csv
import sys

from collections import defaultdict

try:
	import vim
except ImportError:
	vim = object()

from powerline.bindings.vim import (vim_get_func, getbufvar, vim_getbufoption,
                                    buffer_name, vim_getwinvar,
                                    register_buffer_cache, current_tabpage,
                                    list_tabpage_buffers_segment_info)
from powerline.theme import requires_segment_info, requires_filesystem_watcher
from powerline.lib import add_divider_highlight_group
from powerline.lib.vcs import guess
from powerline.lib.humanize_bytes import humanize_bytes
from powerline.lib import wraps_saveargs as wraps
from powerline.segments.common.vcs import BranchSegment, StashSegment
from powerline.segments import with_docstring
from powerline.lib.unicode import string, unicode

try:
	from __builtin__ import xrange as range
except ImportError:
	pass


vim_funcs = {
	'virtcol': vim_get_func('virtcol', rettype='int'),
	'getpos': vim_get_func('getpos'),
	'fnamemodify': vim_get_func('fnamemodify', rettype='bytes'),
	'line2byte': vim_get_func('line2byte', rettype='int'),
	'line': vim_get_func('line', rettype='int'),
}

vim_modes = {
	'n': 'NORMAL',
	'no': 'N-OPER',
	'v': 'VISUAL',
	'V': 'V-LINE',
	'^V': 'V-BLCK',
	's': 'SELECT',
	'S': 'S-LINE',
	'^S': 'S-BLCK',
	'i': 'INSERT',
	'ic': 'I-COMP',
	'ix': 'I-C_X ',
	'R': 'RPLACE',
	'Rv': 'V-RPLC',
	'Rc': 'R-COMP',
	'Rx': 'R-C_X ',
	'c': 'COMMND',
	'cv': 'VIM-EX',
	'ce': 'NRM-EX',
	'r': 'PROMPT',
	'rm': '-MORE-',
	'r?': 'CNFIRM',
	'!': '!SHELL',
	't': 'TERM  ',
}


# TODO Remove cache when needed
def window_cached(func):
	cache = {}

	@requires_segment_info
	@wraps(func)
	def ret(segment_info, **kwargs):
		window_id = segment_info['window_id']
		if segment_info['mode'] == 'nc':
			return cache.get(window_id)
		else:
			if getattr(func, 'powerline_requires_segment_info', False):
				r = func(segment_info=segment_info, **kwargs)
			else:
				r = func(**kwargs)
			cache[window_id] = r
			return r

	return ret


@requires_segment_info
def mode(pl, segment_info, override=None):
	'''Return the current vim mode.

	If mode (returned by ``mode()`` VimL function, see ``:h mode()`` in Vim) 
	consists of multiple characters and necessary mode is not known to powerline 
	then it will fall back to mode with last character(s) ignored.

	:param dict override:
		dict for overriding default mode strings, e.g. ``{ 'n': 'NORM' }``
	'''
	mode = segment_info['mode']
	if mode == 'nc':
		return None
	while mode:
		try:
			if not override:
				return vim_modes[mode]
			try:
				return override[mode]
			except KeyError:
				return vim_modes[mode]
		except KeyError:
			mode = mode[:-1]
	return 'BUG'


@window_cached
@requires_segment_info
def visual_range(pl, segment_info, CTRL_V_text='{rows} x {vcols}', v_text_oneline='C:{vcols}', v_text_multiline='L:{rows}', V_text='L:{rows}'):
	'''Return the current visual selection range.

	:param str CTRL_V_text:
		Text to display when in block visual or select mode.
	:param str v_text_oneline:
		Text to display when in charaterwise visual or select mode, assuming 
		selection occupies only one line.
	:param str v_text_multiline:
		Text to display when in charaterwise visual or select mode, assuming 
		selection occupies more then one line.
	:param str V_text:
		Text to display when in linewise visual or select mode.

	All texts are format strings which are passed the following parameters:

	=========  =============================================================
	Parameter  Description
	=========  =============================================================
	sline      Line number of the first line of the selection
	eline      Line number of the last line of the selection
	scol       Column number of the first character of the selection
	ecol       Column number of the last character of the selection
	svcol      Virtual column number of the first character of the selection
	secol      Virtual column number of the last character of the selection
	rows       Number of lines in the selection
	cols       Number of columns in the selection
	vcols      Number of virtual columns in the selection
	=========  =============================================================
	'''
	sline, scol, soff = [int(v) for v in vim_funcs['getpos']('v')[1:]]
	eline, ecol, eoff = [int(v) for v in vim_funcs['getpos']('.')[1:]]
	svcol = vim_funcs['virtcol']([sline, scol, soff])
	evcol = vim_funcs['virtcol']([eline, ecol, eoff])
	rows = abs(eline - sline) + 1
	cols = abs(ecol - scol) + 1
	vcols = abs(evcol - svcol) + 1
	return {
		'^': CTRL_V_text,
		's': v_text_oneline if rows == 1 else v_text_multiline,
		'S': V_text,
		'v': v_text_oneline if rows == 1 else v_text_multiline,
		'V': V_text,
	}.get(segment_info['mode'][0], '').format(
		sline=sline, eline=eline,
		scol=scol, ecol=ecol,
		svcol=svcol, evcol=evcol,
		rows=rows, cols=cols, vcols=vcols,
	)


@requires_segment_info
def modified_indicator(pl, segment_info, text='+'):
	'''Return a file modified indicator.

	:param string text:
		text to display if the current buffer is modified
	'''
	return text if int(vim_getbufoption(segment_info, 'modified')) else None


@requires_segment_info
def tab_modified_indicator(pl, segment_info, text='+'):
	'''Return a file modified indicator for tabpages.

	:param string text:
		text to display if any buffer in the current tab is modified

	Highlight groups used: ``tab_modified_indicator`` or ``modified_indicator``.
	'''
	for buf_segment_info in list_tabpage_buffers_segment_info(segment_info):
		if int(vim_getbufoption(buf_segment_info, 'modified')):
			return [{
				'contents': text,
				'highlight_groups': ['tab_modified_indicator', 'modified_indicator'],
			}]
	return None


@requires_segment_info
def paste_indicator(pl, segment_info, text='PASTE'):
	'''Return a paste mode indicator.

	:param string text:
		text to display if paste mode is enabled
	'''
	return text if int(vim.eval('&paste')) else None


@requires_segment_info
def readonly_indicator(pl, segment_info, text='RO'):
	'''Return a read-only indicator.

	:param string text:
		text to display if the current buffer is read-only
	'''
	return text if int(vim_getbufoption(segment_info, 'readonly')) else None


SCHEME_RE = re.compile(b'^\\w[\\w\\d+\\-.]*(?=:)')


@requires_segment_info
def file_scheme(pl, segment_info):
	'''Return the protocol part of the file.

	Protocol is the part of the full filename just before the colon which 
	starts with a latin letter and contains only latin letters, digits, plus, 
	period or hyphen (refer to `RFC3986 
	<http://tools.ietf.org/html/rfc3986#section-3.1>`_ for the description of 
	URI scheme). If there is no such a thing ``None`` is returned, effectively 
	removing segment.

	.. note::
		Segment will not check  whether there is ``//`` just after the 
		colon or if there is at least one slash after the scheme. Reason: it is 
		not always present. E.g. when opening file inside a zip archive file 
		name will look like :file:`zipfile:/path/to/archive.zip::file.txt`. 
		``file_scheme`` segment will catch ``zipfile`` part here.
	'''
	name = buffer_name(segment_info)
	if not name:
		return None
	match = SCHEME_RE.match(name)
	if match:
		return match.group(0).decode('ascii')


@requires_segment_info
def file_directory(pl, segment_info, remove_scheme=True, shorten_user=True, shorten_cwd=True, shorten_home=False):
	'''Return file directory (head component of the file path).

	:param bool remove_scheme:
		Remove scheme part from the segment name, if present. See documentation 
		of file_scheme segment for the description of what scheme is. Also 
		removes the colon.

	:param bool shorten_user:
		Shorten ``$HOME`` directory to :file:`~/`. Does not work for files with 
		scheme.

	:param bool shorten_cwd:
		Shorten current directory to :file:`./`. Does not work for files with 
		scheme present.

	:param bool shorten_home:
		Shorten all directories in :file:`/home/` to :file:`~user/` instead of 
		:file:`/home/user/`. Does not work for files with scheme present.
	'''
	name = buffer_name(segment_info)
	if not name:
		return None
	match = SCHEME_RE.match(name)
	if match:
		if remove_scheme:
			name = name[len(match.group(0)) + 1:]  # Remove scheme and colon
		file_directory = vim_funcs['fnamemodify'](name, ':h')
	else:
		file_directory = vim_funcs['fnamemodify'](
			name,
			(':~' if shorten_user else '') + (':.' if shorten_cwd else '') + ':h'
		)
		if not file_directory:
			return None
		if shorten_home and file_directory.startswith('/home/'):
			file_directory = b'~' + file_directory[6:]
	file_directory = file_directory.decode(segment_info['encoding'], 'powerline_vim_strtrans_error')
	return file_directory + os.sep


@requires_segment_info
def file_name(pl, segment_info, display_no_file=False, no_file_text='[No file]'):
	'''Return file name (tail component of the file path).

	:param bool display_no_file:
		display a string if the buffer is missing a file name
	:param str no_file_text:
		the string to display if the buffer is missing a file name

	Highlight groups used: ``file_name_no_file`` or ``file_name``, ``file_name``.
	'''
	name = buffer_name(segment_info)
	if not name:
		if display_no_file:
			return [{
				'contents': no_file_text,
				'highlight_groups': ['file_name_no_file', 'file_name'],
			}]
		else:
			return None
	return os.path.basename(name).decode(segment_info['encoding'], 'powerline_vim_strtrans_error')


@window_cached
def file_size(pl, suffix='B', si_prefix=False):
	'''Return file size in &encoding.

	:param str suffix:
		string appended to the file size
	:param bool si_prefix:
		use SI prefix, e.g. MB instead of MiB
	:return: file size or None if the file isn’t saved or if the size is too big to fit in a number
	'''
	# Note: returns file size in &encoding, not in &fileencoding. But returned 
	# size is updated immediately; and it is valid for any buffer
	file_size = vim_funcs['line2byte'](len(vim.current.buffer) + 1) - 1
	if file_size < 0:
		file_size = 0
	return humanize_bytes(file_size, suffix, si_prefix)


@requires_segment_info
@add_divider_highlight_group('background:divider')
def file_format(pl, segment_info):
	'''Return file format (i.e. line ending type).

	:return: file format or None if unknown or missing file format

	Divider highlight group used: ``background:divider``.
	'''
	return vim_getbufoption(segment_info, 'fileformat') or None


@requires_segment_info
@add_divider_highlight_group('background:divider')
def file_encoding(pl, segment_info):
	'''Return file encoding/character set.

	:return: file encoding/character set or None if unknown or missing file encoding

	Divider highlight group used: ``background:divider``.
	'''
	return vim_getbufoption(segment_info, 'fileencoding') or None


@requires_segment_info
@add_divider_highlight_group('background:divider')
def file_type(pl, segment_info):
	'''Return file type.

	:return: file type or None if unknown file type

	Divider highlight group used: ``background:divider``.
	'''
	return vim_getbufoption(segment_info, 'filetype') or None


@requires_segment_info
def window_title(pl, segment_info):
	'''Return the window title.

	This currently looks at the ``quickfix_title`` window variable,
	which is used by Syntastic and Vim itself.

	It is used in the quickfix theme.'''
	try:
		return vim_getwinvar(segment_info, 'quickfix_title')
	except KeyError:
		return None


@requires_segment_info
def line_percent(pl, segment_info, gradient=False):
	'''Return the cursor position in the file as a percentage.

	:param bool gradient:
		highlight the percentage with a color gradient (by default a green to red gradient)

	Highlight groups used: ``line_percent_gradient`` (gradient), ``line_percent``.
	'''
	line_current = segment_info['window'].cursor[0]
	line_last = len(segment_info['buffer'])
	percentage = line_current * 100.0 / line_last
	if not gradient:
		return str(int(round(percentage)))
	return [{
		'contents': str(int(round(percentage))),
		'highlight_groups': ['line_percent_gradient', 'line_percent'],
		'gradient_level': percentage,
	}]


@window_cached
def position(pl, position_strings={'top': 'Top', 'bottom': 'Bot', 'all': 'All'}, gradient=False):
	'''Return the position of the current view in the file as a percentage.

	:param dict position_strings:
		dict for translation of the position strings, e.g. ``{"top":"Oben", "bottom":"Unten", "all":"Alles"}``

	:param bool gradient:
		highlight the percentage with a color gradient (by default a green to red gradient)

	Highlight groups used: ``position_gradient`` (gradient), ``position``.
	'''
	line_last = len(vim.current.buffer)

	winline_first = vim_funcs['line']('w0')
	winline_last = vim_funcs['line']('w$')
	if winline_first == 1 and winline_last == line_last:
		percentage = 0.0
		content = position_strings['all']
	elif winline_first == 1:
		percentage = 0.0
		content = position_strings['top']
	elif winline_last == line_last:
		percentage = 100.0
		content = position_strings['bottom']
	else:
		percentage = winline_first * 100.0 / (line_last - winline_last + winline_first)
		content = str(int(round(percentage))) + '%'

	if not gradient:
		return content
	return [{
		'contents': content,
		'highlight_groups': ['position_gradient', 'position'],
		'gradient_level': percentage,
	}]


@requires_segment_info
def line_current(pl, segment_info):
	'''Return the current cursor line.'''
	return str(segment_info['window'].cursor[0])


@requires_segment_info
def line_count(pl, segment_info):
	'''Return the line count of the current buffer.'''
	return str(len(segment_info['buffer']))


@requires_segment_info
def col_current(pl, segment_info):
	'''Return the current cursor column.
	'''
	return str(segment_info['window'].cursor[1] + 1)


@window_cached
def virtcol_current(pl, gradient=True):
	'''Return current visual column with concealed characters ingored

	:param bool gradient:
		Determines whether it should show textwidth-based gradient (gradient level is ``virtcol * 100 / textwidth``).

	Highlight groups used: ``virtcol_current_gradient`` (gradient), ``virtcol_current`` or ``col_current``.
	'''
	col = vim_funcs['virtcol']('.')
	r = [{'contents': str(col), 'highlight_groups': ['virtcol_current', 'col_current']}]
	if gradient:
		textwidth = int(getbufvar('%', '&textwidth'))
		r[-1]['gradient_level'] = min(col * 100 / textwidth, 100) if textwidth else 0
		r[-1]['highlight_groups'].insert(0, 'virtcol_current_gradient')
	return r


def modified_buffers(pl, text='+ ', join_str=','):
	'''Return a comma-separated list of modified buffers.

	:param str text:
		text to display before the modified buffer list
	:param str join_str:
		string to use for joining the modified buffer list
	'''
	buffer_mod_text = join_str.join((
		str(buffer.number)
		for buffer in vim.buffers
		if int(vim_getbufoption({'buffer': buffer, 'bufnr': buffer.number}, 'modified'))
	))
	if buffer_mod_text:
		return text + buffer_mod_text
	return None


@requires_filesystem_watcher
@requires_segment_info
class VimBranchSegment(BranchSegment):
	divider_highlight_group = 'branch:divider'

	@staticmethod
	def get_directory(segment_info):
		if vim_getbufoption(segment_info, 'buftype'):
			return None
		return buffer_name(segment_info)


branch = with_docstring(VimBranchSegment(),
'''Return the current working branch.

:param bool status_colors:
	Determines whether repository status will be used to determine highlighting. 
	Default: False.
:param bool ignore_statuses:
	List of statuses which will not result in repo being marked as dirty. Most 
	useful is setting this option to ``["U"]``: this will ignore repository 
	which has just untracked files (i.e. repository with modified, deleted or 
	removed files will be marked as dirty, while just untracked files will make 
	segment show clean repository). Only applicable if ``status_colors`` option 
	is True.

Highlight groups used: ``branch_clean``, ``branch_dirty``, ``branch``.

Divider highlight group used: ``branch:divider``.
''')


@requires_filesystem_watcher
@requires_segment_info
class VimStashSegment(StashSegment):
	divider_highlight_group = 'stash:divider'

	@staticmethod
	def get_directory(segment_info):
		if vim_getbufoption(segment_info, 'buftype'):
			return None
		return buffer_name(segment_info)


stash = with_docstring(VimStashSegment(),
'''Return the number of stashes in the current working branch.

Highlight groups used: ``stash``.
''')


@requires_filesystem_watcher
@requires_segment_info
def file_vcs_status(pl, segment_info, create_watcher):
	'''Return the VCS status for this buffer.

	Highlight groups used: ``file_vcs_status``.
	'''
	name = buffer_name(segment_info)
	skip = not (name and (not vim_getbufoption(segment_info, 'buftype')))
	if not skip:
		repo = guess(path=name, create_watcher=create_watcher)
		if repo is not None:
			status = repo.status(os.path.relpath(name, repo.directory))
			if not status:
				return None
			status = status.strip()
			ret = []
			for status in status:
				ret.append({
					'contents': status,
					'highlight_groups': ['file_vcs_status_' + status, 'file_vcs_status'],
				})
			return ret


trailing_whitespace_cache = None


@requires_segment_info
def trailing_whitespace(pl, segment_info):
	'''Return the line number for trailing whitespaces

	It is advised not to use this segment in insert mode: in Insert mode it will 
	iterate over all lines in buffer each time you happen to type a character 
	which may cause lags. It will also show you whitespace warning each time you 
	happen to type space.

	Highlight groups used: ``trailing_whitespace`` or ``warning``.
	'''
	global trailing_whitespace_cache
	if trailing_whitespace_cache is None:
		trailing_whitespace_cache = register_buffer_cache(defaultdict(lambda: (0, None)))
	bufnr = segment_info['bufnr']
	changedtick = getbufvar(bufnr, 'changedtick')
	if trailing_whitespace_cache[bufnr][0] == changedtick:
		return trailing_whitespace_cache[bufnr][1]
	else:
		buf = segment_info['buffer']
		bws = b' \t'
		sws = str(' \t')  # Ignore unicode_literals and use native str.
		for i in range(len(buf)):
			try:
				line = buf[i]
			except UnicodeDecodeError:  # May happen in Python 3
				if hasattr(vim, 'bindeval'):
					line = vim.bindeval('getbufline({0}, {1})'.format(
						bufnr, i + 1))
					has_trailing_ws = (line[-1] in bws)
				else:
					line = vim.eval('strtrans(getbufline({0}, {1}))'.format(
						bufnr, i + 1))
					has_trailing_ws = (line[-1] in bws)
			else:
				has_trailing_ws = (line and line[-1] in sws)
			if has_trailing_ws:
				break
		if has_trailing_ws:
			ret = [{
				'contents': str(i + 1),
				'highlight_groups': ['trailing_whitespace', 'warning'],
			}]
		else:
			ret = None
		trailing_whitespace_cache[bufnr] = (changedtick, ret)
		return ret


@requires_segment_info
def tabnr(pl, segment_info, show_current=True):
	'''Show tabpage number

	:param bool show_current:
		If False do not show current tabpage number. This is default because 
		tabnr is by default only present in tabline.
	'''
	try:
		tabnr = segment_info['tabnr']
	except KeyError:
		return None
	if show_current or tabnr != current_tabpage().number:
		return str(tabnr)


@requires_segment_info
def bufnr(pl, segment_info, show_current=True):
	'''Show buffer number

	:param bool show_current:
		If False do not show current window number.
	'''
	bufnr = segment_info['bufnr']
	if show_current or bufnr != vim.current.buffer.number:
		return str(bufnr)


@requires_segment_info
def winnr(pl, segment_info, show_current=True):
	'''Show window number

	:param bool show_current:
		If False do not show current window number.
	'''
	winnr = segment_info['winnr']
	if show_current or winnr != vim.current.window.number:
		return str(winnr)


csv_cache = None
sniffer = csv.Sniffer()


def detect_text_csv_dialect(text, display_name, header_text=None):
	return (
		sniffer.sniff(string(text)),
		sniffer.has_header(string(header_text or text)) if display_name == 'auto' else display_name,
	)


CSV_SNIFF_LINES = 100
CSV_PARSE_LINES = 10


if sys.version_info < (2, 7):
	def read_csv(l, dialect, fin=next):
		try:
			return fin(csv.reader(l, dialect))
		except csv.Error as e:
			if str(e) == 'newline inside string' and dialect.quotechar:
				# Maybe we are inside an unfinished quoted string. Python-2.6 
				# does not handle this fine
				return fin(csv.reader(l[:-1] + [l[-1] + dialect.quotechar]))
			else:
				raise
else:
	def read_csv(l, dialect, fin=next):
		return fin(csv.reader(l, dialect))


def process_csv_buffer(pl, buffer, line, col, display_name):
	global csv_cache
	if csv_cache is None:
		csv_cache = register_buffer_cache(defaultdict(lambda: (None, None, None)))
	try:
		cur_first_line = buffer[0]
	except UnicodeDecodeError:
		cur_first_line = vim.eval('strtrans(getline(1))')
	dialect, has_header, first_line = csv_cache[buffer.number]
	if dialect is None or (cur_first_line != first_line and display_name == 'auto'):
		try:
			text = '\n'.join(buffer[:CSV_SNIFF_LINES])
		except UnicodeDecodeError:  # May happen in Python 3
			text = vim.eval('join(map(getline(1, {0}), "strtrans(v:val)"), "\\n")'.format(CSV_SNIFF_LINES))
		try:
			dialect, has_header = detect_text_csv_dialect(text, display_name)
		except csv.Error as e:
			pl.warn('Failed to detect csv format: {0}', str(e))
			# Try detecting using three lines only:
			if line == 1:
				rng = (0, line + 2)
			elif line == len(buffer):
				rng = (line - 3, line)
			else:
				rng = (line - 2, line + 1)
			try:
				dialect, has_header = detect_text_csv_dialect(
					'\n'.join(buffer[rng[0]:rng[1]]),
					display_name,
					header_text='\n'.join(buffer[:4]),
				)
			except csv.Error as e:
				pl.error('Failed to detect csv format: {0}', str(e))
				return None, None
	if len(buffer) > 2:
		csv_cache[buffer.number] = dialect, has_header, cur_first_line
	column_number = len(read_csv(
		buffer[max(0, line - CSV_PARSE_LINES):line - 1] + [buffer[line - 1][:col]],
		dialect=dialect,
		fin=list,
	)[-1]) or 1
	if has_header:
		try:
			header = read_csv(buffer[0:1], dialect=dialect)
		except UnicodeDecodeError:
			header = read_csv([vim.eval('strtrans(getline(1))')], dialect=dialect)
		column_name = header[column_number - 1]
	else:
		column_name = None
	return unicode(column_number), column_name


@requires_segment_info
def csv_col_current(pl, segment_info, display_name='auto', name_format=' ({column_name:.15})'):
	'''Display CSV column number and column name

	Requires filetype to be set to ``csv``.

	:param bool or str name:
		May be ``True``, ``False`` and ``"auto"``. In the first case value from 
		the first raw will always be displayed. In the second case it will never 
		be displayed. In thi last case ``csv.Sniffer().has_header()`` will be 
		used to detect whether current file contains header in the first column.
	:param str name_format:
		String used to format column name (in case ``display_name`` is set to 
		``True`` or ``"auto"``). Accepts ``column_name`` keyword argument.

	Highlight groups used: ``csv:column_number`` or ``csv``, ``csv:column_name`` or ``csv``.
	'''
	if vim_getbufoption(segment_info, 'filetype') != 'csv':
		return None
	line, col = segment_info['window'].cursor
	column_number, column_name = process_csv_buffer(pl, segment_info['buffer'], line, col, display_name)
	if not column_number:
		return None
	return [{
		'contents': column_number,
		'highlight_groups': ['csv:column_number', 'csv'],
	}] + ([{
		'contents': name_format.format(column_name=column_name),
		'highlight_groups': ['csv:column_name', 'csv'],
	}] if column_name else [])


@requires_segment_info
def tab(pl, segment_info, end=False):
	'''Mark start of the clickable region for tabpage

	:param bool end:
		In place of starting region for the current tab end it.

	No highlight groups are used (literal segment).
	'''
	try:
		return [{
			'contents': None,
			'literal_contents': (0, '%{tabnr}T'.format(tabnr=('' if end else segment_info['tabnr']))),
		}]
	except KeyError:
		return None
