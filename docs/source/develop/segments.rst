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
    something needs to be logged.

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

.. note::
    For powerline-lint to work properly the following things may be needed:

    #. If segment is a :py:class:`powerline.segments.Segment` instance and used 
       arguments are scattered over multiple methods 
       :py:meth:`powerline.segments.Segment.argspecobjs` should be overridden in 
       subclass to tell powerline-lint which objects should be inspected for 
       arguments.
    #. If segment takes some arguments that are never listed, but accessed via 
       ``kwargs.get()`` or previous function cannot be used for whatever reason 
       :py:meth:`powerline.segments.Segment.additional_args` should be 
       overridden in subclass.
    #. If user is expected to use one :ref:`name <config-themes-seg-name>` for 
       multiple segments which cannot be linked to the segment function 
       automatically by powerline-lint (e.g. because there are no instances of 
       the segments in question in the default configuration) 
       :py:func:`powerline.lint.checks.register_common_name` function should be 
       used.

Object representing segment may have the following attributes used by 
powerline:

``powerline_requires_segment_info``
    This attribute controls whether segment will receive ``segment_info`` 
    argument: if it is present argument will be received.

``powerline_requires_filesystem_watcher``
    This attribute controls whether segment will receive ``create_watcher`` 
    argument: if it is present argument will be received.

``powerline_segment_datas``
    This attribute must be a dictionary containing ``top_theme: segment_data`` 
    mapping where ``top_theme`` is any theme name (it is expected that all of
    the names from :ref:`top-level themes list <config-top_themes-list>` are 
    present) and ``segment_data`` is a dictionary like the one that is contained 
    inside :ref:`segment_data dictionary in configuration 
    <config-themes-segment_data>`. This attribute should be used to specify 
    default theme-specific values for *third-party* segments: powerline 
    theme-specific values go directly to :ref:`top-level themes 
    <config-themes>`.

.. _dev-segments-startup:

``startup``
    This attribute must be a callable which accepts the following keyword 
    arguments:

    * ``pl``: :py:class:`powerline.PowerlineLogger` instance which is to be used 
      for logging.
    * ``shutdown_event``: :py:class:`Event` object which will be set when 
      powerline will be shut down.
    * Any arguments found in user configuration for the given segment (i.e. 
      :ref:`args key <config-themes-seg-args>`).

    This function is called at powerline startup when using long-running 
    processes (e.g. powerline in vim, in zsh with libzpython, in ipython or in 
    powerline daemon) and not called when ``powerline-render`` executable is 
    used (more specific: when :py:class:`powerline.Powerline` constructor 
    received true ``run_once`` argument).

.. _dev-segments-shutdown:

``shutdown``
    This attribute must be a callable that accepts no arguments and shuts down 
    threads and frees any other resources allocated in ``startup`` method of the 
    segment in question.

    This function is not called when ``startup`` method is not called.

.. _dev-segments-expand:

``expand``
    This attribute must be a callable that accepts the following keyword 
    arguments:

    * ``pl``: :py:class:`powerline.PowerlineLogger` instance which is to be used 
      for logging.
    * ``amount``: integer number representing amount of display cells result 
      must occupy.

      .. warning::
         “Amount of display cells” is *not* number of Unicode codepoints, string 
         length, or byte count. It is suggested that this function should look 
         something like ``return (' ' * amount) + segment['contents']`` where 
         ``' '`` may be replaced with anything that is known to occupy exactly 
         one display cell.
    * ``segment``: :ref:`segment dictionary <dev-segments-segment>`.
    * Any arguments found in user configuration for the given segment (i.e. 
      :ref:`args key <config-themes-seg-args>`).

    It must return new value of :ref:`contents <dev-segments-seg-contents>` key.

.. _dev-segments-truncate:

``truncate``
    Like :ref:`expand function <dev-segments-expand>`, but for truncating 
    segments. Here ``amount`` means the number of display cells which must be 
    freed.

    This function is called for all segments before powerline starts purging 
    them to free space.

This callable object should may return either a string (``unicode`` in Python2 
or ``str`` in Python3, *not* ``str`` in Python2 or ``bytes`` in Python3) object 
or a list of dictionaries. String object is a short form of the following return 
value:

.. code-block:: python

    [{
        'contents': original_return,
        'highlight_groups': [segment_name],
    }]

.. _dev-segments-return:

Returned list is a list of segments treated independently, except for 
:ref:`draw_inner_divider key <dev-segments-draw_inner_divider>`.

All keys in segments returned by the function override those obtained from 
:ref:`configuration <config-themes-segments>` and have the same meaning.

Detailed description of used dictionary keys:

``contents``
    Text displayed by segment. Should be a ``unicode`` (Python2) or ``str`` 
    (Python3) instance.

.. _dev-segments-draw_inner_divider:

