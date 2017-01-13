********************
Installation on Windows
********************

Python package
==============

1. `Install Python <https://www.python.org/downloads>`_ version 2.7.12, 2.8 or 3.4 upwards - Python 2.7.12 onwards, contains pip in the installation package.

2. Install Powerline using one of the following commands:

   .. code-block:: ps1

       pip install --user powerline-status

   will get current release version.

   .. note::
      Powerline developers should be aware that ``pip install --editable`` does 
      not currently fully work. Installation performed this way are missing 
      ``powerline`` executable that needs to be symlinked. It will be located in 
      ``scripts/powerline``.

Vim installation
================

Before you begin the installation, ensure that your Vim and Python supported CPU architecture are either both 32bit or both 64bit. Python support in Vim will not work if they are different.

You'll also need to ensure you have python27.dll in either your vim74 or vim80 installation directory (that is if you plan on using Python 2.7)

Clone the powerline git repository. The only file you'll need from this repository is

   .. code-block:: sh

       bindings\vim\plugin\powerline.vim

Depending on your version of Vim, copy that file to either vim74\plugin\powerline.vim or vim80\plugin\powerline.vim


Fonts installation
==================

To install the font, copy the font PowerlineSymbols.otf from the powerline git repository to vimfiles\fonts, which can be found in your vim installation directory.
