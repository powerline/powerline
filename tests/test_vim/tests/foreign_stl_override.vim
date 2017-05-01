scriptencoding utf-8
set encoding=utf-8
let g:powerline_config_paths = [expand('<sfile>:p:h:h:h:h') . '/powerline/config_files']
set laststatus=2
redir => g:messages
	try
		source <sfile>:p:h:h:h:h/powerline/bindings/vim/plugin/powerline.vim
		redrawstatus!
		vsplit
		redrawstatus!
		setlocal statusline=«»
		redrawstatus!
	catch
		call writefile(['Unexpected exception', v:exception], 'message.fail')
		cquit
	endtry
redir END
if g:messages =~# '\v\S'
	call writefile(['Unexpected messages'] + split(g:messages, "\n", 1), 'message.fail')
	cquit
endif
qall!