``draw_hard_divider``, ``draw_soft_divider``, ``draw_inner_divider``
    Determines whether given divider should be drawn. All have the same meaning 
    as :ref:`the similar keys in configuration <config-themes-seg-draw_divider>` 
    (:ref:`draw_inner_divider <config-themes-seg-draw_inner_divider>`).

.. _dev-segments-highlight_groups:

``highlight_groups``
    Determines segment highlighting. Refer to :ref:`themes documentation 
    <config-themes-seg-highlight_groups>` for more details.

    Defaults to the name of the segment.

    .. note::
       If target is inclusion of the segment in powerline upstream all used 
       highlighting groups must be specified in the segment documentation in the 
       form::

           Highlight groups used: ``g1``[ or ``g2``]*[, ``g3`` (gradient)[ or ``g4``]*]*.

       I.e. use::

           Highlight groups used: ``foo_gradient`` (gradient) or ``foo``, ``bar``.

       to specify that the segment uses *either* ``foo_gradient`` group or 
       ``foo`` group *and* ``bar`` group meaning that ``powerline-lint`` will 
       check that at least one of the first two groups is defined (and if 
       ``foo_gradient`` is defined it must use at least one gradient color) and 
       third group is defined as well.

       All groups must be specified on one line.

``divider_highlight_group``
    Determines segment divider highlight group. Only applicable for soft 
    dividers: colors for hard dividers are determined by colors of adjacent 
    segments.

    .. note::
       If target is inclusion of the segment in powerline upstream used divider 
       highlight group must be specified in the segment documentation in the 
       form::

            Divider highlight group used: ``group``.

        This text must not wrap and all divider highlight group names are 
        supposed to end with ``:divider``: e.g. ``cwd:divider``.

``gradient_level``
    First and the only key that may not be specified in user configuration. It 
    determines which color should be used for this segment when one of the 
    highlighting groups specified by :ref:`highlight_groups 
    <dev-segments-highlight_groups>` was defined to use the color gradient.

    This key may have any value from 0 to 100 inclusive, value is supposed to be 
    an ``int`` or ``float`` instance.

    No error occurs if segment has this key, but no used highlight groups use 
    gradient color.

``_*``
    Keys starting with underscore are reserved for powerline and must not be 
    returned.

``__*``
    Keys starting with two underscores are reserved for the segment functions, 
    specifically for :ref:`expand function <dev-segments-expand>`.

.. _dev-segments-segment:

Segment dictionary
==================

Segment dictionary contains the following keys:

* All keys returned by segment function (if it was used).

