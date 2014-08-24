*****
Usage
*****

Application-specific requirements
---------------------------------

Vim plugin requirements
^^^^^^^^^^^^^^^^^^^^^^^

The vim plugin requires a vim version with Python support compiled in.  You 
can check if your vim supports Python by running ``vim --version | grep 
+python``.

If your vim version doesn't have support for Python, you'll have to compile 
it with the ``--enable-pythoninterp`` flag (``--enable-python3interp`` if 
you want Python 3 support instead). Note that this also requires the related 
Python headers to be installed on your system. Please consult your 
distribution's documentation for details on how to compile and install 
packages.

Vim version 7.4 or newer is recommended for performance reasons, but Powerline 
is known to work on vim-7.0.112 (some segments may not work though as it was not 
actually tested).

.. _usage-terminal-emulators:

Terminal emulator requirements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Powerline uses several special glyphs to get the arrow effect and some 
custom symbols for developers. This requires that you either have a symbol 
font or a patched font on your system. Your terminal emulator must also 
support either patched fonts or fontconfig for Powerline to work properly.

You can also enable :ref:`24-bit color support <config-common-term_truecolor>` 
if your terminal emulator supports it.

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
