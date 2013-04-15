# vim:fileencoding=utf-8:noet

from powerline import Powerline
from powerline.lib import mergedicts
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


class IpythonPowerline(Powerline):
	def __init__(self, is_prompt, old_widths):
		super(IpythonPowerline, self).__init__(
			'ipython',
			renderer_module=('.prompt' if is_prompt else None),
			use_daemon_threads=True
		)
		self.old_widths = old_widths

	def create_renderer(self, *args, **kwargs):
		super(IpythonPowerline, self).create_renderer(*args, **kwargs)
		self.renderer.old_widths = self.old_widths

	def get_config_paths(self):
		if self.paths:
			return self.paths
		else:
			return super(IpythonPowerline, self).get_config_paths()

	def get_local_themes(self, local_themes):
		return dict(((type, {'config': self.load_theme_config(name)}) for type, name in local_themes.items()))

	def load_main_config(self):
		r = super(IpythonPowerline, self).load_main_config()
		if self.config_overrides:
			mergedicts(r, self.config_overrides)
		return r

	def load_theme_config(self, name):
		r = super(IpythonPowerline, self).load_theme_config(name)
		if name in self.theme_overrides:
			mergedicts(r, self.theme_overrides[name])
		return r

	def setup(self, attr, obj):
		setattr(obj, attr, self)
		super(IpythonPowerline, self).setup(attr, obj)
