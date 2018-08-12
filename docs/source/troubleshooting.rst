***************
Troubleshooting
***************

System-specific issues
======================

.. toctree::

   Linux <troubleshooting/linux>
   OS X <troubleshooting/osx>

Common issues
=============

After an update something stopped working
-----------------------------------------

Assuming powerline was working before update and stopped only after there are 
two possible explanations:

* You have more then one powerline installation (e.g. ``pip`` and ``Vundle`` 
  installations) and you have updated only one.
* Update brought some bug to powerline.

In the second case you, of course, should report the bug to `powerline bug 
tracker <https://github.com/powerline/powerline>`_.  In the first you should 
make sure you either have only one powerline installation or you update all of 
them simultaneously (beware that in the second case you are not supported). To 
diagnose this problem you may do the following:

#) If this problem is observed within the shell make sure that

   .. code-block:: sh

      python -c 'import powerline; print (powerline.__file__)'

   which should report something like 
   :file:`/usr/lib64/python2.7/site-packages/powerline/__init__.pyc` (if 
   powerline is installed system-wide) or 
   :file:`/home/USER/.../powerline/__init__.pyc` (if powerline was cloned 
   somewhere, e.g. in :file:`/home/USER/.vim/bundle/powerline`) reports the same 
   location you use to source in your shell configuration: in first case it 
   should be some location in :file:`/usr` (e.g. 
   :file:`/usr/share/zsh/site-contrib/powerline.zsh`), in the second it should 
   be something like 
   :file:`/home/USER/.../powerline/bindings/zsh/powerline.zsh`. If this is true 
   it may be a powerline bug, but if locations do not match you should not 
   report the bug until you observe it on configuration where locations do 
   match.
#) If this problem is observed specifically within bash make sure that you clean 
   ``$POWERLINE_COMMAND`` and ``$PROMPT_COMMAND`` environment variables on 
   startup or, at least, that it was cleaned after update. While different 
   ``$POWERLINE_COMMAND`` variable should not cause any troubles most of time 
   (and when it will cause troubles are rather trivial) spoiled 
   ``$PROMPT_COMMAND`` may lead to strange error messages or absense of exit 
   code reporting.

   These are the sources which may keep outdated environment variables:

   * Any command launched from any application inherits its environment unless 
     callee explicitly requests to use specific environment. So if you did 
     ``exec bash`` after update it is rather unlikely to fix the problem.
   * More interesting: `tmux` is a client-server application, it keeps one 
     server instance per one user. You probably already knew that, but there is 
     an interesting consequence: once `tmux` server was started it inherits its 
     environment from the callee and keeps it *forever* (i.e. until server is 
     killed). This environment is then inherited by applications you start with 
     ``tmux new-session``. Easiest solution is to kill tmux with ``tmux 
     kill-server``, but you may also use ``tmux set-environment -u`` to unset 
     offending variables.
   * Also check `When using z powerline shows wrong number of jobs`_: though 
     this problem should not be seen after update only, it contains another 
     example of ``$PROMPT_COMMAND`` spoiling results.

#) If this problem is observed within the vim instance you should check out the 
   output of the following Ex mode commands

   .. code-block:: vim

      python import powerline as pl ; print (pl.__file__)
      python3 import powerline as pl ; print (pl.__file__)

   One (but not both) of them will most likely error out, this is OK. The same 
   rules apply as in the 1), but in place of sourcing you should seek for the 
   place where you modify `runtimepath` vim option. If you install powerline 
   using `VAM <https://github.com/MarcWeber/vim-addon-manager>`_ then no 
   explicit modifications of runtimpath were performed in your vimrc 
   (runtimepath is modified by VAM in this case), but powerline will be placed 
   in :file:`{plugin_root_dir}/powerline` where `{plugin_root_dir}` is stored in 
   VAM settings dictionary: do `echo g:vim_addon_manager.plugin_root_dir`.

There is a hint if you want to place powerline repository somewhere, but still 
make powerline package importable anywhere: use

  .. code-block:: sh

     pip install --user --editable path/to/powerline

Tmux/screen-related issues
==========================

I’m using tmux and Powerline looks like crap, what’s wrong?
-----------------------------------------------------------

* You need to tell tmux that it has 256-color capabilities. Add this to your 
  :file:`.tmux.conf` to solve this issue::

    set -g default-terminal "screen-256color"
