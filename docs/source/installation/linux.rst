*********************
Installation on Linux
*********************

The following distribution-specific packages are officially supported, and they 
provide an easy way of installing and upgrading Powerline. The packages will 
automatically do most of the configuration for you.

* `Arch Linux (AUR), Python 2 version <https://aur.archlinux.org/packages/python2-powerline-git/>`_
* `Arch Linux (AUR), Python 3 version <https://aur.archlinux.org/packages/python-powerline-git/>`_
* Gentoo Live ebuild in `raiagent <https://github.com/leycec/raiagent>`_ overlay

If you're running a distribution without an official package you'll have to 
follow the installation guide below:

1. Install Python 3.2+ or Python 2.6+ with ``pip``. This step is 
   distribution-specific, so no commands provided.
2. Install Powerline using the following command::

       pip install --user git+git://github.com/Lokaltog/powerline

.. note:: You need to use the GitHub URI when installing Powerline! This 
   project is currently unavailable on the PyPI due to a naming conflict 
   with an unrelated project.

.. note:: If you are powerline developer you should be aware that ``pip install 
   --editable`` does not currently fully work. If you
   install powerline this way you will be missing ``powerline`` executable and 
   need to symlink it. It will be located in ``scripts/powerline``.

Fonts installation
==================

Fontconfig
----------

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
a :ref:`patched font <installation-patched-fonts>`.

Patched font installation
-------------------------

After downloading font you should do the following:

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
