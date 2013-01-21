if ! has('python') && ! has('python3')
	echohl ErrorMsg
	echomsg 'You need vim compiled with Python 3.3 or Python 2.7 support for Powerline to work. Please consult the documentation for more details.'
	echohl None
	finish
endif

let s:pycmd = has('python3') ? 'python3' : 'python'

exec s:pycmd ' import sys, vim'
exec s:pycmd ' sys.path.append(vim.eval(''expand("<sfile>:h:h:h:h:h")''))'

source <sfile>:h:h/powerline.vim
