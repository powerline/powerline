# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.renderers.shell import ShellRenderer
from powerline.renderers.shell.readline import ReadlineRenderer
from powerline.renderers.ipython import IPythonRenderer


class IPythonPre50Renderer(IPythonRenderer, ShellRenderer):
	'''Powerline ipython segment renderer for pre-5.0 IPython versions.'''
	def render(self, **kwargs):
		# XXX super(ShellRenderer), *not* super(IPythonPre50Renderer)
		return super(ShellRenderer, self).render(**kwargs)

	def do_render(self, segment_info, **kwargs):
		segment_info.update(client_id='ipython')
		return super(IPythonPre50Renderer, self).do_render(
			segment_info=segment_info,
			**kwargs
		)


class IPythonPromptRenderer(IPythonPre50Renderer, ReadlineRenderer):
	'''Powerline ipython prompt (in and in2) renderer'''
	pass


class IPythonNonPromptRenderer(IPythonPre50Renderer):
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
