
#------------------------------------------------------------------------------
# $File: lisp,v 1.23 2009/09/19 16:28:10 christos Exp $
# lisp:  file(1) magic for lisp programs
#
# various lisp types, from Daniel Quinlan (quinlan@yggdrasil.com)

# updated by Joerg Jenderek
# GRR: This lot is too weak
#0	string	;;			
# windows INF files often begin with semicolon and use CRLF as line end
# lisp files are mainly created on unix system with LF as line end
#>2	search/4096	!\r		Lisp/Scheme program text
#>2	search/4096	\r		Windows INF file

0	search/4096	(setq\ 			Lisp/Scheme program text
!:mime	text/x-lisp
0	search/4096	(defvar\ 		Lisp/Scheme program text
!:mime	text/x-lisp
0	search/4096	(defparam\ 		Lisp/Scheme program text
!:mime	text/x-lisp
0	search/4096	(defun\  		Lisp/Scheme program text
!:mime	text/x-lisp
0	search/4096	(autoload\ 		Lisp/Scheme program text
!:mime	text/x-lisp
0	search/4096	(custom-set-variables\ 	Lisp/Scheme program text
!:mime	text/x-lisp

# Emacs 18 - this is always correct, but not very magical.
0	string	\012(			Emacs v18 byte-compiled Lisp data
!:mime	application/x-elc
# Emacs 19+ - ver. recognition added by Ian Springer
# Also applies to XEmacs 19+ .elc files; could tell them apart with regexs
# - Chris Chittleborough <cchittleborough@yahoo.com.au>
0	string	;ELC	
>4	byte	>18			
>4	byte    <32			Emacs/XEmacs v%d byte-compiled Lisp data
!:mime	application/x-elc		

# Files produced by CLISP Common Lisp From: Bruno Haible <haible@ilog.fr>
0	string	(SYSTEM::VERSION\040'	CLISP byte-compiled Lisp program (pre 2004-03-27)
0	string	(|SYSTEM|::|VERSION|\040'	CLISP byte-compiled Lisp program text

0	long	0x70768BD2		CLISP memory image data
0	long	0xD28B7670		CLISP memory image data, other endian

#.com and .bin for MIT scheme 
0	string	\372\372\372\372	MIT scheme (library?)

# From: David Allouche <david@allouche.net>
0	search/1	\<TeXmacs|	TeXmacs document text
!:mime	text/texmacs
