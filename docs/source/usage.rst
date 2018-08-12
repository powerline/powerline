*****
Usage
*****

Application-specific requirements
---------------------------------

Vim plugin requirements
^^^^^^^^^^^^^^^^^^^^^^^

The vim plugin requires a vim version with Python support compiled in. Presence 
of Python support in Vim can be checked by running ``vim --version | grep 
+python``.

If Python support is absent then Vim needs to be compiled with it. To do this 
use ``--enable-pythoninterp`` :file:`./configure` flag (Python 3 uses 
``--enable-python3interp`` flag instead). Note that this also requires the 
related Python headers to be installed. Please consult distribution’s 
documentation for details on how to compile and install packages.

Vim version 7.4 or newer is recommended for performance reasons, but Powerline 
supports Vim 7.0.112 and higher.

Shell prompts requirements
^^^^^^^^^^^^^^^^^^^^^^^^^^

Due to fish having incorrect code for prompt width calculations up to version 
2.1 and no way to tell that certain sequence of characters has no width 
(``%{…%}`` in zsh and ``\[…\]`` in bash prompts serve exactly this purpose) 
users that have fish versions below 2.1 are not supported..


WM widgets requirements
^^^^^^^^^^^^^^^^^^^^^^^

Awesome is supported starting from version 3.5.1, inclusive. QTile is supported 
from version 0.6, inclusive.

.. _usage-terminal-emulators:

Terminal emulator requirements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Powerline uses several special glyphs to get the arrow effect and some custom 
symbols for developers. This requires either a symbol font or a patched font 
installed. Used terminal emulator must also support either patched fonts or 
fontconfig for Powerline to work properly.

:ref:`24-bit color support <config-common-term_truecolor>` can also be enabled 
if terminal emulator supports it.

.. table:: Application/terminal emulator feature support matrix
   :name: term-feature-support-matrix

   ===================== ======= ===================== ===================== =====================
   Name                  OS      Patched font support  Fontconfig support    24-bit color support 
   ===================== ======= ===================== ===================== =====================
   Gvim                  Linux   |i_yes|               |i_no|                |i_yes|
   iTerm2                OS X    |i_yes|               |i_no|                |i_no|
   Konsole               Linux   |i_yes|               |i_yes|               |i_yes|
   lxterminal            Linux   |i_yes|               |i_yes|               |i_no|
   MacVim                OS X    |i_yes|               |i_no|                |i_yes|
   rxvt-unicode          Linux   |i_partial| [#]_      |i_no|                |i_no|
   st                    Linux   |i_yes|               |i_yes|               |i_yes| [#]_
   Terminal.app          OS X    |i_yes|               |i_no|                |i_no|
   libvte-based [#]_     Linux   |i_yes|               |i_yes|               |i_yes| [#]_
   xterm                 Linux   |i_yes|               |i_no|                |i_partial| [#]_
   fbterm                Linux   |i_yes|               |i_yes|               |i_no|
   ===================== ======= ===================== ===================== =====================

.. |i_yes| image:: _static/img/icons/tick.png
.. |i_no| image:: _static/img/icons/cross.png
.. |i_partial| image:: _static/img/icons/error.png

.. [#] Must be compiled with ``--enable-unicode3`` for the patched font to work.
.. [#] Since version 0.5.
.. [#] Including XFCE terminal and GNOME terminal.
.. [#] Since version 0.36.
.. [#] Uses nearest color from 8-bit palette.

Plugins
-------

.. toctree::

   usage/shell-prompts
   usage/wm-widgets
   usage/other
