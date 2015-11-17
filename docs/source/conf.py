# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os
import sys


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(os.getcwd()))))
sys.path.insert(0, os.path.abspath(os.getcwd()))

extensions = [
	'powerline_autodoc', 'powerline_automan',
	'sphinx.ext.todo', 'sphinx.ext.coverage', 'sphinx.ext.viewcode',
]
source_suffix = '.rst'
master_doc = 'index'
project = 'Powerline'
version = 'beta'
release = 'beta'
exclude_patterns = ['_build']
pygments_style = 'sphinx'

html_theme = 'default'
html_static_path = ['_static']
html_show_copyright = False

latex_show_urls = 'footnote'
latex_elements = {
	'preamble': '''
		\\DeclareUnicodeCharacter{22EF}{$\\cdots$}   % Dots
		\\DeclareUnicodeCharacter{2665}{\\ding{170}} % Heart
		\\DeclareUnicodeCharacter{2746}{\\ding{105}} % Snow
		\\usepackage{pifont}
	''',
}

man_pages = []
for doc in os.listdir(os.path.join(os.path.dirname(__file__), 'commands')):
	if doc.endswith('.rst'):
		name = doc[:-4]
		module = 'powerline.commands.{0}'.format(name)
		get_argparser = __import__(str(module), fromlist=[str('get_argparser')]).get_argparser
		parser = get_argparser()
		description = parser.description
		man_pages.append([
			'commands/' + name,
			'powerline' if name == 'main' else 'powerline-' + name,
			description,
			'',
			1
		])

on_rtd = os.environ.get('READTHEDOCS', None) == 'True'

if not on_rtd:  # only import and set the theme if we’re building docs locally
	try:
		import sphinx_rtd_theme
		html_theme = 'sphinx_rtd_theme'
		html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
	except ImportError:
		pass

if on_rtd or html_theme == 'sphinx_rtd_theme':
	html_context = {
		'css_files': [
			'https://media.readthedocs.org/css/sphinx_rtd_theme.css',
			'https://media.readthedocs.org/css/readthedocs-doc-embed.css',
			'_static/css/theme_overrides.css',
		],
	}
