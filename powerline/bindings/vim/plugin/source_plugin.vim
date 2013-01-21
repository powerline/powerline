if ! has('python') && ! has('python3')
	echohl ErrorMsg
	echomsg 'You need vim compiled with Python 3.3 or Python 2.7 support for Powerline to work. Please consult the documentation for more details.'
	echohl None
	finish
endif

python <<EOF
import sys, vim
sys.path.append(vim.eval('expand("<sfile>:h:h:h:h:h")'))
from powerline.bindings.vim import source_plugin
source_plugin()
EOF
