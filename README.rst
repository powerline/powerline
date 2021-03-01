Powerline
=========

.. image:: https://api.travis-ci.org/powerline/powerline.svg?branch=develop
   :target: `travis-build-status`_
   :alt: Build status
.. _travis-build-status: https://travis-ci.org/powerline/powerline

**Powerline is a statusline plugin for vim, and provides statuslines and 
prompts for several other applications, including zsh, bash, fish, tmux,
IPython, Awesome, i3 and Qtile.**

+---------+---------------------------------------------------+
| Author  | Kim Silkebækken (kim.silkebaekken+vim@gmail.com)  |
+---------+---------------------------------------------------+
| Source  | https://github.com/powerline/powerline            |
+---------+---------------------------------------------------+
| Version | beta                                              |
+---------+---------------------------------------------------+

**Powerline does not support python2 anymore and powerline will stop working with python2 in the near future.**

Features
--------

* **Extensible and feature rich, written in Python.** Powerline was 
  completely rewritten in Python to get rid of as much vimscript as 
  possible. This has allowed much better extensibility, leaner and better 
  config files, and a structured, object-oriented codebase with no mandatory
  third-party dependencies other than a Python interpreter.
* **Stable and testable code base.** Using Python has allowed unit testing 
  of all the project code. The code is tested to work in Python 3.6+.
* **Support for prompts and statuslines in many applications.** Originally 
  created exclusively for vim statuslines, the project has evolved to 
  provide statuslines in tmux and several WMs, and prompts for shells like 
  bash/zsh and other applications. It’s simple to write renderers for any 
  other applications that Powerline doesn’t yet support.
* **Configuration and colorschemes written in JSON.** JSON is 
  a standardized, simple and easy to use file format that allows for easy 
  user configuration across all of Powerline’s supported applications.
* **Fast and lightweight, with daemon support for even better performance.**
  Although the code base spans a couple of thousand lines of code with no 
  goal of “less than X lines of code”, the main focus is on good performance 
  and as little code as possible while still providing a rich set of 
  features. The new daemon also ensures that only one Python instance is 
  launched for prompts and statuslines, which provides excellent 
  performance.

*But I hate Python / I don’t need shell prompts / this is just too much 
hassle for me / what happened to the original vim-powerline project / …*

You should check out some of the Powerline derivatives. The most lightweight
and feature-rich alternative is currently the `vim-airline 
<https://github.com/vim-airline/vim-airline>`_ project.

Configuration
-------------

Basic powerline configuration is done via `JSON` files located at `.config/powerline/`. It is a good idea to start by copying the default configuration located at `powerline_root/powerline/config_files/` to `.config/powerline/`.
If you installed the powerline from the AUR or via pip, `powerline_root` should be `/usr/lib/python3.6/site-packages/` or something similar, depending on your python version.

If you installed powerline via apt-get 'powerline_root' should be '/usr/share/powerline/'.

This should yield you the following directory structure:

    ::

        .config/powerline/
        ├── colorschemes
        │   ├── ...
        │   └── wm
        |       └── default.json  // Your configuration goes here
        ├── colors.json
        ├── config.json
        └── themes
            ├── ...
            └── wm
                └── default.json  // Your configuration goes here



The files in the subdirectories of `themes` are used to specify which segments shall be shown; the files in subdirectories of `colorschemes` are used to specify which colors (as defined in `colors.json`) shall be used to display a segment.

Note that your local configuration only overrides the global configuration, it does not replace it, i.e. if you don't configure something locally, the global default will be used instead.

* Consult the `documentation <https://powerline.readthedocs.org/en/latest/configuration.html#quick-setup-guide>`_ for more details. See also the `segment reference <https://powerline.readthedocs.org/en/latest/configuration/segments.html>`_ for available segments and their configuration.
* Check out `powerline-fonts <https://github.com/powerline/fonts>`_ for 
  pre-patched versions of popular, open source coding fonts.

Screenshots
-----------

Vim statusline
^^^^^^^^^^^^^^

**Mode-dependent highlighting**

* .. image:: https://raw.github.com/powerline/powerline/develop/docs/source/_static/img/pl-mode-normal.png
     :alt: Normal mode
* .. image:: https://raw.github.com/powerline/powerline/develop/docs/source/_static/img/pl-mode-insert.png
     :alt: Insert mode
* .. image:: https://raw.github.com/powerline/powerline/develop/docs/source/_static/img/pl-mode-visual.png
     :alt: Visual mode
* .. image:: https://raw.github.com/powerline/powerline/develop/docs/source/_static/img/pl-mode-replace.png
     :alt: Replace mode

**Automatic truncation of segments in small windows**

* .. image:: https://raw.github.com/powerline/powerline/develop/docs/source/_static/img/pl-truncate1.png
     :alt: Truncation illustration
* .. image:: https://raw.github.com/powerline/powerline/develop/docs/source/_static/img/pl-truncate2.png
     :alt: Truncation illustration
* .. image:: https://raw.github.com/powerline/powerline/develop/docs/source/_static/img/pl-truncate3.png
     :alt: Truncation illustration

----

The font in the screenshots is `Pragmata Pro`_ by Fabrizio Schiavi.

.. _`Pragmata Pro`: http://www.fsd.it/shop/fonts/pragmatapro
