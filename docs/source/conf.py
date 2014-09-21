# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os
import sys


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(os.getcwd()))))
sys.path.insert(0, os.path.abspath(os.getcwd()))

extensions = ['powerline_autodoc', 'sphinx.ext.todo', 'sphinx.ext.coverage', 'sphinx.ext.viewcode']
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

on_rtd = os.environ.get('READTHEDOCS', None) == 'True'

if not on_rtd:  # only import and set the theme if we’re building docs locally
	try:
		import sphinx_rtd_theme
		html_theme = 'sphinx_rtd_theme'
		html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
	except ImportError:
		pass
