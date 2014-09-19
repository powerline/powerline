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
	for func in dir(tuple):
		if func in ('__getitem__', '__init__', '__getattribute__', '__len__', '__iter__'):
			continue
		exec((
			'def {0}(self, *args, **kwargs):\n'
			'	raise TypeError("{0} is not allowed for Context")'
		).format(func))
	del func

	__slots__ = ()

	def __new__(cls, base, context_key=None, context_value=None):
		if context_key is not None:
			assert(context_value is not None)
			assert(type(base) is Context)
			havemarks(context_key, context_value)
			return tuple.__new__(cls, tuple.__add__(base, ((context_key, context_value),)))
		else:
			havemarks(base)
			return tuple.__new__(cls, ((MarkedUnicode('', base.mark), base),))

	@property
	def key(self):
		return key_sep.join((c[0] for c in self))

	def enter_key(self, value, key):
		return self.enter(value.keydict[key], value[key])

	def enter_item(self, name, item):
		return self.enter(MarkedUnicode(name, item.mark), item)

	def enter(self, context_key, context_value):
		return Context.__new__(Context, self, context_key, context_value)
