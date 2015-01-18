# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os

from powerline.lib.unicode import out_u
from powerline.theme import requires_segment_info
from powerline.segments import Segment, with_docstring


@requires_segment_info
def environment(pl, segment_info, variable=None):
	'''Return the value of any defined environment variable

	:param string variable:
		The environment variable to return if found
	'''
	return segment_info['environ'].get(variable, None)


@requires_segment_info
def virtualenv(pl, segment_info):
	'''Return the name of the current Python virtualenv.'''
	return os.path.basename(segment_info['environ'].get('VIRTUAL_ENV', '')) or None


@requires_segment_info
class CwdSegment(Segment):
	def argspecobjs(self):
		for obj in super(CwdSegment, self).argspecobjs():
			yield obj
		yield 'get_shortened_path', self.get_shortened_path

	def omitted_args(self, name, method):
		if method is self.get_shortened_path:
			return (0, 1, 2)
		else:
			return super(CwdSegment, self).omitted_args(name, method)

	def get_shortened_path(self, pl, segment_info, shorten_home=True, **kwargs):
		try:
			path = out_u(segment_info['getcwd']())
		except OSError as e:
			if e.errno == 2:
				# user most probably deleted the directory
				# this happens when removing files from Mercurial repos for example
				pl.warn('Current directory not found')
				return '[not found]'
			else:
				raise
		if shorten_home:
			home = segment_info['home']
			if home:
				home = out_u(home)
				if path.startswith(home):
					path = '~' + path[len(home):]
		return path

	def __call__(self, pl, segment_info,
	             dir_shorten_len=None,
	             dir_limit_depth=None,
	             use_path_separator=False,
	             ellipsis='...',
	             **kwargs):
		cwd = self.get_shortened_path(pl, segment_info, **kwargs)
		cwd_split = cwd.split(os.sep)
		cwd_split_len = len(cwd_split)
		cwd = [i[0:dir_shorten_len] if dir_shorten_len and i else i for i in cwd_split[:-1]] + [cwd_split[-1]]
		if dir_limit_depth and cwd_split_len > dir_limit_depth + 1:
			del(cwd[0:-dir_limit_depth])
			if ellipsis is not None:
				cwd.insert(0, ellipsis)
		ret = []
		if not cwd[0]:
			cwd[0] = '/'
		draw_inner_divider = not use_path_separator
		for part in cwd:
			if not part:
				continue
			if use_path_separator:
				part += os.sep
			ret.append({
				'contents': part,
				'divider_highlight_group': 'cwd:divider',
				'draw_inner_divider': draw_inner_divider,
			})
		ret[-1]['highlight_groups'] = ['cwd:current_folder', 'cwd']
		if use_path_separator:
			ret[-1]['contents'] = ret[-1]['contents'][:-1]
			if len(ret) > 1 and ret[0]['contents'][0] == os.sep:
				ret[0]['contents'] = ret[0]['contents'][1:]
		return ret


cwd = with_docstring(CwdSegment(),
'''Return the current working directory.

Returns a segment list to create a breadcrumb-like effect.

:param int dir_shorten_len:
	shorten parent directory names to this length (e.g. 
	:file:`/long/path/to/powerline` → :file:`/l/p/t/powerline`)
:param int dir_limit_depth:
	limit directory depth to this number (e.g. 
	:file:`/long/path/to/powerline` → :file:`⋯/to/powerline`)
:param bool use_path_separator:
	Use path separator in place of soft divider.
:param bool shorten_home:
	Shorten home directory to ``~``.
:param str ellipsis:
	Specifies what to use in place of omitted directories. Use None to not 
	show this subsegment at all.

Divider highlight group used: ``cwd:divider``.

Highlight groups used: ``cwd:current_folder`` or ``cwd``. It is recommended to define all highlight groups.
''')


try:
	import psutil

	# psutil-2.0.0: psutil.Process.username is unbound method
	if callable(psutil.Process.username):
		def _get_user():
			return psutil.Process(os.getpid()).username()
	# pre psutil-2.0.0: psutil.Process.username has type property
	else:
		def _get_user():
			return psutil.Process(os.getpid()).username
except ImportError:
	try:
		import pwd
	except ImportError:
		from getpass import getuser as _get_user
	else:
		try:
			from os import geteuid as getuid
		except ImportError:
			from os import getuid

		def _get_user():
			return pwd.getpwuid(getuid()).pw_name


username = False
# os.geteuid is not available on windows
_geteuid = getattr(os, 'geteuid', lambda: 1)


def user(pl, hide_user=None):
	'''Return the current user.

	:param str hide_user:
		Omit showing segment for users with names equal to this string.

	Highlights the user with the ``superuser`` if the effective user ID is 0.

	Highlight groups used: ``superuser`` or ``user``. It is recommended to define all highlight groups.
	'''
	global username
	if username is False:
		username = _get_user()
	if username is None:
		pl.warn('Failed to get username')
		return None
	if username == hide_user:
		return None
	euid = _geteuid()
	return [{
		'contents': username,
		'highlight_groups': ['user'] if euid != 0 else ['superuser', 'user'],
	}]
