#!/usr/bin/vim -S
set nocompatible
try
	source powerline/bindings/vim/plugin/powerline.vim
catch
	cquit
endtry
set ls=2
redrawstatus!
redir =>mes
	messages
redir END
if len(split(mes, "\n"))>1
	cquit
endif
quit!
