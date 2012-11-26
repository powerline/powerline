=========
Powerline
=========

:Author: Kim Silkebækken (kim.silkebaekken+vim@gmail.com)
:Source: https://github.com/Lokaltog/powerline

**This is alpha software, expect things to change or break at any point.**

This is the next version of Powerline, implemented in Python. It aims to 
resolve some of the "unresolvable" problems of the vimscript implementation, 
as well as providing a common code base for all projects that use Powerline 
in some way (e.g. shell prompts and tmux themes).

Some of the new features for vim are:

* **Dynamic statusline evaluation in Python.** Python performs really well 
  and allows Powerline to re-render the statusline in Python instead of 
  relying on vim's statusline flags. This means no more caching, and much 
  more flexibility.
* **Automatic removal of less important segments in small windows.** Not all 
  information is equally important to have in the statusline, and segments 
  with e.g. encoding and file format information are automatically removed 
  in smaller windows.
* **The possibility of adding more segments.** Because of vim's hardcoded 
  limitation of 80 statusline options, the vimscript implementation 
  triggered an error when adding more segments to the default theme. Since 
  segment contents are now rendered as plain text in Python it's possible to 
  add many more segments in the statusline before hitting this limit.
