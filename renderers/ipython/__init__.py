# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.renderers.shell import ShellRenderer
from powerline.renderers.shell.readline import ReadlineRenderer
from powerline.theme import Theme


class IPythonRenderer(ShellRenderer):
	'''Powerline ipython segment renderer.'''
	def get_segment_info(self, segment_info, mode):
		r = self.segment_info.copy()
		r['ipython'] = segment_info
		return r

	def get_theme(self, matcher_info):
		if matcher_info == 'in':
			return self.theme
		else:
			match = self.local_themes[matcher_info]
			try:
				return match['theme']
			except KeyError:
				match['theme'] = Theme(
					theme_config=match['config'],
					main_theme_config=self.theme_config,
					**self.theme_kwargs
				)
				return match['theme']

	def shutdown(self):
		self.theme.shutdown()
		for match in self.local_themes.values():
			if 'theme' in match:
				match['theme'].shutdown()

	def render(self, **kwargs):
		# XXX super(ShellRenderer), *not* super(IPythonRenderer)
		return super(ShellRenderer, self).render(**kwargs)

	def do_render(self, segment_info, **kwargs):
		segment_info.update(client_id='ipython')
		return super(IPythonRenderer, self).do_render(
			segment_info=segment_info,
			**kwargs
		)


class IPythonPromptRenderer(IPythonRenderer, ReadlineRenderer):
	'''Powerline ipython prompt (in and in2) renderer'''
	pass


class IPythonNonPromptRenderer(IPythonRenderer):
	'''Powerline ipython non-prompt (out and rewrite) renderer'''
	pass


class RendererProxy(object):
	'''Powerline IPython renderer proxy which chooses appropriate renderer

	Instantiates two renderer objects: one will be used for prompts and the 
	other for non-prompts.
	'''
	def __init__(self, **kwargs):
		old_widths = {}
		self.non_prompt_renderer = IPythonNonPromptRenderer(old_widths=old_widths, **kwargs)
		self.prompt_renderer = IPythonPromptRenderer(old_widths=old_widths, **kwargs)

	def render_above_lines(self, *args, **kwargs):
		return self.non_prompt_renderer.render_above_lines(*args, **kwargs)

	def render(self, is_prompt, *args, **kwargs):
		return (self.prompt_renderer if is_prompt else self.non_prompt_renderer).render(
			*args, **kwargs)

	def shutdown(self, *args, **kwargs):
		self.prompt_renderer.shutdown(*args, **kwargs)
		self.non_prompt_renderer.shutdown(*args, **kwargs)


renderer = RendererProxy
