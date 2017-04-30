let g:powerline_use_var_handler = 1

let g:pyfiles_root=expand('<sfile>:p:h').'/pyfiles'
let g:root=expand('<sfile>:p:h:h:h')
let g:mf=fnamemodify('message.fail', ':p')

command -nargs=1 LST :call writefile(<args>, g:mf, 'a') | cquit
command -nargs=1 ERR :LST [<args>]
command -nargs=1 EXC :ERR 'Unexpected exception', <q-args>, v:exception, v:throwpoint

function EnablePlugins(...)
	let &runtimepath = join(map(copy(a:000), 'escape(g:root."/tests/vim-plugins/".v:val, "\\,")'), ',')
	try
		runtime! plugin/*.vim
		silent doautocmd BufWinEnter
		silent doautocmd BufEnter
		silent doautocmd VimEnter
	catch
		EXC EnablePlugins
	endtry
endfunction
function RecordStatusline()
	let g:statusline = &l:statusline
	if g:statusline[:1] is# '%!'
		let g:statusline_value=eval(g:statusline[2:])
	else
		ERR 'Statusline does not start with %!', g:statusline
	endif
	return ''
endfunction
function SourcePowerline()
	let g:powerline_config_paths = [g:root . '/powerline/config_files']
	try
		execute 'source' fnameescape(g:root . '/powerline/bindings/vim/plugin/powerline.vim')
	catch
		EXC SourcePowerline
	endtry
endfunction
function NDiff(actual, expected)
	return systemlist(shellescape(g:root.'/tests/bot-ci/scripts/ndiff-strings.py').' '.shellescape(a:actual).' '.shellescape(a:expected))
endfunction
function CheckStatuslineValue(actual, expected)
	if a:actual isnot# a:expected
		LST ['Expected different statusline value', a:actual, a:expected] + NDiff(a:actual, a:expected)
	endif
endfunction
function CheckRecordedStatuslineValue(expected)
	return CheckStatuslineValue(g:statusline_value, a:expected)
endfunction
function GetCurrentStatusline()
	if &l:statusline[:1] isnot# '%!'
		ERR 'Statusline does not start with %!', &l:statusline
	endif
	return eval(&l:statusline[2:])
endfunction
function CheckCurrentStatusline(expected)
	return CheckStatuslineValue(GetCurrentStatusline(), a:expected)
endfunction
function CheckMessages()
	if !empty(g:powerline_log_messages)
		LST ['Unexpected messages in log'] + g:powerline_log_messages
	endif
	redir => mes
		messages
	redir END
	let mesl = split(mes, "\n")[1:]
	if !empty(mesl)
		LST ['Unexpected messages'] + split(mes, "\n", 1)
	endif
endfunction
function RunPython(s)
	if has('python')
		execute 'python' a:s
	else
		execute 'python3' a:s
	endif
endfunction
function PyFile(f)
	if has('python')
		execute 'pyfile' fnameescape(g:pyfiles_root.'/'.a:f.'.py')
	else
		execute 'py3file' fnameescape(g:pyfiles_root.'/'.a:f.'.py')
	endif
endfunction

for s:c in ['noremap', 'noremap!']
	execute s:c '<special><expr>' '<Plug>(PowerlineTestRecordStatusline)' 'RecordStatusline()'
endfor
