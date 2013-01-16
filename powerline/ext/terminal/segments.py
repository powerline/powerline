# -*- coding: utf-8 -*-

import os
import re
import socket

from powerline.lib.vcs import guess


def hostname():
	if not os.environ.get('SSH_CLIENT'):
		return None
	return socket.gethostname()


def user():
	user = os.environ.get('USER')
	euid = os.geteuid()
	return {
		'contents': user,
		'highlight': 'user' if euid != 0 else ['superuser', 'user'],
		}


def branch():
	repo = guess(os.path.abspath(os.getcwd()))
	if repo:
		return repo.branch()
	return None


def cwd(dir_shorten_len=None, dir_limit_depth=None):
	cwd = os.getcwdu()
	home = os.environ.get('HOME')
	if home:
		cwd = re.sub('^' + re.escape(home), '~', cwd, 1)
	cwd_split = cwd.split(os.sep)
	cwd_split_len = len(cwd_split)
	if cwd_split_len > dir_limit_depth + 1:
		del(cwd_split[0:-dir_limit_depth])
		cwd_split.insert(0, u'⋯')
	cwd = [i[0:dir_shorten_len] if dir_shorten_len and i else i for i in cwd_split[:-1]] + [cwd_split[-1]]
	cwd = os.path.join(*cwd)
	return cwd
