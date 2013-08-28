***********************************
Font installation and configuration
***********************************

Powerline uses several special glyphs to get the arrow effect and some 
custom symbols for developers. This requires that you either have a symbol 
font or a patched font on your system. Your terminal emulator must also 
support either patched fonts or fontconfig for Powerline to work properly.

You can also enable :ref:`24-bit color support <config-common-term_truecolor>` 
if your terminal emulator supports it.

.. table:: Application/terminal emulator feature support matrix
   :name: term-feature-support-matrix

   ===================== ======= =================================== ===================== ===================== =====================
   Name                  OS      Recommended installation method     Patched font support  Fontconfig support    24-bit color support
   ===================== ======= =================================== ===================== ===================== =====================
   Gnome Terminal        Linux   `Fontconfig`_                       |i_yes|               |i_yes|               |i_no|
   Gvim                  Linux   `Patched font`_                     |i_yes|               |i_no|                |i_yes|
   Konsole               Linux   `Fontconfig`_                       |i_yes|               |i_yes|               |i_yes|
   lxterminal            Linux   `Fontconfig`_                       |i_yes|               |i_yes|               |i_no|
   rxvt-unicode          Linux   `rxvt-unicode`_ or `Patched font`_  |i_partial| [#]_      |i_no|                |i_no|
   st                    Linux   `Fontconfig`_                       |i_yes|               |i_yes|               |i_no|
   Xfce Terminal         Linux   `Fontconfig`_                       |i_yes|               |i_yes|               |i_no|
   xterm                 Linux   `Patched font`_                     |i_yes|               |i_no|                |i_partial| [#]_
   iTerm2                OS X    `Patched font`_                     |i_yes|               |i_no|                |i_no|
   MacVim                OS X    `Patched font`_                     |i_yes|               |i_no|                |i_yes|
   Terminal.app          OS X    `Patched font`_                     |i_yes|               |i_no|                |i_no|
   ===================== ======= =================================== ===================== ===================== =====================

.. |i_yes| image:: _static/img/icons/tick.png
.. |i_no| image:: _static/img/icons/cross.png
.. |i_partial| image:: _static/img/icons/error.png

.. [#] Must be compiled with ``--enable-unicode3`` for the 
   patched font to work.
.. [#] Uses nearest color from 8-bit palette.

Fontconfig
==========

This method only works on Linux. It's the recommended method if your 
terminal emulator supports it as you don't have to patch any fonts, and it 
generally works well with any coding font.

#. Download the latest version of the symbol font and fontconfig file::

      wget https://github.com/Lokaltog/powerline/raw/develop/font/PowerlineSymbols.otf
      wget https://github.com/Lokaltog/powerline/raw/develop/font/10-powerline-symbols.conf

#. Move the symbol font to a valid X font path. Valid font paths can be 
   listed with ``xset q``::

      mv PowerlineSymbols.otf ~/.fonts/

#. Update font cache for the path you moved the font to (you may need to be 
   root to update the cache for system-wide paths)::

      fc-cache -vf ~/.fonts/

#. Install the fontconfig file. For newer versions of fontconfig the config 
   path is ``~/.config/fontconfig/conf.d/``, for older versions it's  
   ``~/.fonts.conf.d/``::

      mv 10-powerline-symbols.conf ~/.config/fontconfig/conf.d/

If you can't see the custom symbols, please close all instances of your 
terminal emulator. You may need to restart X for the changes to take
effect.

If you *still* can't see the custom symbols, double-check that you have 
installed the font to a valid X font path, and that you have installed the 
fontconfig file to a valid fontconfig path. Alternatively try to install 
a `Patched font`_.

Patched font
============

This method is the fallback method and works for every terminal emulator and
OS, with the exception of `rxvt-unicode`_.

Download the font of your choice from `powerline-fonts`_. If you can't find 
your preferred font in the `powerline-fonts`_ repo, you'll have to patch 
your own font instead. See :ref:`font-patching` for instructions.

.. _powerline-fonts: https://github.com/Lokaltog/powerline-fonts

Installation on Linux
---------------------

#. Move the patched font to a valid X font path. Valid font paths can be 
   listed with ``xset q``::

      mv 'MyFont for Powerline.otf' ~/.fonts/

#. Update font cache for the path you moved the font to (you may need to be 
   root to update the cache for system-wide paths)::

      fc-cache -vf ~/.fonts/

After installing the patched font you need to update Gvim or your terminal 
emulator to use the patched font. The correct font usually ends with *for 
Powerline*.

If you can't see the custom symbols, please close all instances of your 
terminal emulator. You may need to restart X for the changes to take
effect.

If you *still* can't see the custom symbols, double-check that you have 
installed the font to a valid X font path.

Installation on OS X
--------------------

Install your patched font by double-clicking the font file in Finder, then 
clicking :guilabel:`Install this font` in the preview window.

After installing the patched font you need to update MacVim or your terminal 
emulator to use the patched font. The correct font usually ends with *for 
Powerline*.

Special cases
=============

rxvt-unicode
------------

.. note:: Symbol font support generally doesn't work well in
   rxvt-unicode. It's recommended that you either disable the symbols or 
   switch to a better terminal emulator if you want to use Powerline.

rxvt-unicode allows using a `Patched font`_ only if it's compiled with the 
``--enable-unicode3`` flag.

For unsupported fonts (e.g. bitmap fonts like Terminus), you can't use 
``PowerlineSymbols.otf`` as a fallback since rxvt-unicode has trouble 
determining the font's metrics. A solution to this issue is to get 
a `Patched font`_ and add this as a fallback font to your 
``.Xresources``/``.Xdefaults``::

    URxvt*font: xft:Terminus:pixelsize=12,xft:Inconsolata\ for\ Powerline:pixelsize=12
