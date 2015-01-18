*********************
Installation on Linux
*********************

The following distribution-specific packages are officially supported, and they 
provide an easy way of installing and upgrading Powerline. The packages will 
automatically do most of the configuration.

* `Arch Linux (AUR), Python 2 version <https://aur.archlinux.org/packages/python2-powerline-git/>`_
* `Arch Linux (AUR), Python 3 version <https://aur.archlinux.org/packages/python-powerline-git/>`_
* Gentoo Live ebuild in `raiagent <https://github.com/leycec/raiagent>`_ overlay
* Powerline package is available for Debian starting from Wheezy (via `backports 
  <https://packages.debian.org/wheezy-backports/powerline>`_). Use `search 
  <https://packages.debian.org/search?keywords=powerline&searchon=names&suite=all&section=all>`_ 
  to get more information.

If used distribution does not have an official package installation guide below 
should be followed:

1. Install Python 3.2+, Python 2.6+ or PyPy and ``pip`` with ``setuptools``. 
   This step is distribution-specific, so no commands provided.
2. Install Powerline using one of the following commands:

   .. code-block:: sh

      pip install --user powerline-status

   will get the latest release version and

   .. code-block:: sh

      pip install --user git+git://github.com/powerline/powerline

   will get the latest development version.

   .. note:: Due to the naming conflict with an unrelated project powerline is
      named ``powerline-status`` in PyPI.

   .. note::
      Powerline developers should be aware that``pip install --editable`` does 
      not currently fully work. Installation performed this way are missing 
      ``powerline`` executable that needs to be symlinked. It will be located in 
      ``scripts/powerline``.

Fonts installation
==================

Fontconfig
----------

This method only works on Linux. It’s the second recommended method if terminal 
emulator supports it as patching fonts is not needed, and it generally works 
with any coding font.

#. Download the latest version of the symbol font and fontconfig file::

      wget https://github.com/powerline/powerline/raw/develop/font/PowerlineSymbols.otf
      wget https://github.com/powerline/powerline/raw/develop/font/10-powerline-symbols.conf

#. Move the symbol font to a valid X font path. Valid font paths can be 
   listed with ``xset q``::

      mv PowerlineSymbols.otf ~/.fonts/

#. Update font cache for the path the font was moved to (root priveleges may be 
   needed to update cache for the system-wide paths)::

      fc-cache -vf ~/.fonts/

#. Install the fontconfig file. For newer versions of fontconfig the config 
   path is ``~/.config/fontconfig/conf.d/``, for older versions it’s  
   ``~/.fonts.conf.d/``::

      mv 10-powerline-symbols.conf ~/.config/fontconfig/conf.d/

If custom symbols still cannot be seen then try closing all instances of the 
terminal emulator. Restarting X may be needed for the changes to take effect.

If custom symbols *still* can’t be seen, double-check that the font have been 
installed to a valid X font path, and that the fontconfig file was installed to 
a valid fontconfig path. Alternatively try to install a :ref:`patched font 
<installation-patched-fonts>`.

Patched font installation
-------------------------

This is the preferred method, but it is not always available because not all 
fonts were patched and not all fonts *can* be patched due to licensing issues.

After downloading font the following should be done:

#. Move the patched font to a valid X font path. Valid font paths can be 
   listed with ``xset q``::

      mv 'SomeFont for Powerline.otf' ~/.fonts/

#. Update font cache for the path the font was moved to (root priveleges may be 
   needed for updating font cache for some paths)::

      fc-cache -vf ~/.fonts/

After installing patched font terminal emulator, GVim or whatever application 
powerline should work with must be configured to use the patched font. The 
correct font usually ends with *for Powerline*.

If custom symbols cannot be seen then try closing all instances of the terminal 
emulator. X server may need to be restarted for the changes to take effect.

If custom symbols *still* can’t be seen then double-check that the font have 
been installed to a valid X font path.
