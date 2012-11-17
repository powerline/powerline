" Powerline vim example
" Run with :source %

python import sys, vim, os
python sys.path.append(vim.eval('expand("<sfile>:h:h:h")'))
python from examples.vim.powerline import statusline

if exists('*pyeval')
	let s:pyeval=function('pyeval')
else
	python import json
	function! s:pyeval(e)
		python vim.command('return ' + json.dumps(eval(vim.eval('a:e'))))
	endfunction
endif

function! DynStl()
	return s:pyeval('statusline()')
endfunction

set stl=%!DynStl()
