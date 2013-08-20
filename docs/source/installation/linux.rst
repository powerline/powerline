:tocdepth: 2

.. _installation-linux:

*********************
Installation on Linux
*********************

The following distribution-specific packages are officially supported, and 
they provide an easy way of installing and upgrading Powerline. The packages 
will automatically do most of the configuration for you, but you should 
still skim through this guide so you know how the plugin works.

* `Arch Linux (AUR), Python 2 version <https://aur.archlinux.org/packages/python2-powerline-git/>`_
* `Arch Linux (AUR), Python 3 version <https://aur.archlinux.org/packages/python-powerline-git/>`_
* Gentoo Live ebuild (:file:`packages/gentoo/app-misc/powerline/`)

If you're running a distribution without an official package you'll have to 
follow the installation guide below:

Plugin installation
===================

1. Install Python 3.2+ or Python 2.6+.
2. Install Powerline using the following command::

       pip install --user git+git://github.com/Lokaltog/powerline

.. note:: You need to use the GitHub URI when installing Powerline! This 
   project is currently unavailable on the PyPI due to a naming conflict 
   with an unrelated project.

Font installation
=================

Powerline provides two ways of installing the required fonts on Linux. The 
recommended method is using ``fontconfig`` if your terminal emulator 
supports it. See the :ref:`term-feature-support-matrix` for details about 
what features your terminal emulator supports.

Fontconfig
----------

1. Download the `latest version of PowerlineSymbols 
   <https://github.com/Lokaltog/powerline/raw/develop/font/PowerlineSymbols.otf>`_  
   and the `latest version of the fontconfig file 
   <https://github.com/Lokaltog/powerline/raw/develop/font/10-powerline-symbols.conf>`_.
2. Move :file:`PowerlineSymbols.otf` to :file:`~/.fonts/` (or another X font 
   directory).
3. Run ``fc-cache -vf ~/.fonts`` to update your font cache.
4. Move :file:`10-powerline-symbols.conf` to either :file:`~/.fonts.conf.d/` 
   or :file:`~/.config/fontconfig/conf.d/`, depending on your fontconfig 
   version.
5. If you don't see the arrow symbols, please close all instances of your 
   terminal emulator or gvim. You may also have to restart X for the changes 
   to take effect. If you *still* don't see the arrow symbols, please submit 
   an issue on GitHub.

Patched font
------------

1. Download the font of your choice from `powerline-fonts`_. If you can't 
   find your preferred font in the `powerline-fonts`_ repo, you'll have to 
   patch your own font instead. See :ref:`font-patching` for instructions.
2. Move your patched font to :file:`~/.fonts/` (or another X font 
   directory).
3. Run ``fc-cache -vf ~/.fonts`` to update your font cache.
4. Update Gvim or your terminal emulator to use the patched font. (the 
   correct font usually ends with *for Powerline*).
5. If you don't see the arrow symbols, please close all instances of your 
   terminal emulator or gvim. You may also have to restart X for the changes 
   to take effect. If you *still* don't see the arrow symbols, please submit 
   an issue on GitHub.

.. _powerline-fonts: https://github.com/Lokaltog/powerline-fonts

Troubleshooting
===============

.. contents::
   :local:

I can't see any fancy symbols, what's wrong?
--------------------------------------------

* Make sure that you've configured gvim or your terminal emulator to use 
  a patched font (see :ref:`font-patching`).
* You need to set your ``LANG`` and ``LC_*`` environment variables to 
  a UTF-8 locale (e.g. ``LANG=en_US.utf8``). Consult your Linux distro's 
  documentation for information about setting these variables correctly.
* Make sure that vim is compiled with the ``--with-features=big`` flag.
* If you're using rxvt-unicode, make sure that it's compiled with the 
  ``--enable-unicode3`` flag.

The fancy symbols look a bit blurry or "off"!
---------------------------------------------

* Make sure that you have patched all variants of your font (i.e. both the 
  regular and the bold font files).

.. include:: troubleshooting-common.rst
