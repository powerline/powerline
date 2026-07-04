# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os

from powerline import Powerline
from powerline.lib.dict import mergedicts
from powerline.lib.overrides import parse_override_var
from powerline.lib.dict import mergeargs


class PsqlPowerline(Powerline):
	'''psql-specific powerline bindings.

	Designed for PostgreSQL psql :varname:`PROMPT_COMMAND` support (companion
	patch to postgres/postgres; see docs/source/usage/psql-postgres-integration.rst
	and ``src/bin/psql/powerline-integration.md`` in that tree).
	'''

	def init(self, **kwargs):
		return super(PsqlPowerline, self).init(
			ext='psql',
			renderer_module='psql',
			**kwargs
		)

	def load_main_config(self):
		r = super(PsqlPowerline, self).load_main_config()
		config_overrides = os.environ.get('POWERLINE_CONFIG_OVERRIDES')
		if config_overrides:
			mergedicts(r, mergeargs(parse_override_var(config_overrides)))
		return r

	def load_theme_config(self, name):
		r = super(PsqlPowerline, self).load_theme_config(name)
		theme_overrides = os.environ.get('POWERLINE_THEME_OVERRIDES')
		if theme_overrides:
			theme_overrides_dict = mergeargs(parse_override_var(theme_overrides))
			if name in theme_overrides_dict:
				mergedicts(r, theme_overrides_dict[name])
		return r

	def get_config_paths(self):
		paths = [path for path in os.environ.get('POWERLINE_CONFIG_PATHS', '').split(':') if path]
		return paths or super(PsqlPowerline, self).get_config_paths()