Introduction
============

This is the next version of Powerline, implemented in Python. It aims to 
resolve some of the "unresolvable" problems of the vimscript implementation, 
as well as providing a common code base for all projects that use Powerline 
in some way (e.g. shell prompts and tmux themes).

The project is currently in beta, and most of the functionality in the old 
vimscript project is already implemented.

Feature highlights
------------------

* **Better performance.** Python performs quite a bit better than vimscript, 
  and by having most of the code in Python instead of vimscript it's also 
  much easier to profile the code and eliminate bottlenecks.
* **A much leaner code base.** With most of the functionality of the old 
  project implemented the new version consists of less than half the amount 
  of code.
* **Automatic removal of less important segments in small windows.** Not all 
  information is equally important to have in the statusline, and segments 
  with e.g.  encoding and file format information are automatically removed 
  in smaller windows.
* **Dynamic statusline evaluation in Python.** Statuslines are dynamically 
  rendered in Python instead of relying on vim's statusline flags, which 
  allows much more flexibility when creating statuslines.
* **The possibility of adding more segments.** Because of vim's hardcoded 
  limitation of 80 statusline options, the vimscript implementation 
  triggered an error when adding more segments to the default theme. Since 
  segment contents are now rendered as plain text in Python it's possible to 
  add many more segments in the statusline before reaching this limit.
* **New and improved theme and colorscheme syntax.** Themes and colorschemes 
  are now written in JSON, with a much cleaner syntax that's easier to learn 
  and work with. Themes and colorschemes are also much more configurable, 
  and it's easy to write your own and store them in your home config 
  directory (usually ``~/.config/powerline``).
