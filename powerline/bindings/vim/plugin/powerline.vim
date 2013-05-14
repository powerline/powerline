if exists('g:powerline_loaded')
    finish
endif
let g:powerline_loaded = 1

function! s:CriticalError(message)
	echohl ErrorMsg
	echomsg a:message
	echohl None
endfunction

if ! has('python') && ! has('python3')
	call s:CriticalError('You need vim compiled with Python 2.6+ or 3.2+ support
		\ for Powerline to work. Please consult the documentation for more details.')
	finish
endif

let s:pycmd = substitute(get(g:, 'powerline_pycmd', has('python') ? 'py' : 'py3'),
			\'\v^(py)%[thon](3?)$', '\1\2', '')
let s:pyeval = get(g:, 'powerline_pyeval', s:pycmd.'eval')

let s:import_cmd = 'from powerline.vim import setup as powerline_setup'
try
	execute s:pycmd "try:\n"
				\  ."	".s:import_cmd."\n"
				\  ."except ImportError:\n"
				\  ."	import sys, vim\n"
				\  ."	sys.path.append(vim.eval('expand(\"<sfile>:h:h:h:h:h\")'))\n"
				\  ."	".s:import_cmd
	let s:launched = 1
finally
	if !exists('s:launched')
		call s:CriticalError('An error occurred while importing the Powerline package.
			\ This could be caused by an invalid sys.path setting, or by an incompatible
			\ Python version (Powerline requires Python 2.6+ or 3.2+ to work). Please consult
			\ the troubleshooting section in the documentation for possible solutions.')
		finish
	else
		unlet s:launched
	endif
endtry

execute s:pycmd 'powerline_setup(pyeval=vim.eval("s:pyeval"), pycmd=vim.eval("s:pycmd"))'
execute s:pycmd 'del powerline_setup'
