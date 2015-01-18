.. _dev-listers:

***************
Writing listers
***************

Listers provide a way to show some segments multiple times: once per each entity 
(buffer, tabpage, etc) lister knows. They are functions which receive the 
following arguments:

``pl``
    A :py:class:`powerline.PowerlineLogger` class instance. It must be used for 
    logging.

``segment_info``
    Base segment info dictionary. Lister function or class must have 
    ``powerline_requires_segment_info`` to receive this argument.

    .. warning::
        Listers are close to useless if they do not have access to this 
        argument.

    Refer to :ref:`segment_info detailed description <dev-segments-info>` for 
    further details.

``draw_inner_divider``
    If False (default) soft dividers between segments in the listed group will 
    not be drawn regardless of actual segment settings. If True they will be 
    drawn, again regardless of actual segment settings. Set it to ``None`` in 
    order to respect segment settings.

And also any other argument(s) specified by user in :ref:`args key 
<config-themes-seg-args>` (no additional arguments by default).

Listers must return a sequence of pairs. First item in the pair must contain 
a ``segment_info`` dictionary specific to one of the listed entities.

Second item must contain another dictionary: it will be used to modify the 
resulting segment. In addition to :ref:`usual keys that describe segment 
<dev-segments-segment>` the following keys may be present (it is advised that 
*only* the following keys will be used):

``priority_multiplier``
    Value (usually a ``float``) used to multiply segment priority. It is useful 
    for finer-grained controlling which segments disappear first: e.g. when 
    listing tab pages make first disappear directory names of the tabpages which 
    are most far away from current tabpage, then (when all directory names 
    disappeared) buffer names. Check out existing listers implementation in 
    :file:`powerline/listers/vim.py`.