* All of the following keys:

  ``name``
    Segment name: value of the :ref:`name key <config-themes-seg-name>` or 
    function name (last component of the :ref:`function key 
    <config-themes-seg-function>`). May be ``None``.

  ``type``
    :ref:`Segment type <config-themes-seg-type>`. Always represents actual type 
    and is never ``None``.

  ``highlight_groups``, ``divider_highlight_group``
    Used highlight groups. May be ``None``.

  ``highlight_group_prefix``
    If this key is present then given prefix will be prepended to each highlight 
    group (both regular and divider) used by this segment in a form 
    ``{prefix}:{group}`` (note the colon). This key is mostly useful for 
    :ref:`segment listers <dev-listers>`.

  .. _dev-segments-seg-around:

  ``before``, ``after``
    Value of :ref:`before <config-themes-seg-before>` or :ref:`after 
    <config-themes-seg-after>` configuration options. May be ``None`` as well as 
    an empty string.

  ``contents_func``
    Function used to get segment contents. May be ``None``.

  .. _dev-segments-seg-contents:

  ``contents``
    Actual segment contents, excluding dividers and :ref:`before/after 
    <dev-segments-seg-around>`. May be ``None``.

  ``priority``
    :ref:`Segment priority <config-themes-seg-priority>`. May be ``None`` for no 
    priority (such segments are always shown).

  ``draw_soft_divider``, ``draw_hard_divider``, ``draw_inner_divider``
    :ref:`Divider control flags <dev-segments-draw_inner_divider>`.

  ``side``
    Segment side: ``right`` or ``left``.

  ``display_condition```
    Contains function that takes three position parameters: 
    :py:class:`powerline.PowerlineLogger` instance, :ref:`segment_info 
    <dev-segments-info>` dictionary and current mode and returns either ``True`` 
    or ``False`` to indicate whether particular segment should be processed.

    This key is constructed based on :ref:`exclude_/include_modes keys 
    <config-themes-seg-exclude_modes>` and :ref:`exclude_/include_function keys 
    <config-themes-seg-exclude_function>`.

  ``width``, ``align``
    :ref:`Width and align options <config-themes-seg-align>`. May be ``None``.

  ``expand``, ``truncate``
    Partially applied :ref:`expand <dev-segments-expand>` or :ref:`truncate 
    <dev-segments-truncate>` function. Accepts ``pl``, ``amount`` and 
    ``segment`` positional parameters, keyword parameters from :ref:`args 
    <config-themes-seg-args>` key were applied.

  ``startup``
    Partially applied :ref:`startup function <dev-segments-startup>`. Accepts 
    ``pl`` and ``shutdown_event`` positional parameters, keyword parameters from 
    :ref:`args <config-themes-seg-args>` key were applied.

  ``shutdown``
    :ref:`Shutdown function <dev-segments-shutdown>`. Accepts no argument.

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
       ``os.environ`` must not ever be used:

       * If segment is run in the daemon this way it will get daemon’s 
         environment which is not correct.
       * If segment is run in Vim or in zsh with libzpython ``os.environ`` will 
         contain Vim or zsh environ *at the moment Python interpreter was 
         loaded*.

``getcwd``
    Function that returns current working directory being called with no 
    arguments. ``os.getcwd`` must not be used for the same reasons the use of 
    ``os.environ`` is forbidden, except that current working directory is valid 
    in Vim and zsh (but not in daemon).

``home``
    Current home directory. May be false.

.. _dev-segment_info-vim:

Vim
---

Vim ``segment_info`` argument is a dictionary with the following keys:

``window``
    ``vim.Window`` object. ``vim.current.window`` or ``vim.windows[number - 1]`` 
    may be used to obtain such object. May be a false object, in which case any 
    of this object’s properties must not be used.

``winnr``
    Window number. Same as ``segment_info['window'].number`` *assuming* Vim is 
    new enough for ``vim.Window`` object to have ``number`` attribute.

``window_id``
    Internal powerline window id, unique for each newly created window. It is 
    safe to assume that this ID is hashable and supports equality comparison, 
    but no other assumptions about it should be used. Currently uses integer 
    numbers incremented each time window is created.

``buffer``
    ``vim.Buffer`` object. One may be obtained using ``vim.current.buffer``, 
    ``segment_info['window'].buffer`` or ``vim.buffers[some_number]``. Note that 
    in the latter case depending on vim version ``some_number`` may be ``bufnr`` 
    or the internal Vim buffer index which is *not* buffer number. For this 
    reason to get ``vim.Buffer`` object other then stored in ``segment_info`` 
    dictionary iteration over ``vim.buffers`` and checking their ``number`` 
    attributes should be performed.

``bufnr``
    Buffer number.

``tabpage``
    ``vim.Tabpage`` object. One may be obtained using ``vim.current.tabpage`` or 
    ``vim.tabpages[number - 1]``. May be a false object, in which case no 
    object’s properties can be used.

``tabnr``
    Tabpage number.

``mode``
    Current mode.

``encoding``
    Value of ``&encoding`` from the time when powerline was initialized. It 
    should be used to convert return values.

.. note::
   Segment generally should not assume that it is run for the current window, 
   current buffer or current tabpage. “Current window” and “current buffer” 
   restrictions may be ignored if ``window_cached`` decorator is used, “current 
   tabpage” restriction may be safely ignored if segment is not supposed to be 
   used in tabline.

.. warning::
   Powerline is being tested with vim-7.0.112 (some minor sanity check) and 
   latest Vim. This means that most of the functionality like 
   ``vim.Window.number``, ``vim.*.vars``, ``vim.*.options`` or even ``dir(vim 
   object)`` should be avoided in segments that want to be included in the 
   upstream.

Shell
-----

``args``
    Parsed shell arguments: a ``argparse.Namespace`` object. Check out 
    ``powerline-render --help`` for the list of all available arguments. 
    Currently it is expected to contain at least the following attributes:

    ``last_exit_code``
        Exit code returned by last shell command. Is either one integer, 
        ``sig{name}`` or ``sig{name}+core`` (latter two are only seen in ``rc`` 
        shell).

    ``last_pipe_status``
        List of exit codes returned by last programs in the pipe or some false 
        object. Only available in ``zsh`` and ``rc``. Is a list of either 
        integers, ``sig{name}`` or ``sig{name}+core`` (latter two are only seen 
        in ``rc`` shell).

    ``jobnum``
        Number of background jobs.

    ``renderer_arg``
        Dictionary containing some keys that are additional arguments used by 
        shell bindings. *This attribute must not be used directly*: all 
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

Pdb
---

``pdb``
    Currently active :py:class:`pdb.Pdb` instance.

``curframe``
    Frame which will be run next. Note: due to the existence of 
    :py:func:`powerline.listers.pdb.frame_lister` one must not use 
    ``segment_info['pdb'].curframe``.

``initial_stack_length``
    Equal to the length of :py:attr:`pdb.Pdb.stack` at the first invocation of 
    the prompt decremented by one.

Segment class
=============

.. autoclass:: powerline.segments.Segment
   :members:

PowerlineLogger class
=====================

.. autoclass:: powerline.PowerlineLogger
   :members:
   :undoc-members:
