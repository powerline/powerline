# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import json

from powerline.lib.dict import REMOVE_THIS_KEY, mergedicts


def parse_value(s):
	'''Convert string to Python object

	Rules:

	* Empty string means that corresponding key should be removed from the 
	  dictionary.
	* Strings that start with a minus, digit or with some character that starts 
	  JSON collection or string object are parsed as JSON.
	* JSON special values ``null``, ``true``, ``false`` (case matters) are 
	  parsed  as JSON.
	* All other values are considered to be raw strings.

	:param str s: Parsed string.

	:return: Python object.
	'''
	if not s:
		return REMOVE_THIS_KEY
	elif s[0] in '"{[0193456789-' or s in ('null', 'true', 'false'):
		return json.loads(s)
	else:
		return s


def keyvaluesplit(s):
	'''Split K1.K2=VAL into K1.K2 and parsed VAL
	'''
	if '=' not in s:
		raise TypeError('Option must look like option=json_value')
	if s[0] == '_':
		raise ValueError('Option names must not start with `_\'')
	idx = s.index('=')
	o = s[:idx]
	val = parse_value(s[idx + 1:])
	return (o, val)


def parsedotval(s):
	'''Parse K1.K2=VAL into {"K1":{"K2":VAL}}

	``VAL`` is processed according to rules defined in :py:func:`parse_value`.
	'''
	if type(s) is tuple:
		o, val = s
		val = parse_value(val)
	else:
		o, val = keyvaluesplit(s)

	keys = o.split('.')
	if len(keys) > 1:
		r = (keys[0], {})
		rcur = r[1]
		for key in keys[1:-1]:
			rcur[key] = {}
			rcur = rcur[key]
		rcur[keys[-1]] = val
		return r
	else:
		return (o, val)


def parse_override_var(s):
	'''Parse a semicolon-separated list of strings into a sequence of values

	Emits the same items in sequence as :py:func:`parsedotval` does.
	'''
	return (
		parsedotval(item)
		for item in s.split(';')
		if item
	)


def get_env_config_paths(environ):
	'''Get config paths from environment

	:param dict environ:
		Environment from which paths should be obtained.

	:return: Paths from ``POWERLINE_CONFIG_PATHS`` as a list. List may be empty.
	'''
	return [path for path in environ.get('POWERLINE_CONFIG_PATHS', '').split(':') if path]


def _get_env_overrides(environ, varname):
	'''Get overrides from environment

	:param dict environ:
		Environment from which overrides should be obtained.
	:param str varname:
		Name of the variable containing overrides.

	:return:
		Iterable (may be empty) containing a sequence of overrides, where each 
		item is similar to what :py:func:`powerline.lib.overrides.parsedotval` 
		returns.
	'''
	return parse_override_var(environ.get(varname, ''))


def get_env_config_overrides(environ):
	'''Get config overrides from environment

	:param dict environ:
		Environment from which overrides should be obtained.

	:return:
		Iterable (may be empty) containing a sequence of overrides, where each 
		item is similar to what :py:func:`powerline.lib.overrides.parsedotval` 
		returns.
	'''
	return _get_env_overrides(environ, 'POWERLINE_CONFIG_OVERRIDES')


def get_env_theme_overrides(environ):
	'''Get config overrides from environment

	:param dict environ:
		Environment from which overrides should be obtained.

	:return:
		Iterable (may be empty) containing a sequence of overrides, where each 
		item is similar to what :py:func:`powerline.lib.overrides.parsedotval` 
		returns.
	'''
	return _get_env_overrides(environ, 'POWERLINE_THEME_OVERRIDES')


def override_theme_config(theme, name, override):
	'''Update theme with given overrides

	:param dict theme:
		Updated theme.
	:param str name:
		Theme name.
	:param dict override:
		Dictionary containing overrides. May be any false value in which case 
		nothing is done.

	:return: ``theme`` argument, possibly modified.
	'''
	if override and name in override:
		mergedicts(theme, override[name])
	return theme


def override_main_config(config, override):
	'''Update main config with given overrides

	:param dict config:
		Updated config.
	:param dict override:
		Dictionary containing overrides. May be any false value in which case 
		nothing is done.

	:return: ``config`` argument, possibly modified.
	'''
	if override:
		mergedicts(config, override)
	return config
