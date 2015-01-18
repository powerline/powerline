# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline import Powerline
from powerline.lib.dict import mergedicts
from powerline.lib.unicode import string


# HACK: ipython tries to only leave us with plain ASCII
class RewriteResult(object):
	def __init__(self, prompt):
		self.prompt = string(prompt)

	def __str__(self):
		return self.prompt

	def __add__(self, s):
		if type(s) is not str:
			try:
				s = s.encode('utf-8')
			except AttributeError:
				raise NotImplementedError
		return RewriteResult(self.prompt + s)


class IPythonPowerline(Powerline):
	def init(self, **kwargs):
		super(IPythonPowerline, self).init(
			'ipython',
			use_daemon_threads=True,
			**kwargs
		)

	def get_config_paths(self):
		if self.config_paths:
			return self.config_paths
		else:
			return super(IPythonPowerline, self).get_config_paths()

	def get_local_themes(self, local_themes):
		return dict(((type, {'config': self.load_theme_config(name)}) for type, name in local_themes.items()))

	def load_main_config(self):
		r = super(IPythonPowerline, self).load_main_config()
		if self.config_overrides:
			mergedicts(r, self.config_overrides)
		return r

	def load_theme_config(self, name):
		r = super(IPythonPowerline, self).load_theme_config(name)
		if name in self.theme_overrides:
			mergedicts(r, self.theme_overrides[name])
		return r

	def do_setup(self, wrefs):
		for wref in wrefs:
			obj = wref()
			if obj is not None:
				setattr(obj, 'powerline', self)
