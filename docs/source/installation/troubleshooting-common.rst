I'm using tmux and Powerline looks like crap, what's wrong?
-----------------------------------------------------------

* You need to tell tmux that it has 256-color capabilities. Add this to your 
  :file:`.tmux.conf` to solve this issue::

    set -g default-terminal "screen-256color"

* If you're using iTerm2, make sure that you have enabled the setting 
  :guilabel:`Set locale variables automatically` in :menuselection:`Profiles 
  --> Terminal --> Environment`.

I’m using tmux/screen and Powerline is colorless
------------------------------------------------

* If the above advices do not help, then you need to disable 
  :ref:`term_truecolor <config-common-term_truecolor>`.
* Alternative: set :ref:`additional_escapes <config-common-additional_escapes>` 
  to ``"tmux"`` or ``"screen"``. Note that it is known to work perfectly in 
  screen, but in tmux it may produce ugly spaces.

After an update something stopped working
-----------------------------------------

Assuming powerline was working before update and stopped only after there are 
two possible explanations:

* You have more then one powerline installation (e.g. ``pip`` and ``Vundle`` 
  installations) and you have updated only one.
* Update brought some bug to powerline.

In the second case you, of course, should report the bug to `powerline bug 
tracker <https://github.com/Lokaltog/powerline>`_.  In the first you should make 
sure you either have only one powerline installation or you update all of them 
simultaneously (beware that in the second case you are not supported). To 
diagnose this problem you may do the following:

#) If this problem is observed within the shell make sure that

   .. code-block:: shell

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

  .. code-block:: shell

     pip install --user --editable path/to/powerline

My vim statusline has strange characters like ``^B`` in it!
-----------------------------------------------------------

* Please add ``set encoding=utf-8`` to your :file:`vimrc`.

My vim statusline has a lot of ``^`` or underline characters in it!
-------------------------------------------------------------------

* You need to configure the ``fillchars`` setting to disable statusline 
  fillchars (see ``:h fillchars`` for details). Add this to your 
  :file:`vimrc` to solve this issue:

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

When using z powerline shows wrong number of jobs
-------------------------------------------------

This happens because `z <https://github.com/rupa/z>`_ is launching some jobs in 
the background from ``$POWERLINE_COMMAND`` and these jobs fail to finish before 
powerline prompt is run.

Solution to this problem is simple: be sure that :file:`z.sh` is sourced 
strictly after :file:`powerline/bindings/bash/powerline.sh`. This way background 
jobs are spawned by `z <https://github.com/rupa/z>`_ after powerline has done 
its job.
