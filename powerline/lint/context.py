# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import itertools

from powerline.lib.unicode import unicode
from powerline.lint.markedjson.markedvalue import MarkedUnicode
from powerline.lint.selfcheck import havemarks


class JStr(unicode):
	def join(self, iterable):
		return super(JStr, self).join((unicode(item) for item in iterable))


key_sep = JStr('/')
list_sep = JStr(', ')


def new_context_item(key, value):
	return ((value.keydict[key], value[key]),)


def list_themes(data, context):
	theme_type = data['theme_type']
	ext = data['ext']
	main_theme_name = data['main_config'].get('ext', {}).get(ext, {}).get('theme', None)
	is_main_theme = (data['theme'] == main_theme_name)
	if theme_type == 'top':
		return list(itertools.chain(*[
			[(theme_ext, theme) for theme in theme_configs.values()]
			for theme_ext, theme_configs in data['theme_configs'].items()
		]))
	elif theme_type == 'main' or is_main_theme:
		return [(ext, theme) for theme in data['ext_theme_configs'].values()]
	else:
		return [(ext, context[0][1])]


class Context(tuple):
	def __new__(cls, base, other=None):
		if other is not None:
			return tuple.__new__(cls, tuple.__add__(base, other))
		else:
			return tuple.__new__(cls, ((MarkedUnicode('', base.mark), base),))

	def __add__(self, arg):
		assert(len(arg) == 1)
		assert(type(arg) is tuple)
		assert(len(arg[0]) == 2)
		assert(type(arg[0]) is tuple)
		havemarks(arg[0][0], arg[0][1])
		return Context.__new__(Context, self, arg)

	@property
	def key(self):
		return key_sep.join((c[0] for c in self))

	def enter_key(self, value, key):
		return self + ((value.keydict[key], value[key]),)
