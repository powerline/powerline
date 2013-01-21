if ! has('python')
	echohl ErrorMsg
	echomsg 'You need vim compiled with Python 2 support for Powerline to work. Please consult the documentation for more details.'
	echohl None
	finish
endif

python import sys, vim
python sys.path.append(vim.eval('expand("<sfile>:h:h:h:h:h")'))

source <sfile>:h:h/powerline.vim
