.. _dev-segments:

****************
Writing segments
****************

Each powerline segment is a callable object. It is supposed to be either 
a Python function or :py:class:`powerline.segments.Segment` class. As a callable 
object it should receive the following arguments:

.. note:: All received arguments are keyword arguments.

``pl``
    A :py:class:`powerline.PowerlineLogger` instance. It must be used every time 
    you need to log something.

``segment_info``
    A dictionary. It is only received if callable has 
    ``powerline_requires_segment_info`` attribute.

    Refer to :ref:`segment_info detailed description <dev-segments-info>` for 
    further details.

``create_watcher``
    Function that will create filesystem watcher once called. Which watcher will 
    be created exactly is controlled by :ref:`watcher configuration option 
    <config-common-watcher>`.

And also any other argument(s) specified by user in :ref:`args key 
<config-themes-seg-args>` (no additional arguments by default).

This callable object should may return either a string (``unicode`` in Python2 
or ``str`` in Python3, *not* ``str`` in Python2 or ``bytes`` in Python3) object 
or a list of dictionaries. String object is a short form of the following return 
value:

.. code-block:: python

    [{
        'contents': original_return,
        'highlight_group': [segment_name],
    }]

Returned list is a list of segments treated independently, except for 
:ref:`draw_inner_divider key <dev-segments-draw_inner_divider>`.

All keys in segments returned by the function override those obtained from 
:ref:`configuration <config-themes-segments>` and have the same meaning.

Detailed description of used dictionary keys:

``contents``
    Text displayed by segment. Should be a ``unicode`` (Python2) or ``str`` 
    (Python3) instance.

``draw_hard_divider``, ``draw_soft_divider``, ``draw_inner_divider``
    Determines whether given divider should be drawn. All have the same meaning 
    as :ref:`the similar keys in configuration <config-themes-seg-draw_divider>` 
    (:ref:`draw_inner_divider <config-themes-seg-draw_inner_divider>`).

.. _dev-segments-highlight_group:

``highlight_group``
    Determines segment highlighting. Refer to :ref:`themes documentation 
    <config-themes-seg-highlight_group>` for more details.

    Defaults to the name of the segment.

    .. note::
        If you want to include your segment in powerline you must specify all 
        highlighting groups used in the segment documentation in the form::

            Highlight groups used: ``g1``[ or ``g2``]*[, ``g3`` (gradient)[ or ``g4``]*]*.

        I.e. use::

            Highlight groups used: ``foo_gradient`` (gradient) or ``foo``, ``bar``.

        to specify that your segment uses *either* ``foo_gradient`` group or 
        ``foo`` group *and* ``bar`` group meaning that ``powerline-lint`` will 
        check that at least one of the first two groups is defined (and if 
        ``foo_gradient`` is defined it must use at least one gradient color) and 
        third group is defined as well.

        You must specify all groups on one line.

``divider_highlight_group``
    Determines segment divider highlight group. Only applicable for soft 
    dividers: colors for hard dividers are determined by colors of adjacent 
    segments.

    .. note::
        If you want to include your segment in powerline you must specify used 
        groups in the segment documentation in the form::

            Divider highlight group used: ``group``.

        This text must not wrap and you are supposed to end all divider 
        highlight group names with ``:divider``: e.g. ``cwd:divider``.

``gradient_level``
    First and the only key that may not be specified in user configuration. It 
    determines which color should be used for this segment when one of the 
    highlighting groups specified by :ref:`highlight_group 
    <dev-segments-highlight_group>` was defined to use the color gradient.

    This key may have any value from 0 to 100 inclusive, value is supposed to be 
    an ``int`` or ``float`` instance.

    No error occurs if segment has this key, but no used highlight groups use 
    gradient color.

Segments layout
===============

Powerline segments are all located in one of the ``powerline.segments`` 
submodules. For extension-specific segments ``powerline.segments.{ext}`` module 
should be used (e.g. ``powerline.segments.shell``), for extension-agnostic there 
is ``powerline.segments.common``.

Plugin-specific segments (currently only those that are specific to vim plugins) 
should live in ``powerline.segments.{ext}.plugin.{plugin_name}``: e.g. 
``powerline.segments.vim.plugin.gundo``.

.. _dev-segments-info:

Segment information used in various extensions
==============================================

Each ``segment_info`` value should be a dictionary with at least the following 
keys:

