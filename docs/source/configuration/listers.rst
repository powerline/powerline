.. _config-listers:

****************
Lister reference
****************

Listers are special segment collections which allow to show some list of 
segments for each entity in the list of entities (multiply their segments list 
by a list of entities). E.g. ``powerline.listers.vim.tablister`` presented with 
``powerline.segments.vim.tabnr`` and ``….file_name`` as segments will emit 
segments with buffer names and tabpage numbers for each tabpage shown by vim.

Listers appear in configuration as irregular segments having ``segment_list`` as 
their type and ``segments`` key with a list of segments (a bit more details in 
:ref:`Themes section of configuration reference <config-themes-segments>`).

More information in :ref:`Writing listers <dev-listers>` section.

Vim listers
-----------

.. automodule:: powerline.listers.vim
   :members:

Pdb listers
-----------

.. automodule:: powerline.listers.pdb
   :members:

i3wm listers
------------

.. automodule:: powerline.listers.i3wm
   :members:
