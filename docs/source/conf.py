# vim:fileencoding=utf-8:noet

import os
import sys

sys.path.insert(0, os.path.abspath('../..'))

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.todo', 'sphinx.ext.coverage', 'sphinx.ext.viewcode']
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
