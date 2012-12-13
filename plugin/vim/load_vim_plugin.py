import os
import vim

vim.command('source ' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'powerline.vim'))
