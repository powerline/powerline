# -*- coding: utf-8 -*-

import sys, os

sys.path.insert(0, os.path.abspath('../powerline'))

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.todo', 'sphinx.ext.coverage', 'sphinx.ext.viewcode']
source_suffix = '.rst'
master_doc = 'index'
project = u'Powerline'
copyright = u'Kim Silkebækken'
version = 'dev'
release = 'dev'
exclude_patterns = ['_build']
pygments_style = 'sphinx'
html_theme = 'nature'
html_static_path = ['_static']