* If you’re using iTerm2, make sure that you have enabled the setting 
  :guilabel:`Set locale variables automatically` in :menuselection:`Profiles --> 
  Terminal --> Environment`.
* Make sure tmux knows that terminal it is running in support 256 colors. You 
  may tell it tmux by using ``-2`` option when launching it.

I’m using tmux/screen and Powerline is colorless
------------------------------------------------

* If the above advices do not help, then you need to disable 
  :ref:`term_truecolor <config-common-term_truecolor>`.
* Alternative: set :ref:`additional_escapes <config-common-additional_escapes>` 
  to ``"tmux"`` or ``"screen"``. Note that it is known to work perfectly in 
  screen, but in tmux it may produce ugly spaces.

  .. warning::
    Both tmux and screen are not resending sequences escaped in such a way. Thus 
    even though additional escaping will work for the last shown prompt, 
    highlighting will eventually go away when tmux or screen will redraw screen 
    for some reason.

    E.g. in screen it will go away when you used copy mode and prompt got out of 
    screen and in tmux it will go away immediately after you press ``<Enter>``.

In tmux there is a green bar in place of powerline
--------------------------------------------------

In order for tmux bindings to work ``powerline-config`` script is required to be 
present in ``$PATH``. Alternatively one may define ``$POWERLINE_CONFIG_COMMAND`` 
environment variable pointing to the location of the script. *This variable must 
be defined prior to launching tmux server and in the environment where server is 
started from.*

Shell issues
============

Pipe status segment displays only last value in bash
----------------------------------------------------

Make sure that powerline command that sets prompt appears the very first in 
``$PROMPT_COMMAND``. To do this ``powerline.sh`` needs to be sourced the very 
last, after all other users of ``$PROMPT_COMMAND``.

Bash prompt stopped updating
----------------------------

Make sure that powerline commands appear in ``$PROMPT_COMMAND``: some users of 
``$PROMPT_COMMAND`` have a habit of overwriting the value instead of 
prepending/appending to it. All powerline commands start with ``_powerline`` or 
``powerline``, e.g. ``_powerline_set_prompt``.

Bash prompt does not show last exit code
----------------------------------------

There are two possibilities here:

* You are using ``default`` theme in place of ``default_leftonly``. Unlike 
  ``default_leftonly`` ``default`` theme was designed for shells with right 
  prompt support (e.g. zsh, tcsh, fish) and status in question is supposed to be 
  shown on the right side which bash cannot display.

* There is some other user of ``$PROMPT_COMMAND`` which prepended to this 
  variable, but did not bother keeping the exit code. For the best experience 
  powerline must appear first in ``$PROMPT_COMMAND`` which may be achieved by 
  sourcing powerline bindings the last.

  .. note::
     Resourcing bash bindings will not resolve the problem unless you clear 
     powerline commands from ``$PROMPT_COMMAND`` first.

When sourcing shell bindings it complains about missing command or file
-----------------------------------------------------------------------

If you are using ``pip`` based installation do not forget to add pip-specific 
executable path to ``$PATH`` environment variable. This path usually looks 
something like ``$HOME/.local/bin`` (linux) or 
``$HOME/Library/Python/{python_version}/bin`` (OS X). One may check out where 
``powerline-config`` script was installed by using ``pip show -f 
powerline-status | grep powerline-config`` (does not always work).

I am suffering bad lags before displaying shell prompt
------------------------------------------------------

To get rid of these lags there currently are two options:

* Run ``powerline-daemon``. Powerline does not automatically start it for you.
* Compile and install ``libzpython`` module that lives in 
  https://bitbucket.org/ZyX_I/zpython. This variant is zsh-specific.

Prompt is spoiled after completing files in ksh
-----------------------------------------------

This is exactly why powerline has official mksh support, but not official ksh 
support. If you know the solution feel free to share it in `powerline bug 
tracker`_.

When using z powerline shows wrong number of jobs
-------------------------------------------------

This happens because `z <https://github.com/rupa/z>`_ is launching some jobs in 
the background from ``$POWERLINE_COMMAND`` and these jobs fail to finish before 
powerline prompt is run.