``environ``
    Current environment, may be an alias to ``os.environ``. Is guaranteed to 
    have ``__getitem__`` and ``get`` methods and nothing more.

    .. warning::
        You must not ever use ``os.environ``. If your segment is run in daemon 
        you will get daemon’s environment which is not correct. If your segment 
        is run in Vim or in zsh with libzpython you will get Vim or zsh 
        environment at python startup.

``getcwd``
    Function that returns current working directory being called with no 
    arguments. You must not use ``os.getcwd`` for the same reasons you must not 
    use ``os.environ``, except that current working directory is valid in Vim 
    and zsh (but not in daemon).

``home``
    Current home directory. May be false.

.. _dev-segment_info-vim:

Vim
---

Vim ``segment_info`` argument is a dictionary with the following keys:

``window``
    ``vim.Window`` object. You may obtain one using ``vim.current.window`` or 
    ``vim.windows[number - 1]``. May be a false object, in which case you should 
    not use any of this objects’ properties.

``winnr``
    Window number. Same as ``segment_info['window'].number`` *assuming* Vim is 
    new enough for ``vim.Window`` object to have ``number`` attribute.

``window_id``
    Internal powerline window id, unique for each newly created window. You 
    should assume that this ID is hashable and supports equality comparison, but 
    you must not use any other assumptions about it. Currently uses integer 
    numbers incremented each time window is created.

``buffer``
    ``vim.Buffer`` object. You may obtain one using ``vim.current.buffer``, 
    ``segment_info['window'].buffer`` or ``vim.buffers[some_number]``. Note that 
    in the latter case depending on vim version ``some_number`` may be ``bufnr`` 
    or the internal Vim buffer index which is *not* buffer number. For this 
    reason to get ``vim.Buffer`` object other then stored in ``segment_info`` 
    dictionary you must iterate over ``vim.buffers`` and check their ``number`` 
    attributes.

``bufnr``
    Buffer number.

``tabpage``
    ``vim.Tabpage`` object. You may obtain one using ``vim.current.tabpage`` or 
    ``vim.tabpages[number - 1]``. May be a false object, in which case you 
    should not use any of this objects’ properties.

``tabnr``
    Tabpage number.

``mode``
    Current mode.

.. note::
    Your segment generally should not assume that it is run for the current 
    window, current buffer or current tabpage. “Current window” and “current 
    buffer” restrictions may be ignored if you use ``window_cached`` decorator, 
    “current tabpage” restriction may be safely ignored if you do not plan to 
    ever see your segment in the tabline.

.. warning::
    Powerline is being tested with vim-7.2 and will be tested with it until 
    travis changes used vim version. This means that you may not use most of the 
    functionality like ``vim.Window.number``, ``vim.*.vars``, ``vim.*.options`` 
    or even ``dir(vim object)`` if you want your segment to be included in 
    powerline.

Shell
-----

``args``
    Parsed shell arguments: a ``argparse.Namespace`` object. Check out 
    ``powerline-render --help`` for the list of all available arguments. 
    Currently it is expected to contain at least the following attributes:

    ``last_exit_code``
        Exit code returned by last shell command.

    ``last_pipe_status``
        List of exit codes returned by last programs in the pipe or some false 
        object. Only available in ``zsh``.

    ``jobnum``
        Number of background jobs.

    ``renderer_arg``
        Dictionary containing some keys that are additional arguments used by 
        shell bindings. *You must not use this attribute directly*: all 
        arguments from this dictionary are merged with ``segment_info`` 
        dictionary. Known to have at least the following keys:

        ``client_id``
            Identifier unique to one shell instance. Is used to record instance 
            state by powerline daemon.

            It is not guaranteed that existing client ID will not be retaken 
            when old shell with this ID quit: usually process PID is used as 
            a client ID.

            It is also not guaranteed that client ID will be process PID, number 
            or something else at all. It is guaranteed though that client ID 
            will be some hashable object which supports equality comparison.

        ``local_theme``
            Local theme that will be used by shell. One should not rely on the 
            existence of this key.

        Other keys, if any, are specific to segments.

Ipython
-------

``ipython``
    Some object which has ``prompt_count`` attribute. Currently it is guaranteed 
    to have only this attribute.

    Attribute ``prompt_count`` contains the so-called “history count” 
    (equivalent to ``\N`` in ``in_template``).

Segment class
=============

.. autoclass:: powerline.segments.Segment
   :members:

PowerlineLogger class
=====================

.. autoclass:: powerline.PowerlineLogger
   :members:
   :undoc-members:
