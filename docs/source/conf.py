# vim:fileencoding=utf-8:noet

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(os.getcwd()))))
sys.path.insert(0, os.path.abspath(os.getcwd()))

extensions = ['powerline_autodoc', 'sphinx.ext.todo', 'sphinx.ext.coverage', 'sphinx.ext.viewcode']
source_suffix = '.rst'
master_doc = 'index'
project = u'Powerline'
copyright = u'Kim Silkebækken'
version = 'beta'
release = 'beta'
exclude_patterns = ['_build']
pygments_style = 'sphinx'
html_theme = 'default'
html_static_path = ['_static']