Solution to this problem is simple: be sure that :file:`z.sh` is sourced 
strictly after :file:`powerline/bindings/bash/powerline.sh`. This way background 
jobs are spawned by `z <https://github.com/rupa/z>`_ after powerline has done 
its job.

When using shell I do not see powerline fancy characters
--------------------------------------------------------

If your locale encoding is not unicode (any encoding that starts with “utf” or 
“ucs” will work, case is ignored) powerline falls back to ascii-only theme. You 
should set up your system to use unicode locale or forget about powerline fancy 
characters.

Urxvt unicode3 and frills
-------------------------

Make sure that, whatever urxvt package you're installing, both the `unicode3`
and `frills` features are enabled at compile time. Run
``urxvt --help 2>&1 | grep options:`` to get a list of enabled options.
This should contain at least `frills`, `unicode3` and optionally `iso14755`
if you want to input Unicode characters as well.

Compiler flags example:

    --enable-frills \
    --enable-unicode3

As long as your terminal emulator is compiled without unicode rendering,
no amount of configuration will make it display unicode characters.
They're being considered 'unnecessary features', but they add negligible
overhead to the size of the installed package (~100KB).

Vim issues
==========

My vim statusline has strange characters like ``^B`` in it!
-----------------------------------------------------------

* Please add ``set encoding=utf-8`` to your :file:`vimrc`.

My vim statusline has a lot of ``^`` or underline characters in it!
-------------------------------------------------------------------

* You need to configure the ``fillchars`` setting to disable statusline 
  fillchars (see ``:h 'fillchars'`` for details). Add this to your :file:`vimrc` 
  to solve this issue:

   .. code-block:: vim

      set fillchars+=stl:\ ,stlnc:\ 

My vim statusline is hidden/only appears in split windows!
----------------------------------------------------------

* Make sure that you have ``set laststatus=2`` in your :file:`vimrc`.

My vim statusline is not displayed completely and has too much spaces
---------------------------------------------------------------------

* Be sure you have ``ambiwidth`` option set to ``single``.
* Alternative: set :ref:`ambiwidth <config-common-ambiwidth>` to 2, remove fancy 
  dividers (they suck when ``ambiwidth`` is set to double).

Powerline loses color after editing vimrc
-----------------------------------------

If your vimrc has something like

.. code-block:: vim

    autocmd! BufWritePost ~/.vimrc :source ~/.vimrc

used to automatically source vimrc after saving it then you must add ``nested`` 
after pattern (``vimrc`` in this case):

.. code-block:: vim

    autocmd! BufWritePost ~/.vimrc nested :source ~/.vimrc

. Alternatively move ``:colorscheme`` command out of the vimrc to the file which 
will not be automatically resourced.

Observed problem is that when you use ``:colorscheme`` command existing 
highlighting groups are usually cleared, including those defined by powerline. 
To workaround this issue powerline hooks ``Colorscheme`` event, but when you 
source vimrc with ``BufWritePost`` (or any other) event, but without ``nested`` 
this event is not launched. See also `autocmd-nested 
<http://vimcommunity.bitbucket.org/doc/autocmd.txt.html#autocmd-nested>`_ Vim 
documentation.

Powerline loses color after saving any file
-------------------------------------------

It may be one of the incarnations of the above issue: specifically minibufexpl 
is known to trigger it. If you are using minibufexplorer you should set

.. code-block:: vim

    let g:miniBufExplForceSyntaxEnable = 1

variable so that this issue is not triggered. Complete explanation:

#. When MBE autocommand is executed it launches ``:syntax enable`` Vim command…
#. … which makes Vim source :file:`syntax/syntax.vim` file …
#. … which in turn sources :file:`syntax/synload.vim` …
#. … which executes ``:colorscheme`` command. Normally this command triggers 
   ``Colorscheme`` event, but in the first point minibufexplorer did set up 
   autocommands that miss ``nested`` attribute meaning that no events will be 
   triggered when processing MBE events.

.. note::
    This setting was introduced in version 6.3.1 of `minibufexpl 
    <http://www.vim.org/scripts/script.php?script_id=159>`_ and removed in 
    version 6.5.0 of its successor `minibufexplorer 
    <http://www.vim.org/scripts/script.php?script_id=3239>`_. It is highly 
    advised to use the latter because `minibufexpl`_ was last updated late in 
    2004.
